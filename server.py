#!python

from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

import subprocess, os
import util
import createConfigurations
import createScript
import ledgerController
from ledgerController import LedgerBootError

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

app.run(debug=True)