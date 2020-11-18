#!/bin/bash

CHANNEL_NAME="{{ channel.channel_name }}"
CHANNEL_PROFILE="{{ channel.channel_profile }}"
CHANNEL_ORGMSPS=({% for msp in channel.msps %}{{ msp }} {% endfor %})
CHANNEL_PEERS=({% for org in channel.peerorgs %}{{ org }} {% endfor %})
CHANNEL_MAIN_ORG={{ channel.peerorgs[0] }}
CHANNEL_MAIN_NODE=0
DELAY="$1"
MAX_RETRY="$2"
VERBOSE="$3"

FABRIC_CFG_PATH=${PWD}/config

: ${DELAY:="3"}
: ${MAX_RETRY:="5"}
: ${VERBOSE:="false"}

. ./scripts/envVars.sh

if [ ! -d "channel-artifacts" ]; then
	mkdir channel-artifacts
fi

createChannelBlock() {
  set -x
  configtxgen -profile $CHANNEL_PROFILE \
    -outputCreateChannelTx ./channel-artifacts/${CHANNEL_NAME}.pb -channelID $CHANNEL_NAME
  res=$?
  set +x
  if [ $res -ne 0 ]; then
    exit 1
  fi
}

createAncorPeerBlock() {
  for Omsp in ${CHANNEL_ORGMSPS[@]}; do
    set -x
    configtxgen -profile $CHANNEL_PROFILE \
      -outputAnchorPeersUpdate ./channel-artifacts/${Omsp}Anchor_${CHANNEL_NAME}.pb -channelID $CHANNEL_NAME -asOrg ${Omsp}
    res=$?
    set +x
    if [ $res -ne 0 ]; then
      exit 1
    fi
  done
}

createChannel() {
  setGlobals $CHANNEL_MAIN_ORG $CHANNEL_MAIN_NODE
  local rc=1
  local COUNTER=1
  while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ] ; do
    sleep $DELAY
    set -x
    peer channel create -o localhost:{{ orderer.port }} -c $CHANNEL_NAME \
      --ordererTLSHostnameOverride {{ orderer.orderer_name | lower }}.{{ orderer.orderer_domain }} \
      -f ./channel-artifacts/${CHANNEL_NAME}.pb \
      --outputBlock ./channel-artifacts/${CHANNEL_NAME}.pb --tls --cafile $ORDERER_CA >&log.txt
    res=$?
    set +x
    let rc=$res
    COUNTER=$(expr $COUNTER + 1)
  done
  cat log.txt
}

joinChannel() {
    ORG=$1
    PEER=$2
    setGlobals $ORG $PEER
    local rc=1
    local COUNTER=1
    while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ] ; do
    sleep $DELAY
    set -x
    peer channel join -b ./channel-artifacts/$CHANNEL_NAME.pb >&log.txt
    res=$?
    set +x
        let rc=$res
        COUNTER=$(expr $COUNTER + 1)
    done
	cat log.txt
}

updateAnchorPeers() {
    ORG=$1
    PEER=$2
    setGlobals $ORG $PEER
    local rc=1
    local COUNTER=1
    while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ] ; do
    sleep $DELAY
    set -x
      # TODO: fix orderer address to be able to be visit
      peer channel update -o localhost:{{ orderer.port }} \
          --ordererTLSHostnameOverride {{ orderer.orderer_name | lower }}.{{ orderer.orderer_domain }} \
          -c $CHANNEL_NAME -f ./channel-artifacts/${CORE_PEER_LOCALMSPID}Anchor_${CHANNEL_NAME}.pb --tls --cafile $ORDERER_CA >&log.txt
    res=$?
    set +x
        let rc=$res
        COUNTER=$(expr $COUNTER + 1)
    done
    cat log.txt
    sleep $DELAY
}

createChannelBlock
createAncorPeerBlock
createChannel

for org in ${CHANNEL_PEERS[@]}; do
  joinChannel $org 0
done

for org in ${CHANNEL_PEERS[@]}; do
  updateAnchorPeers $org 0
done

exit 0
