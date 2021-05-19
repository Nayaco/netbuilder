#!python
import subprocess
import os
import waver.util as util
input_data = {
    'target_path': 'test', 
    'script_pwd': os.getcwd(),
    'force': False,
    'max_retry': 3,
    'cli_delay': 5,
    'project_name': 'net',
    'image_tag': '2.2.2',
    'ca_image_tag': '2.2.2',
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
                'profile_name': 'TwoOrgsChannel1',
                'consortium_name': 'SampleConsortium1',
                'peerorgs': ['Org1', 'Org2']
            },
            {
                'profile_name': 'TwoOrgsChannel2',
                'consortium_name': 'SampleConsortium2',
                'peerorgs': ['Org2', 'Org3']
            }
        ]
    },
    'channels': [
        {
            'channel_name': 'mychannel',
            'channel_profile': 'TwoOrgsChannel1',
            'peerorgs': ['Org1', 'Org2']
        },
        {
            'channel_name': 'mychannel2',
            'channel_profile': 'TwoOrgsChannel2',
            'peerorgs': ['Org2', 'Org3']
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
        },
        {
            'peer': 'org3',
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
            'peer_nodes': 2,
            'peer_users': 1,
            'orgCA_admin': 'org1admin',
            'orgCA_pw': 'org1pw',
            'peernodes': [
                {
                    'port': 7051,
                    'CCport': 7052,
                    'CApw': 'peer0pw'
                },
                {
                    'port': 7061,
                    'CCport': 7062,
                    'CApw': 'peer1pw'
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
        {
            'peer_name': 'Org3',
            'peer_domain': 'example.com',
            'peer_nodes': 1,
            'peer_users': 1,
            'orgCA_admin': 'org3admin',
            'orgCA_pw': 'org3pw',
            'peernodes': [
                {
                    'port': 8251,
                    'CCport': 8252,
                    'CApw': 'peer0pw'
                }
            ],
            'CA': {
                'port': 8254,
                'debug': False,
                'admin': 'admin',
                'adminpw': 'adminpw'
            }
        },
    ],
}

util.data_autofill(input_data)

# import waver.createConfigurations as createConfigurations
# import waver.createScript as createScript

# createConfigurations.gen_core_config_conf('test', input_data)
# createConfigurations.gen_cryptogen_conf('test', input_data)
# createConfigurations.gen_dockers_conf('test', input_data)
# createConfigurations.gen_fabric_ca_server_conf('test', input_data)

# createScript.create_registerEnroll('test', input_data)
# createScript.create_envVars('test', input_data)
# createScript.create_createChannel('test', input_data)
# createScript.create_DeployChaincode('test', input_data)
# createScript.create_netController('test', input_data)

import waver.ledgerController as ledgerController
from waver.ledgerController import LedgerBootError
try:
    controller = ledgerController.LedgerController(target_path=os.getcwd() + '/test', data=input_data)
    controller.deployLedger()
except LedgerBootError as e:
    print(e.msg)
