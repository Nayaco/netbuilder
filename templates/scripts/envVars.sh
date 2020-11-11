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
