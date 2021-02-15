import waver.util as util
import os

def create_registerEnroll(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'organizations')): 
        os.mkdir(os.path.join(target_dir, 'organizations'))
    if not os.path.exists(os.path.join(target_dir, 'organizations', 'fabric-ca')):
        os.mkdir(os.path.join(target_dir, 'organizations', 'fabric-ca'))
    util.render_template('organizations/fabric-ca/registerEnroll.sh',
        os.path.join(target_dir, 'organizations', 'fabric-ca', 'registerEnroll.sh'), data)

def create_envVars(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'scripts')): 
        os.mkdir(os.path.join(target_dir, 'scripts'))
    util.render_template('scripts/envVars.sh',
        os.path.join(target_dir, 'scripts', 'envVars.sh'), data)

def create_createChannel(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'scripts')): 
        os.mkdir(os.path.join(target_dir, 'scripts'))
    for channel in data['channels']:
        util.render_template('scripts/createChannel.sh',
            os.path.join(target_dir, 'scripts', 'createChannel' + channel['channel_name'] +'.sh'), 
            {'channel': channel, 'orderer': data['orderer']})

def create_DeployChaincode(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'scripts')): 
        os.mkdir(os.path.join(target_dir, 'scripts'))
    input_data = []
    for chaincode in data['chaincodes']:
        input_data.append({'chaincode': chaincode, 'orderer': data['orderer']})
    for channel in data['channels']:
        for chaincode in input_data:
            if chaincode['chaincode']['channel'] == channel['channel_name']:
                chaincode['channel'] = channel
    for chaincode in input_data:
        util.render_template('scripts/deployChaincode.sh',
            os.path.join(target_dir, 'scripts', 'deployChaincode' + chaincode['chaincode']['cc_name'] +'.sh'), chaincode)

def create_netController(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    util.render_template('netController.sh',
        os.path.join(target_dir, 'netController.sh'), data)


