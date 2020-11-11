#!/bin/sh
export CORE_PEER_TLS_ENABLED=true
export {{ orderer.orderer_name | upper }}_CA=${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer.orderer_name | lower }}.{{ orderer.orderer_domain }}/msp/tlscacerts/tlsca.{{ orderer.orderer_domain }}-cert.pem
{%- for peer in peerorgs %}
{%- set peer_dir = (peer.peer_name | lower) ~ '.' ~ (peer.peer_domain) %}
{%- for peernode in peer.peernodes %}
{%- set node_dir = 'peer' ~ (loop.index0) ~ '.' ~ peer_dir %}
export PEER{{ loop.index0 }}_{{ peer.peer_name | upper }}_CA=${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/ca.crt
{%- endfor %}
{%- endfor %}

set{{ orderer.orderer_name }}Globals() {
  export CORE_PEER_LOCALMSPID="{{ orderer.orderer_name }}MSP"
  export CORE_PEER_TLS_ROOTCERT_FILE=${{ orderer.orderer_name | upper }}_CA
  export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/users/Admin@{{ orderer.orderer_domain }}/msp
}

setGlobals() {
  local USING_ORG=""
  local USING_PEER=""
  USING_ORG=$1
  USING_PEER=$1
{%- for peer in peerorgs %}
{%- set peer_dir = (peer.peer_name | lower) ~ '.' ~ (peer.peer_domain) %}
{%- set index_peer = loop.index0 %}
{%- for peernode in peer.peernodes %}
{%- set node_dir = 'peer' ~ (loop.index0) ~ '.' ~ peer_dir %}
{%- if (index_peer == 0) and (loop.index0 == 0) %}
  if [ $USING_ORG -eq "{{ peer.peer_name }}" && $USING_PEER -eq {{ loop.index0 }} ]; then
{%- else %}
  elif [ $USING_ORG -eq "{{ peer.peer_name }}" && $USING_PEER -eq {{ loop.index0 }} ]; then
{%- endif %}
    export CORE_PEER_LOCALMSPID="{{ peer.peer_name }}MSP"
    export CORE_PEER_TLS_ROOTCERT_FILE=$PEER{{ loop.index0 }}_{{ peer.peer_name | upper }}_CA
    export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/{{ peer_dir }}/users/Admin@{{ peer_dir }}/msp
    export CORE_PEER_ADDRESS=localhost:{{ peernode.port }}
{%- endfor %}
{%- endfor %}
  else
    exit 1
  fi
  if [ "$VERBOSE" == "true" ]; then
    env | grep CORE
  fi
}

