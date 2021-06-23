import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os, random, copy, time, math
import torch
from torch_geometric.datasets import TUDataset
import torch_geometric.transforms as T
import torch.utils
import torch.utils.data
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.optim.lr_scheduler as lr_scheduler
from torch.nn.parameter import Parameter
from torch.utils.data import DataLoader
import argparse
from os.path import join as pjoin
from torch.utils.tensorboard import SummaryWriter
matplotlib.use('agg')
writer = SummaryWriter(log_dir='run')
print('using torch', torch.__version__)

parser = argparse.ArgumentParser(description='Chebnet')
parser.add_argument('-D', '--dataset', type=str, default='PROTEINS')
parser.add_argument('--lr', type=float, default=0.005, help='learning rate')
parser.add_argument('--lr_decay_steps', type=str, default='25,35', help='learning rate')
parser.add_argument('--wd', type=float, default=1e-4, help='weight decay')
parser.add_argument('-d', '--dropout', type=float, default=0.1, help='dropout rate')
parser.add_argument('-f', '--filters', type=str, default='64,64,64', help='GCN filters')
parser.add_argument('-K', '--chebkvar', type=int, default=1, help='ChebNet K')
parser.add_argument('--n_hidden', type=int, default=0, help='number of hidden layer')
parser.add_argument('--n_hidden_edge', type=int, default=32, help='number of hidden layer edge prediction')
parser.add_argument('--epochs', type=int, default=40, help='number of epochs')
parser.add_argument('-b', '--batch_size', type=int, default=32, help='batch size')
parser.add_argument('--folds', type=int, default=10, help='number of cross-validation folds')
parser.add_argument('--log_interval', type=int, default=10, help='interval log')
parser.add_argument('-s', '--scale_identity', action='store_true', default=False, help='2I')

args = parser.parse_args()

args.filters = list(map(int, args.filters.split(',')))
args.lr_decay_steps = list(map(int, args.lr_decay_steps.split(',')))

loader_thread = 24
torch_seed = random.randint(0, 10000)
for arg in vars(args):
    print(arg, getattr(args, arg))

n_folds = args.folds  
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = True
torch.manual_seed(torch_seed)
torch.cuda.manual_seed(torch_seed)
torch.cuda.manual_seed_all(torch_seed)
rnd_state = np.random.RandomState(torch_seed)

def split_ids(ids, folds=10):
    n = len(ids)
    stride = int(np.ceil(n / float(folds)))
    test_ids = [ids[i: i + stride] for i in range(0, n, stride)]
    assert np.all(
        np.unique(np.concatenate(test_ids)) == sorted(ids)), 'some graphs are missing in the test sets'
    assert len(test_ids) == folds, 'invalid test sets'
    train_ids = []
    for fold in range(folds):
        train_ids.append(np.array([e for e in ids if e not in test_ids[fold]]))
        assert len(train_ids[fold]) + len(test_ids[fold]) == len(
            np.unique(list(train_ids[fold]) + list(test_ids[fold]))) == n, 'invalid splits'

    return train_ids, test_ids

class GraphConv(nn.Module):
    def __init__(self,
            in_features,
            out_features,
            n_relations=1,
            K=1,
            activation=None,
            scale_identity=False):
        super(GraphConv, self).__init__()
        self.fc = nn.Linear(in_features=in_features * K * n_relations, out_features=out_features)
        self.n_relations = n_relations
        assert K > 0, ('filter scale must be greater than 0', K)
        self.K = K
        self.activation = activation
        self.bn = nn.BatchNorm1d(out_features)
        self.scale_identity = scale_identity

    def chebyshev_basis(self, L, X, K):
        if K > 1:
            Xt = [X]
            Xt.append(torch.bmm(L, X)) 
            for k in range(2, K):
                Xt.append(2 * torch.bmm(L, Xt[k - 1]) - Xt[k - 2]) 
            Xt = torch.cat(Xt, dim=2)
            return Xt
        else:
            assert K == 1, K
            return torch.bmm(L, X)

    def laplacian_batch(self, A):
        batch, N = A.shape[:2]
        A_hat = A
        if self.K < 2 or self.scale_identity:
            I = torch.eye(N).unsqueeze(0).to('cpu')
            if self.scale_identity:
                I = 2 * I  
            if self.K < 2:
                A_hat = A + I
        D_hat = (torch.sum(A_hat, 1) + 1e-5) ** (-0.5)
        L = D_hat.view(batch, N, 1) * A_hat * D_hat.view(batch, 1, N)
        return L

    def forward(self, data):
        x, A, mask = data[:3]
        if len(A.shape) == 3:
            A = A.unsqueeze(3)
        x_hat = []
        for rel in range(self.n_relations):
            L = self.laplacian_batch(A[:, :, :, rel])
            x_hat.append(self.chebyshev_basis(L, x, self.K))
        x = self.fc(torch.cat(x_hat, 2))
        if len(mask.shape) == 2:
            mask = mask.unsqueeze(2)
        x = x * mask
        x = self.bn(x.permute(0, 2, 1)).permute(0, 2, 1)

        if self.activation is not None:
            x = self.activation(x)
        return (x, A, mask)

class MultiCheb(nn.Module):
    def __init__(self,
            in_features,
            out_features,
            n_relations,
            filters=[32, 128, 512],
            K=1,
            n_hidden=0,
            n_hidden_edge=32,
            dropout=0.2,
            scale_identity=False):
        super(MultiCheb, self).__init__()

        self.gconv = nn.Sequential(*([GraphConv(in_features=in_features if layer == 0 else filters[layer - 1],
            out_features=f,
            n_relations=n_relations,
            K=K,
            activation=nn.ReLU(inplace=True),
            scale_identity=scale_identity) for layer, f in enumerate(filters)]))
        self.edge_pred = nn.Sequential(nn.Linear(in_features * 2, n_hidden_edge),
            nn.ReLU(inplace=True),
            nn.Linear(n_hidden_edge, 1))
        fc = []
        fc.append(nn.Dropout(p=dropout))
        fc.append(nn.Linear(filters[-1], n_hidden))
        if dropout > 0:
            fc.append(nn.Dropout(p=dropout))
        n_last = n_hidden
        fc.append(nn.Linear(n_last, out_features))
        self.fc = nn.Sequential(*fc)

    def forward(self, data):
        # data: [node_features, A, graph_support, N_nodes, label, batch_cur]
        x = data[0]
        B, N, C = x.shape
        mask = data[2]
        N_nodes = data[3]
        batch_cur = data[5]
        x_cat, idx = [], []
        for b in range(B):
            n = int(mask[b].sum())
            node_i = torch.nonzero(mask[b]).repeat(1, n).view(-1, 1)
            node_j = torch.nonzero(mask[b]).repeat(n, 1).view(-1, 1)
            triu = (node_i < node_j).squeeze()
            x_cat.append(torch.cat((x[b, node_i[triu]], x[b, node_j[triu]]), 2).view(int(torch.sum(triu)), C * 2))
            idx.append((node_i * N + node_j)[triu].squeeze())

        x_cat = torch.cat(x_cat)
        idx_flip = np.concatenate((np.arange(C, 2 * C), np.arange(C)))
        y = torch.exp(0.5 * (self.edge_pred(x_cat) + self.edge_pred(x_cat[:, idx_flip])).squeeze())
        A_pred = torch.zeros(B, N * N, device='cpu')
        c = 0
        for b in range(B):
            A_pred[b, idx[b]] = y[c:c + idx[b].nelement()]
            c += idx[b].nelement()
        A_pred = A_pred.view(B, N, N)
        A_pred_new = torch.zeros(B, N, N, device='cpu')
        for b in range(B):
            A_pred_sum = torch.sum(A_pred[b], 1)
            A_pred_sum[A_pred_sum == 0] = 1
            A_pred_new[b] = torch.div(A_pred[b], A_pred_sum.view(-1, 1))
        A_pred_new = (A_pred_new + A_pred_new.permute(0, 2, 1))
        data = (x, torch.stack((data[1], A_pred_new), 3), mask)
        x = self.gconv(data)[0]
        
        B, N, _ = x.shape
        sample_id_vis, N_nodes_vis = -1, -1
        for b in range(B):
            if (N_nodes[b] < 20 and N_nodes[b] > 10) or sample_id_vis > -1:
                if sample_id_vis > -1 and sample_id_vis != b:
                    continue
                if N_nodes_vis < 0:
                    N_nodes_vis = N_nodes[b]
                plt.figure()
                plt.imshow(A_pred_new[b][:N_nodes_vis, :N_nodes_vis].data.cpu().numpy())
                plt.colorbar()
                plt.title('Predict adjacency matrix')
                plt.savefig('adjs/predict_adjacency_batch%d.png' % batch_cur)
                plt.close()

                plt.figure()
                plt.imshow(data[1][b][:N_nodes_vis, :N_nodes_vis, 0].data.cpu().numpy())
                plt.colorbar()
                plt.title('adjacency matrix')
                plt.savefig('adjs/adjacency_batch%d.png' % batch_cur)
                plt.close()
                sample_id_vis = b
                break

        x = torch.max(x, dim=1)[0].squeeze() 
        x = self.fc(x)
        return x

# ANCHOR MAIN PROC 
def collate_batch(batch):
    '''
    [node_features*batch_size, A*batch_size, label*batch_size]
    [node_features, A, mask, N_nodes, label]
    '''
    B = len(batch)
    N_nodes = [len(batch[b].x) for b in range(B)]
    C = batch[0].x.shape[1]
    N_nodes_max = int(np.max(N_nodes))

    mask = torch.zeros(B, N_nodes_max)
    A = torch.zeros(B, N_nodes_max, N_nodes_max)
    x = torch.zeros(B, N_nodes_max, C)
    for b in range(B):
        x[b, :N_nodes[b]] = batch[b].x
        A[b].index_put_((batch[b].edge_index[0], batch[b].edge_index[1]), torch.Tensor([1]))
        mask[b][:N_nodes[b]] = 1

    N_nodes = torch.from_numpy(np.array(N_nodes)).long()
    labels = torch.from_numpy(np.array([batch[b].y.item() for b in range(B)])).long()
    return [x, A, mask, N_nodes, labels]

transforms = []

print('Loading data')

loss_fn = F.cross_entropy
predict_fn = lambda output: output.max(1, keepdim=True)[1].detach().cpu()

dataset = TUDataset('./data/%s/' % args.dataset, name=args.dataset,
                    use_node_attr=False,
                    transform=T.Compose(transforms))

train_ids, test_ids = split_ids(rnd_state.permutation(len(dataset)), folds=n_folds)

acc_folds = []

for fold_id in range(n_folds):

    loaders = []
    for split in ['train', 'test']:
        gdata = dataset[torch.from_numpy((train_ids if split.find('train') >= 0 else test_ids)[fold_id])]

        loader = DataLoader(gdata,
                            batch_size=args.batch_size,
                            shuffle=split.find('train') >= 0,
                            num_workers=loader_thread,
                            collate_fn=collate_batch)
        loaders.append(loader)

    print('\nFold {}/{}, train {}, test {}'.format(fold_id + 1, n_folds, len(loaders[0].dataset), len(loaders[1].dataset)))

    model = MultiCheb(in_features=loaders[0].dataset.num_features,
                out_features=loaders[0].dataset.num_classes,
                n_relations=2,
                n_hidden=args.n_hidden,
                n_hidden_edge=args.n_hidden_edge,
                filters=args.filters,
                K=args.chebkvar,
                dropout=args.dropout,
                scale_identity=args.scale_identity).to('cpu')

    train_params = list(filter(lambda p: p.requires_grad, model.parameters()))

    optimizer = optim.Adam(train_params, lr=args.lr, weight_decay=args.wd, betas=(0.5, 0.999))
    scheduler = lr_scheduler.MultiStepLR(optimizer, args.lr_decay_steps, gamma=0.1)

    def train(train_loader):
        model.train()
        start = time.time()
        train_loss, n_samples = 0, 0
        for batch_idx, data in enumerate(train_loader):
            data = [data[0], data[1], data[2], data[3], data[4], torch.tensor(batch_idx)]
            for i in range(len(data)):
                data[i] = data[i].to('cpu')
            optimizer.zero_grad()
            output = model(data)
            loss = loss_fn(output, data[4])
            loss.backward()
            optimizer.step()
            time_iter = time.time() - start
            train_loss += loss.item() * len(output)
            n_samples += len(output)
            if batch_idx % args.log_interval == 0 or batch_idx == len(train_loader) - 1:
                print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f} (avg: {:.6f}) \tsec/iter: {:.4f}'.format(
                    epoch + 1, n_samples, len(train_loader.dataset),
                    100. * (batch_idx + 1) / len(train_loader), loss.item(), train_loss / n_samples,
                    time_iter / (batch_idx + 1)))
        return train_loss / n_samples
    def test(test_loader):
        model.eval()
        start = time.time()
        test_loss, correct, n_samples = 0, 0, 0
        for batch_idx, data in enumerate(test_loader):
            data = [data[0], data[1], data[2], data[3], data[4], torch.tensor(batch_idx)]
            for i in range(len(data)):
                data[i] = data[i].to('cpu')
            output = model(data)
            loss = loss_fn(output, data[4], reduction='sum')
            test_loss += loss.item()
            n_samples += len(output)
            pred = predict_fn(output)

            correct += pred.eq(data[4].detach().cpu().view_as(pred)).sum().item()
        acc = 100. * correct / n_samples
        print('Test set (epoch {}): Average loss: {:.4f}, Accuracy: {}/{} ({:.2f}%) \tsec/iter: {:.4f}\n'.format(
            epoch + 1,
            test_loss / n_samples,
            correct,
            n_samples,
            acc, (time.time() - start) / len(test_loader)))
        return acc

    for epoch in range(args.epochs):
        writer.add_scalar('Loss/train', train(loaders[0]), epoch)
        scheduler.step()
    acc = test(loaders[1])
    acc_folds.append(acc)

torch.save(model.state_dict(), './multicheb.pth')
print(acc_folds)
print('{}-fold cross validation avg acc (+- std): {} ({})'.format(n_folds, np.mean(acc_folds), np.std(acc_folds)))
