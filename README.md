# NET-WEAVER
A hyperledger network constructor.

## build
```
pip install -r requirements.txt 
```

## local build
```
./netBuilder.py
```
Configuration is hard-coded, it'll be a shell command tool later.

## http server
```
./server.py
```
- POST:`/build`

### configuration(json)
```json
{
    "target_path": "test",
    "script_pwd": "/home/hanabi/workbench/project-2020/BlockChain2020/fabric_bin/netbuilder",
    "force": false,
    "max_retry": 3,
    "cli_delay": 5,
    "project_name": "net",
    "image_tag": "latest",
    "ca_image_tag": "latest",
    "database": "leveldb", 
    "ca_network_name": "test",
    "base_network_name": "test",
    "crypto_method": "cryptogen",
    "environment": [
        ["MY_CC_VERSION", "1.0"]
    ],
    "core": {
        "id": "aloha",
        "network_id": "dev"
    },
    "tx": {
        "genesis_channel": "system-channel",
        "genesis_profile": "TwoOrgsOrdererGenesis",
        "channel_profiles": [
            {
                "profile_name": "TwoOrgsChannel",
                "peerorgs": ["Org1", "Org2"]
            }
        ]
    },
    "channels": [
        {
            "channel_name": "mychannel",
            "channel_profile": "TwoOrgsChannel",
            "peerorgs": ["Org1", "Org2"]
        }
    ],
    "chaincodes": [
        {
            "channel": "mychannel",
            "cc_name": "basic",
            "cc_path_origin": "/home/hanabi/workbench/project-2020/BlockChain2020/fabric_bin/netbuilder/chaincodes/basic",
            "cc_path": "/home/hanabi/workbench/project-2020/BlockChain2020/fabric_bin/netbuilder/test/chaincodes/basic",
            "cc_lang": "go",
            "cc_version": "1.0",
            "cc_seq": "1",
            "init_func": "initLedger",
            "sig_policy": "NA",
            "col_config": "NA",
            "endorse_peers": [
                {"org": "Org1", "peer": 0},
                {"org": "Org2", "peer": 0}
            ]
        }
    ],
    "affiliations": [
        {
            "peer": "org1",
            "peer_affiliation": [
                "department1",
                "department2"
            ]
        },
        {
            "peer": "org2",
            "peer_affiliation": [
                "department1"
            ]
        }
    ],
    "orderer": {
        "orderer_name": "Orderer",
        "orderer_domain": "example.com",
        "port": 7050,
        "CAid": "orderer",
        "CApw": "ordererpw",
        "orgCA_admin": "ordererAdmin",
        "orgCA_pw": "ordererAdminpw",
        "CA": {
            "port": 9054,
            "debug": false,
            "admin": "admin",
            "adminpw": "adminpw"
        }
    },
    "peerorgs": [
        {
            "peer_name": "Org1",
            "peer_domain": "example.com",
            "peer_nodes": 1,
            "peer_users": 1,
            "orgCA_admin": "org1admin",
            "orgCA_pw": "org1pw",
            "peernodes": [
                {
                    "port": 7051,
                    "CCport": 7052,
                    "CApw": "peer0pw"
                }
            ],
            "CA": {
                "port": 7054,
                "debug": false,
                "admin": "admin",
                "adminpw": "adminpw"
            }
        },
        {
            "peer_name": "Org2",
            "peer_domain": "example.com",
            "peer_nodes": 1,
            "peer_users": 1,
            "orgCA_admin": "org2admin",
            "orgCA_pw": "org2pw",
            "peernodes": [
                {
                    "port": 8051,
                    "CCport": 8052,
                    "CApw": "peer0pw"
                }
            ],
            "CA": {
                "port": 8054,
                "debug": false,
                "admin": "admin",
                "adminpw": "adminpw"
            }
        }
    ]
}
```
