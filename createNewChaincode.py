#!python
import subprocess
import os
import weaver.util as util

chiancode = {
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



