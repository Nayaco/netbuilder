import util
import os
def gen_configtx_conf(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'config')): 
        os.mkdir(os.path.join(target_dir, 'config'))

    util.render_template('config/configtx.yaml', 
        os.path.join(target_dir, 'config', 'configtx.yaml'), data)


def gen_cryptogen_conf(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'organizations')): 
        os.mkdir(os.path.join(target_dir, 'organizations'))
    if not os.path.exists(os.path.join(target_dir, 'organizations', 'cryptogen')): 
        os.mkdir(os.path.join(target_dir, 'organizations', 'cryptogen'))

    util.render_template('organizations/cryptogen/crypto-config-orderer.yaml', 
        os.path.join(target_dir, 'organizations', 'cryptogen', 'crypto-config-orderer.yaml'), data['orderer'])
    for peer in data['peerorgs']:
        util.render_template('organizations/cryptogen/crypto-config-peer.yaml', 
            os.path.join(target_dir, 'organizations', 'cryptogen', 'crypto-config-' + peer['peer_name'].lower() + '.yaml'), peer)

def gen_dockers_conf(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'docker')): 
        os.mkdir(os.path.join(target_dir, 'docker'))
    util.render_template('docker/docker-compose-ca.yaml', 
        os.path.join(target_dir, 'docker', 'docker-compose-ca.yaml'), data)
    util.render_template('docker/docker-compose-base.yaml', 
        os.path.join(target_dir, 'docker', 'docker-compose-base.yaml'), data)

def gen_fabric_ca_server_conf(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'organizations')): 
        os.mkdir(os.path.join(target_dir, 'organizations'))
    if not os.path.exists(os.path.join(target_dir, 'organizations', 'fabric-ca')):
        os.mkdir(os.path.join(target_dir, 'organizations', 'fabric-ca'))
    for peer in data['peerorgs']:
        if not os.path.exists(os.path.join(target_dir, 'organizations', 'fabric-ca', peer['peer_name'].lower())):
            os.mkdir(os.path.join(target_dir, 'organizations', 'fabric-ca', peer['peer_name'].lower()))
        util.render_template('organizations/fabric-ca/fabric-ca-server-config.yaml', 
            os.path.join(target_dir, 'organizations', 'fabric-ca', peer['peer_name'].lower(), 'fabric-ca-server-config.yaml'),
            {
                'affiliations': data['affiliations'],
                'peer': peer
            })
    orderer_path = os.path.join(target_dir, 'organizations', 'fabric-ca', data['orderer']['orderer_name'].lower() + 'Org')
    if not os.path.exists(orderer_path):
        os.mkdir(orderer_path)
    util.render_template('organizations/fabric-ca/fabric-ca-server-config.yaml', 
        os.path.join(orderer_path, 'fabric-ca-server-config.yaml'),
        {
            'affiliations': data['affiliations'],
            'peer': data['orderer']
        })
