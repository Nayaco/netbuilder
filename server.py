#!python
import os
import json
import copy
import waver.util as util
import waver.createConfigurations as createConfigurations
import waver.createScript as createScript
import waver.ledgerController as ledgerController
from waver.ledgerController import LedgerBootError

from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

input_meta = {
    'script_pwd': os.getcwd(),
    'force': False,
    'max_retry': 3,
    'cli_delay': 5,
    'image_tag': 'latest',
    'ca_image_tag': 'latest',
    'database': 'leveldb',
    'crypto_method': 'cryptogen',
    'environment': [
        ['CC_VERSION', '1.0']
    ],
    'core': {
        'id': 'aloha',
        'network_id': 'dev'
    },
    'tx': {
        'genesis_channel': 'system-channel',
        'genesis_profile': 'OrdererGenesis',
        'channel_profiles': [],
    },
    'channels': [],
    'chaincodes': [],
    'affiliations': [],
    'orderer': { 
        'orderer_name': 'Orderer',
        'orderer_domain': 'blockcase.org',
        'CAid': 'orderer',
        'CApw': 'ordererpw',
        'orgCA_admin': 'ordererAdmin',
        'orgCA_pw': 'ordererAdminpw',
        'CA': {
            'debug': False,
            'admin': 'admin',
            'adminpw': 'adminpw'
        }
    },
    'peerorgs': [],
}

port_from = 7001
port_end = 8000
port_busy = set()
port_free = set(range(port_from, port_end))


def _get_free():
    try:
        p = port_free.pop()
        port_busy.add(p)
        return p
    except:
        return -1
def _free_ports(port_list):
    port_free.update(port_list)
    for i in port_list:
        port_busy.discard(i)

@app.route("/generate", methods=['POST'])
def generate():
    origin_input = request.get_json()
    input_data = copy.deepcopy(input_meta)
    input_data['target_path'] = origin_input['project']
    input_data['project_name'] = origin_input['project']
    input_data['ca_network_name'] = 'net' + origin_input['project']
    input_data['base_network_name'] = 'net' + origin_input['project']
    input_data['orderer']['port'] = _get_free()
    if input_data['orderer']['port'] == -1: 
        _free_ports([input_data['orderer']['port']])
        return jsonify({'status': 'PORTS BUSY'})

    port_assign = {input_data['orderer']['port']}
    for i, peer in enumerate(origin_input['peers']):
        port_fororg = {_get_free() for j in  range(0, 2 * peer['nodes'])}
        port_fororg.add(_get_free())
        port_assign.update(port_fororg)
        if -1 in port_fororg:
            _free_ports(port_assign)
            return jsonify({'status': 'PORTS BUSY'})
        input_data['peerorgs'].append({
            'peer_name': 'ORG' + str(peer['index']),
            'peer_domain': 'example.com',
            'peer_node': peer['nodes'],
            'peer_users': 1,
            'orgCA_admin': 'org' + str(peer['index']) + 'admin',
            'orgCA_pw': 'org' + str(peer['index']) + 'pw',
            'peernodes': [
                {
                    'port': port_fororg.pop(),
                    'CCport': port_fororg.pop(),
                    'capw': 'peer' + str(j) + 'pw'
                } 
                for j in range(0, peer['nodes']) 
            ],
            'CA': {
                'port': port_fororg.pop(),
                'debug': False,
                'admin': 'admin',
                'adminpw': 'adminpw'
            }
        })
        input_data['affiliations'].append({
            'peer': 'org' + str(peer['index']),
            'peer_affiliation': [
                'department1',
            ]
        })
    for i, channel in enumerate(origin_input['channels']):
        input_data['channels'].append({
            'channel_name': 'channel' + str(i),
            'channel_profile': 'ChanProfile' + str(i),
            'peerorgs': ['ORG' + str(j) for j in channel['peerorgs']]
        })
        input_data['tx']['channel_profiles'].append({
            'profile_name': 'ChanProfile' + str(i),
            'consortium_name': 'ChanConsortium' + str(i),
            'peerorgs': ['ORG' + str(j) for j in channel['peerorgs']]
        })
    print(json.dumps(input_data, indent=2))
    return jsonify({'status': 'OK'})
    
@app.route("/build", methods=['POST'])
def buildn():
    input_data = request.get_json()
    util.data_autofill(input_data)
    print(input_data['target_path'])
    if not os.path.exists(os.getcwd() + '/' + input_data['target_path']):
        createConfigurations.gen_core_config_conf(input_data['target_path'], input_data)
        createConfigurations.gen_cryptogen_conf(input_data['target_path'], input_data)
        createConfigurations.gen_dockers_conf(input_data['target_path'], input_data)
        createConfigurations.gen_fabric_ca_server_conf(input_data['target_path'], input_data)

        createScript.create_registerEnroll(input_data['target_path'], input_data)
        createScript.create_envVars(input_data['target_path'], input_data)
        createScript.create_createChannel(input_data['target_path'], input_data)
        createScript.create_DeployChaincode(input_data['target_path'], input_data)
        createScript.create_netController(input_data['target_path'], input_data)
    try:
        controller = ledgerController.LedgerController(target_path=os.getcwd() + '/test', data=input_data)
        controller.deployLedger()
    except LedgerBootError as e:
        print(e.msg)

    return jsonify({'status': 'OK'})

app.run(debug=True, port=8081)