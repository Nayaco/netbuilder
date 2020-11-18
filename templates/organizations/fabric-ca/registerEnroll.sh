
{%- for peer in peerorgs %}
{%- set peer_dir = (peer.peer_name | lower) ~ '.' ~ (peer.peer_domain) %}
{%- set peer_nam = (peer.peer_name | lower) %}

function create{{ peer.peer_name }}() {
  mkdir -p organizations/peerOrganizations/{{ peer_dir }}/
  export FABRIC_CA_CLIENT_HOME=${PWD}/organizations/peerOrganizations/{{ peer_dir }}/
  set -x
  fabric-ca-client enroll \
    -u https://{{ peer.CA.admin }}:{{ peer.CA.adminpw }}@localhost:{{ peer.CA.port }} \
    --caname ca-{{ peer_nam }} \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ peer_nam }}/tls-cert.pem
  set +x
#############################################################
  echo 'NodeOUs:
  Enable: true
  ClientOUIdentifier:
    Certificate: cacerts/localhost-{{ peer.CA.port }}-ca-{{ peer_nam }}.pem
    OrganizationalUnitIdentifier: client
  PeerOUIdentifier:
    Certificate: cacerts/localhost-{{ peer.CA.port }}-ca-{{ peer_nam }}.pem
    OrganizationalUnitIdentifier: peer
  AdminOUIdentifier:
    Certificate: cacerts/localhost-{{ peer.CA.port }}-ca-{{ peer_nam }}.pem
    OrganizationalUnitIdentifier: admin
  OrdererOUIdentifier:
    Certificate: cacerts/localhost-{{ peer.CA.port }}-ca-{{ peer_nam }}.pem
    OrganizationalUnitIdentifier: orderer' > ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/msp/config.yaml
#############################################################
{%- for peernode in peer.peernodes %}
  set -x
  fabric-ca-client register --caname ca-{{ peer_nam }} \
    --id.name peer{{ loop.index0 }} --id.secret {{ peernode.CApw }} --id.type peer \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ peer_nam }}/tls-cert.pem
  set +x
{%- endfor %}
  set -x
  fabric-ca-client register --caname ca-{{ peer_nam }} \
    --id.name {{ peer.orgCA_admin }} --id.secret {{ peer.orgCA_pw }} --id.type admin \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ peer_nam }}/tls-cert.pem
  set +x
#############################################################
  mkdir -p organizations/peerOrganizations/{{ peer_dir }}/peers
{%- for peernode in peer.peernodes %}
{%- set node_dir = 'peer' ~ (loop.index0) ~ '.' ~ (peer_dir) %}
  mkdir -p organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}
  set -x
  fabric-ca-client enroll -u https://peer{{ loop.index0 }}:{{ peernode.CApw }}@localhost:{{ peer.CA.port }} \
    --caname ca-{{ peer_nam }} \
    -M ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/msp \
    --csr.hosts {{ node_dir }} \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ peer_nam }}/tls-cert.pem
  set +x

  cp ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/msp/config.yaml \
    ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/msp/config.yaml
  
  set -x
  fabric-ca-client enroll -u https://peer{{ loop.index0 }}:{{ peernode.CApw }}@localhost:{{ peer.CA.port }} \
    --caname ca-{{ peer_nam }} \
    -M ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls \
    --enrollment.profile tls \
    --csr.hosts {{ node_dir }} \
    --csr.hosts localhost \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ peer_nam }}/tls-cert.pem
  set +x
#############################################################
  cp ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/tlscacerts/* \
    ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/ca.crt
  cp ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/signcerts/* \
    ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/server.crt
  cp ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/keystore/* \
    ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/server.key

  mkdir -p ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/msp/tlscacerts
  cp ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/tlscacerts/* \
    ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/msp/tlscacerts/ca.crt

  mkdir -p ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/tlsca
  cp ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/tls/tlscacerts/* \
    ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/tlsca/tlsca.{{ peer_dir }}-cert.pem

  mkdir -p ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/ca
  cp ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/peers/{{ node_dir }}/msp/cacerts/* \
    ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/ca/ca.{{ peer_dir }}-cert.pem
{%- endfor %}
#############################################################
  mkdir -p organizations/peerOrganizations/{{ peer_dir }}/users

  mkdir -p organizations/peerOrganizations/{{ peer_dir }}/users/Admin@{{ peer_dir }}

  set -x
	fabric-ca-client enroll -u https://{{ peer.orgCA_admin }}:{{ peer.orgCA_pw }}@localhost:{{ peer.CA.port }} \
    --caname ca-{{ peer_nam }} \
    -M ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/users/Admin@{{ peer_dir }}/msp \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ peer_nam }}/tls-cert.pem
  set +x

  cp ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/msp/config.yaml \
    ${PWD}/organizations/peerOrganizations/{{ peer_dir }}/users/Admin@{{ peer_dir }}/msp/config.yaml

}
{%- endfor %}

##########################################################################################################################
##########################################################################################################################
##########################################################################################################################

{%- set orderer_dir = (orderer.orderer_name | lower) ~ '.' ~ (orderer.orderer_domain) %}
{%- set orderer_nam = (orderer.orderer_name | lower) %}

function create{{ orderer.orderer_name }}() {
  mkdir -p organizations/ordererOrganizations/{{ orderer.orderer_domain }}/
  export FABRIC_CA_CLIENT_HOME=${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/
  set -x
  fabric-ca-client enroll \
    -u https://{{ orderer.CA.admin }}:{{ orderer.CA.adminpw }}@localhost:{{ orderer.CA.port }} \
    --caname ca-{{ orderer_nam }} \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ orderer_nam }}Org/tls-cert.pem
  set +x
#############################################################
  echo 'NodeOUs:
  Enable: true
  ClientOUIdentifier:
    Certificate: cacerts/localhost-{{ orderer.CA.port }}-ca-{{ orderer_nam }}.pem
    OrganizationalUnitIdentifier: client
  PeerOUIdentifier:
    Certificate: cacerts/localhost-{{ orderer.CA.port }}-ca-{{ orderer_nam }}.pem
    OrganizationalUnitIdentifier: peer
  AdminOUIdentifier:
    Certificate: cacerts/localhost-{{ orderer.CA.port }}-ca-{{ orderer_nam }}.pem
    OrganizationalUnitIdentifier: admin
  OrdererOUIdentifier:
    Certificate: cacerts/localhost-{{ orderer.CA.port }}-ca-{{ orderer_nam }}.pem
    OrganizationalUnitIdentifier: orderer' > ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/msp/config.yaml
#############################################################
  set -x
  fabric-ca-client register --caname ca-{{ orderer_nam }} \
    --id.name {{ orderer.CAid }} --id.secret {{ orderer.CApw }} --id.type orderer \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ orderer_nam }}Org/tls-cert.pem
  set +x

  set -x
  fabric-ca-client register --caname ca-{{ orderer_nam }} \
    --id.name {{ orderer.orgCA_admin }} --id.secret {{ orderer.orgCA_pw }} --id.type admin \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ orderer_nam }}Org/tls-cert.pem
  set +x
#############################################################
  mkdir -p organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers
  mkdir -p organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer.orderer_domain }}
  mkdir -p organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}

  set -x
  fabric-ca-client enroll -u https://{{ orderer.CAid }}:{{ orderer.CApw }}@localhost:{{ orderer.CA.port }} \
    --caname ca-{{ orderer_nam }} \
    -M ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/msp \
    --csr.hosts {{ orderer_dir }} \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ orderer_nam }}Org/tls-cert.pem
  set +x

  cp ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/msp/config.yaml \
    ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/msp/config.yaml

  set -x
  fabric-ca-client enroll -u https://{{ orderer.CAid }}:{{ orderer.CApw }}@localhost:{{ orderer.CA.port }} \
    --caname ca-{{ orderer_nam }} \
    -M ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls \
    --enrollment.profile tls \
    --csr.hosts {{ orderer_dir }} \
    --csr.hosts localhost \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ orderer_nam }}Org/tls-cert.pem
  set +x
#############################################################
  cp ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls/tlscacerts/* \
    ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls/ca.crt
  cp ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls/signcerts/* \
    ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls/server.crt
  cp ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls/keystore/* \
    ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls/server.key

  mkdir -p ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/msp/tlscacerts
  cp ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls/tlscacerts/* \
    ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/msp/tlscacerts/tlsca.{{ orderer.orderer_domain }}-cert.pem

  mkdir -p ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/msp/tlscacerts
  cp ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/orderers/{{ orderer_dir }}/tls/tlscacerts/* \
    ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/msp/tlscacerts/tlsca.{{ orderer.orderer_domain }}-cert.pem
#############################################################
  mkdir -p organizations/ordererOrganizations/{{ orderer.orderer_domain }}/users

  mkdir -p organizations/ordererOrganizations/{{ orderer.orderer_domain }}/users/Admin@{{ orderer.orderer_domain }}

  set -x
	fabric-ca-client enroll -u https://{{ orderer.orgCA_admin }}:{{ orderer.orgCA_pw }}@localhost:{{ orderer.CA.port }} \
    --caname ca-{{ orderer_nam }} \
    -M ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/users/Admin@{{ orderer.orderer_domain }}/msp \
    --tls.certfiles ${PWD}/organizations/fabric-ca/{{ orderer_nam }}Org/tls-cert.pem
  set +x

  cp ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/msp/config.yaml \
    ${PWD}/organizations/ordererOrganizations/{{ orderer.orderer_domain }}/users/Admin@{{ orderer.orderer_domain }}/msp/config.yaml
}

