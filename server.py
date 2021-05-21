#!python
import os, glob, json, copy
import weaver.util as util
import weaver.createConfigurations as createConfigurations
import weaver.createScript as createScript
import weaver.ledgerController as ledgerController
import weaver.freePorts as freePorts 
from weaver.ledgerController import LedgerBootError
from weaver.ledgerStore import LedgerStore
from weaverConfig import getConfig


from flask import Flask, render_template, session, copy_current_request_context
from flask import jsonify
from flask import request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, supports_credentials=True)

bindir  = os.getcwd() + '/bin'
workdir = os.getcwd() + '/workdir'
if not os.path.exists(workdir):
    os.makedirs(workdir)
inputmeta = getConfig(workdir, bindir)
ledgerStore = LedgerStore('%s/%s' % (workdir, 'ledgerstore.json')) 

fports = freePorts.FreePorts()
@app.route("/generate", methods=['POST'])
@cross_origin()
def generate():
    origin_input = request.get_json()

    input_data = copy.deepcopy(inputmeta)
    input_data['target_path'] = origin_input['project']
    input_data['project_name'] = origin_input['project']
    input_data['ca_network_name'] = 'net' + origin_input['project']
    input_data['base_network_name'] = 'net' + origin_input['project']
    input_data['orderer']['port'] = fports.get_free()
    casedomain = 'blockcase'+ origin_input['project'] +'.org'
    input_data['orderer']['orderer_domain'] = casedomain
    if input_data['orderer']['port'] == -1: 
        fports.free_ports([input_data['orderer']['port']])
        return jsonify({'status': 'PORTS BUSY'})
    port_assign = {input_data['orderer']['port']}

    for i, peer in enumerate(origin_input['peers']):
        port_fororg = {fports.get_free() for j in  range(0, 2 * peer['nodes'])}
        port_fororg.add(fports.get_free())
        port_assign.update(port_fororg)
        if -1 in port_fororg:
            fports.free_ports(port_assign)
            return jsonify({'status': 'PORTS BUSY'})
        input_data['peerorgs'].append({
            'peer_name': 'ORG%d' % peer['index'],
            'peer_domain': casedomain,
            'peer_nodes': peer['nodes'],
            'peer_users': 1,
            'orgCA_admin': 'org%dadmin' % peer['index'],
            'orgCA_pw': 'org%dpw' % peer['index'],
            'peernodes': [
                {
                    'port': port_fororg.pop(),
                    'CCport': port_fororg.pop(),
                    'CApw': 'peer%dpw' % j
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
            'peer': 'org%d' % peer['index'],
            'peer_affiliation': [
                'department1',
            ]
        })
    for i, channel in enumerate(origin_input['channels']):
        input_data['channels'].append({
            'channel_name': 'channel%d' % i,
            'channel_profile': 'ChanProfile%d' % i,
            'peerorgs': ['ORG%d' % j for j in channel['peerorgs']]
        })
        input_data['tx']['channel_profiles'].append({
            'profile_name': 'ChanProfile%d' % i,
            'consortium_name': 'ChanConsortium%d' % i,
            'peerorgs': ['ORG%d' % j for j in channel['peerorgs']]
        })

    util.data_autofill(input_data)
    try:
        controller = ledgerController.LedgerController(data=input_data, \
            logfile='%s/%s_log' % (workdir, origin_input['project']))
        controller.deployLedger()
    except LedgerBootError as e:
        print(e.msg)
    ledgerStore.append(input_data, status='running')
    return jsonify({'status': 'OK'})

@app.route("/log", methods=['GET'])
@cross_origin()
def get_log():
    project = request.args.get('project')
    line_from = int(request.args.get('line_from'))
    log_lines = []
    with open('%s/%s_log' % (workdir, project), 'r') as f:
        lines = f.readlines()
        log_lines = lines[line_from:]
    return jsonify({
        'log': log_lines,
        'over': ledgerStore.exist(project)
    })

@app.route("/activate", methods=['GET'])
@cross_origin()
def activate_net():
    project = request.args.get('project')
    input_data = ledgerStore[project]
    if input_data is not None and input_data['status'] != 'running':
        controller = ledgerController.LedgerController(data=input_data, \
                logfile='%s/%s_log' % (workdir, project))
        controller.deployLedger()
        ledgerStore[project]['status'] = 'running'
    return jsonify({'status': 'OK'})

@app.route("/list", methods=['GET'])
@cross_origin()
def list_nets():    
    nets = [ledgerStore[key] for key in ledgerStore.items()]
    return jsonify({'status': 'OK', 'networks': nets})

@app.route("/suspend", methods=['GET'])
@cross_origin()
def suspend_net():
    project = request.args.get('project')
    input_data = ledgerStore[project]
    if input_data is not None and input_data['status'] == 'running':
        controller = ledgerController.LedgerController(data=input_data, \
                logfile='%s/%s_log' % (workdir, project))
        controller.suspendLedger()
        ledgerStore[project]['status'] = 'suspend'
    return jsonify({'status': 'OK'})

@app.route("/remove", methods=['GET'])
@cross_origin()
def remove_net():    
    project = request.args.get('project')
    input_data = ledgerStore[project]
    if input_data is not None:
        controller = ledgerController.LedgerController(data=input_data, \
                logfile='%s/%s_log' % (workdir, project))
        controller.shutdownLedger()
        controller.removeLedger()
        fports.free_ports([input_data['orderer']['port']] + \
            [i['CA']['port'] for i in input_data['peerorgs']] + \
            [j['port'] for i in input_data['peerorgs'] for j in i['peernodes']] + \
            [j['CCport'] for i in input_data['peerorgs'] for j in i['peernodes']])
        ledgerStore.remove(project)
    return jsonify({'status': 'OK'})

if __name__ == '__main__':
    app.run(debug=True, port=8081)