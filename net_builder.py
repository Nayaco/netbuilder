#!python
import subprocess, os
import util
# process = subprocess.Popen(['echo', 'More output'],
#                      stdout=subprocess.PIPE, 
#                      stderr=subprocess.PIPE)
# stdout, stderr = process.communicate()
# print(stdout, stderr)
input_data = {
    'script_pwd': os.getcwd(),
    'force': False,
    'max_retry': 3,
    'cli_delay': 5,
    'image_tag': 'latest',
    'ca_image_tag': 'latest',
    'database': 'leveldb',
    'ca_network_name': 'test',
    'base_network_name': 'test',
    'crypto_method': 'cryptogen',
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
            'peerorgs': ['Org1', 'Org2'],
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

util.msp_autofill(input_data)


env_vars = os.environ.copy()
env_vars["PATH"] = input_data['script_pwd'] + "bin:" + env_vars["PATH"]

import create_configurations
import create_script

create_configurations.gen_configtx_conf('test', input_data)
create_configurations.gen_cryptogen_conf('test', input_data)
create_configurations.gen_dockers_conf('test', input_data)
create_configurations.gen_fabric_ca_server_conf('test', input_data)

create_script.create_registerEnroll('test', input_data)
create_script.create_envVars('test', input_data)
create_script.create_createChannel('test', input_data)
create_script.create_netController('test', input_data)

