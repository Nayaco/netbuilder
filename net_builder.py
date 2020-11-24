#!python
import subprocess, os
import util

input_data = {
    'script_pwd': os.getcwd(),
    'force': False,
    'max_retry': 3,
    'cli_delay': 5,
    'project_name': 'net',
    'image_tag': 'latest',
    'ca_image_tag': 'latest',
    'database': 'leveldb', 
    'ca_network_name': 'test',
    'base_network_name': 'test',
    'crypto_method': 'cryptogen',
    'environment': [
        ['MY_CC_VERSION', '1.0']
    ],
    'core': {
        'id': 'aloha',
        'network_id': 'dev'
    },
    'tx': {
        'genesis_channel': 'system-channel',
        'genesis_profile': 'TwoOrgsOrdererGenesis',
        'channel_profiles': [
            {
                'profile_name': 'TwoOrgsChannel',
                'peerorgs': ['Org1', 'Org2']
            }
        ]
    },
    'channels': [
        {
            'channel_name': 'mychannel',
            'channel_profile': 'TwoOrgsChannel',
            'peerorgs': ['Org1', 'Org2']
        }
    ],
    'chaincodes': [
        {
            'channel': 'mychannel',
            'cc_name': 'basic',
            'cc_path_origin': os.getcwd() + '/chaincodes/basic',
            'cc_path': os.getcwd() + '/test/chaincodes/basic',
            'cc_lang': 'go',
            'cc_version': '1.0',
            'cc_seq': '1',
            'init_func': 'initLedger',
            'sig_policy': 'NA',
            'col_config': 'NA',
            'endorse_peers': [
                {'org': 'Org1', 'peer': 0},
                {'org': 'Org2', 'peer': 0}
            ]
        }
    ],
    'affiliations': [
        {
            'peer': 'org1',
            'peer_affiliation': [
                'department1',
                'department2'
            ]
        },
        {
            'peer': 'org2',
            'peer_affiliation': [
                'department1'
            ]
        }
    ],
    'orderer': {
        'orderer_name': 'Orderer',
        'orderer_domain': 'example.com',
        'port': 7050,
        'CAid': 'orderer',
        'CApw': 'ordererpw',
        'orgCA_admin': 'ordererAdmin',
        'orgCA_pw': 'ordererAdminpw',
        'CA': {
            'port': 9054,
            'debug': False,
            'admin': 'admin',
            'adminpw': 'adminpw'
        }
    },
    'peerorgs': [
        {
            'peer_name': 'Org1',
            'peer_domain': 'example.com',
            'peer_nodes': 1,
            'peer_users': 1,
            'orgCA_admin': 'org1admin',
            'orgCA_pw': 'org1pw',
            'peernodes': [
                {
                    'port': 7051,
                    'CCport': 7052,
                    'CApw': 'peer0pw'
                }
            ],
            'CA': {
                'port': 7054,
                'debug': False,
                'admin': 'admin',
                'adminpw': 'adminpw'
            }
        },
        {
            'peer_name': 'Org2',
            'peer_domain': 'example.com',
            'peer_nodes': 1,
            'peer_users': 1,
            'orgCA_admin': 'org2admin',
            'orgCA_pw': 'org2pw',
            'peernodes': [
                {
                    'port': 8051,
                    'CCport': 8052,
                    'CApw': 'peer0pw'
                }
            ],
            'CA': {
                'port': 8054,
                'debug': False,
                'admin': 'admin',
                'adminpw': 'adminpw'
            }
        },
    ],
}

util.data_autofill(input_data)


env_vars = os.environ.copy()
env_vars["PATH"] = input_data['script_pwd'] + "bin:" + env_vars["PATH"]

import create_configurations
import create_script

create_configurations.gen_core_config_conf('test', input_data)
create_configurations.gen_cryptogen_conf('test', input_data)
create_configurations.gen_dockers_conf('test', input_data)
create_configurations.gen_fabric_ca_server_conf('test', input_data)

create_script.create_registerEnroll('test', input_data)
create_script.create_envVars('test', input_data)
create_script.create_createChannel('test', input_data)
create_script.create_DeployChaincode('test', input_data)
create_script.create_netController('test', input_data)

import run_script
from run_script import LedgerBootError
try:
    controller = run_script.LedgerController(target_path=os.getcwd() + '/test', data=input_data)
    controller.deployLedger()
except LedgerBootError as e:
    print(e.msg)
