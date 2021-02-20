#!/bin/bash 

export FABRIC_CFG_PATH=${PWD}/config
export VERBOSE=false
export PATH=${PWD}/../bin:$PATH

. ./scripts/envVars.sh

OS_ARCH=$(echo "$(uname -s | tr '[:upper:]' '[:lower:]' | sed 's/mingw64_nt.*/windows/')-$(uname -m | sed 's/x86_64/amd64/g')" | awk '{print tolower($0)}')
CRYPTO="{{ crypto_method }}"
MAX_RETRY={{ max_retry }}
CLI_DELAY={{ cli_delay }}
CHANNEL_NAME="mychannel"
CC_NAME="basic"
CC_SRC_PATH="NA"
CC_END_POLICY="NA"
CC_COLL_CONFIG="NA"
CC_INIT_FCN="NA"

COMPOSE_FILE_BASE=docker/docker-compose-base.yaml
COMPOSE_FILE_COUCH=docker/docker-compose-couch.yaml
COMPOSE_FILE_CA=docker/docker-compose-ca.yaml

CC_SRC_LANGUAGE="go"
CC_VERSION="1.0"
CC_SEQUENCE=1
IMAGETAG="{{ image_tag }}"
CA_IMAGETAG="{{ ca_image_tag }}"
DATABASE="{{ database }}"

FORCE={{ force }}

function clearContainers() {
  if [ -d "organizations/peerOrganizations" ]; then
    rm -Rf organizations/peerOrganizations && rm -Rf organizations/ordererOrganizations
  fi
  CONTAINER_IDS=$(docker ps -a | awk '($2 ~ /dev-peer.*/ || $2 ~ /*.com/ || $2 ~ /ca*/) {print $1}')
  if [ -z "$CONTAINER_IDS" -o "$CONTAINER_IDS" == " " ]; then
    echo "---- No containers available for deletion ----"
  else
    docker rm -f $CONTAINER_IDS
  fi
}
{%- if crypto_method == 'cryptogen' %} 
function createCrypto() {
  {% for peer in peerorgs %}
  set -x
  cryptogen generate --config=./organizations/cryptogen/crypto-config-{{ peer.peer_name | lower }}.yaml --output="organizations"
  set +x 
  {% endfor %}
  set -x
  cryptogen generate --config=./organizations/cryptogen/crypto-config-orderer.yaml --output="organizations"   
  res=$?
  set +x
}
{%- endif %}

function createConsortium() {
  which configtxgen
  if [ "$?" -ne 0 ]; then
    echo "Configtxgen not found"
    exit 1
  fi
  set -x
  configtxgen -profile {{ tx.genesis_profile }} -channelID {{ tx.genesis_channel }} -outputBlock ./system-genesis-block/genesis.block
  res=$?
  set +x
  if [ $res -ne 0 ]; then
    echo $'\e[1;32m'"Failed to generate orderer genesis block..."$'\e[0m'
    exit 1
  fi
}

function createOrgs() {
  if [ -d "organizations/peerOrganizations" ]; then
    rm -Rf organizations/peerOrganizations && rm -Rf organizations/ordererOrganizations
  fi
  {%- if crypto_method == 'cryptogen' %} 
  createCrypto
  {%- elif crypto_method == 'CA' %}
  IMAGE_TAG=${CA_IMAGETAG} docker-compose -f $COMPOSE_FILE_CA up -d 2>&1
  . organizations/fabric-ca/registerEnroll.sh
  sleep 10
  {%- for peer in peerorgs %}
  create{{ peer.peer_name }}
  {%- endfor %}
  create{{ orderer.orderer_name }}
  {%- else %}
  echo "Fail to determine crypto method"
  exit 1
  {%- endif %}
}

function netUp() {
    if [ $FORCE == true ]; then
      clearContainers
    fi
    if [ ! -d "organizations/peerOrganizations" ]; then
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
        echo "Unable to start network"
        exit 1
    fi
}

function createChannel() {
  if [ ! -d "organizations/peerOrganizations" ]; then
    netUp
  fi
{%- if channels|length > 0 %}
  chmod +x scripts/createChannel*.sh 
{%- for channel in channels %}
  scripts/createChannel{{ channel.channel_name }}.sh $CLI_DELAY $MAX_RETRY $VERBOSE
{%- endfor %}
{%- endif %}
}

function deployChaincode() {
  echo "Deploy Chaincode"
{%- if chaincodes|length > 0 %}
  chmod +x scripts/deployChaincode*.sh
{%- for chaincode in chaincodes %}
  scripts/deployChaincode{{chaincode.cc_name}}.sh $CLI_DELAY $MAX_RETRY $VERBOSE
{%- endfor %}
{%- endif %}
}

MODE=$1
if [ "${MODE}" == "up" ]; then
  netUp
elif [ "${MODE}" == "createChannel" ]; then
  createChannel
elif [ "${MODE}" == "deployChaincode" ]; then
  deployChaincode
else
  exit 0
fi