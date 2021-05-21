INPUTMETA = {
    'script_pwd': '',
    'binaray_pwd': '',
    'force': False,
    'max_retry': 3,
    'cli_delay': 5,
    'image_tag': '2.2.2',
    'ca_image_tag': '2.2.2',
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
def getConfig(workdir, bindir):
    INPUTMETA['script_pwd'] = workdir
    INPUTMETA['binaray_pwd'] = bindir
    return INPUTMETA