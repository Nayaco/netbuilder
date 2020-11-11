#!/bin/sh 

export FABRIC_CFG_PATH=${PWD}/configtx
export VERBOSE=false
. ./envVars.sh

OS_ARCH=$(echo "$(uname -s | tr '[:upper:]' '[:lower:]' | sed 's/mingw64_nt.*/windows/')-$(uname -m | sed 's/x86_64/amd64/g')" | awk '{print tolower($0)}')
# Using crpto vs CA. default is cryptogen
CRYPTO="cryptogen"
# timeout duration - the duration the CLI should wait for a response from
# another container before giving up
MAX_RETRY=5
# default for delay between commands
CLI_DELAY=3
# channel name defaults to "mychannel"
CHANNEL_NAME="mychannel"
# chaincode name defaults to "basic"
CC_NAME="basic"
# chaincode path defaults to "NA"
CC_SRC_PATH="NA"
# endorsement policy defaults to "NA". This would allow chaincodes to use the majority default policy.
CC_END_POLICY="NA"
# collection configuration defaults to "NA"
CC_COLL_CONFIG="NA"
# chaincode init function defaults to "NA"
CC_INIT_FCN="NA"
# use this as the default docker-compose yaml definition
COMPOSE_FILE_BASE=docker/docker-compose-test-net.yaml
# docker-compose.yaml file if you are using couchdb
COMPOSE_FILE_COUCH=docker/docker-compose-couch.yaml
# certificate authorities compose file
COMPOSE_FILE_CA=docker/docker-compose-ca.yaml
# use this as the docker compose couch file for org3
COMPOSE_FILE_COUCH_ORG3=addOrg3/docker/docker-compose-couch-org3.yaml
# use this as the default docker-compose yaml definition for org3
COMPOSE_FILE_ORG3=addOrg3/docker/docker-compose-org3.yaml
#
# use go as the default language for chaincode
CC_SRC_LANGUAGE="go"
# Chaincode version
CC_VERSION="1.0"
# Chaincode definition sequence
CC_SEQUENCE=1
# default image tag
IMAGETAG="latest"
# default ca image tag
CA_IMAGETAG="latest"
# default database
DATABASE="leveldb"

function clearContainers() {
  CONTAINER_IDS=$(docker ps -a | awk '($2 ~ /dev-peer.*/ || $2 ~ /*.com/ || $2 ~ /ca*/) {print $1}')
  if [ -z "$CONTAINER_IDS" -o "$CONTAINER_IDS" == " " ]; then
    echo "---- No containers available for deletion ----"
  else
    docker rm -f $CONTAINER_IDS
  fi
}

function createCrypto() {
    set -x
    cryptogen generate --config=./organizations/cryptogen/crypto-config-org1.yaml --output="organizations"
    res=$?
    set +x
    echo $res

    set -x
    cryptogen generate --config=./organizations/cryptogen/crypto-config-org2.yaml --output="organizations"
    res=$?
    set +x
    echo $res

    set -x
    cryptogen generate --config=./organizations/cryptogen/crypto-config-orderer.yaml --output="organizations"   
    res=$?
    set +x
    echo $res
}

function createConsortium() {
  which configtxgen
  if [ "$?" -ne 0 ]; then
    echo "configtxgen tool not found. exiting"
    exit 1
  fi

  echo "#########  Generating Orderer Genesis block ##############"
  set -x
  configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel -outputBlock ./system-genesis-block/genesis.block
  res=$?
  set +x
  if [ $res -ne 0 ]; then
    echo $'\e[1;32m'"Failed to generate orderer genesis block..."$'\e[0m'
    exit 1
  fi
}

function createOrgs() {
    IMAGE_TAG=${CA_IMAGETAG} docker-compose -f $COMPOSE_FILE_CA up -d 2>&1

    . organizations/fabric-ca/registerEnroll.sh

    sleep 10

    createOrg1
    createOrg2
    createOrderer
}

function netUp() {
    clearContainers 
    
    if [[ ! -d "./organizations/ordererOrganizations" && ! -d "./organizations/peerOrganizations" ]]; then
      createCrypto
    fi
    if [[ ! -d "./organizations/system-genesis-block" ]]; then
      createOrgs
      createConsortium
    fi

    COMPOSE_FILES="-f ${COMPOSE_FILE_BASE}"

    if [ "${DATABASE}" == "couchdb" ]; then
        COMPOSE _FILES="${COMPOSE_FILES} -f ${COMPOSE_FILE_COUCH}"
    fi

    IMAGE_TAG=$IMAGETAG docker-compose ${COMPOSE_FILES} up -d 2>&1

    docker ps -a
    if [ $? -ne 0 ]; then
        echo "ERROR !!!! Unable to start network"
        exit 1
    fi
}

MODE=$1

# clearContainers

if [ "${MODE}" == "up" ]; then
  netUp
elif [ "${MODE}" == "createCrypto" ]; then
  createCrypto
elif [ "${MODE}" == "createConsortium" ]; then
  createConsortium
elif [ "${MODE}" == "createOrgs" ]; then
  createOrgs
else
  exit 1
fi