CHANNEL_NAME="{{ channel.channel_name }}"

CC_NAME={{ chaincode.cc_name }}
CC_SRC_PATH={{ chaincode.cc_name }}
CC_SRC_LANGUAGE={{ chaincode.cc_lang }}
CC_VERSION={{ chaincode.cc_version }}
CC_SEQUENCE={{ chaincode.cc_seq }}
CC_INIT_FCN={{ chaincode.init_func }}
CC_END_POLICY={{ chaincode.sig_policy }}
CC_COLL_CONFIG={{ chaincode.col_config }}

CC_PEERS=({% for org in chaincode.endorse_peers %}{{ org }} {% endfor %})
CC_PEER
DELAY=$1
MAX_RETRY=$2
VERBOSE=$3

CC_READINESS_TEXT=()

for org in ${CC_PEERS[@]}; do

: ${DELAY:="3"}
: ${MAX_RETRY:="3"}
: ${VERBOSE:="false"}

if [ "$CC_SRC_LANGUAGE" = "go" ]; then
  CC_RUNTIME_LANGUAGE=golang
	pushd $CC_SRC_PATH
	GO111MODULE=on 
  go mod vendor
	popd
elif [ "$CC_SRC_LANGUAGE" = "java" ]; then
  CC_RUNTIME_LANGUAGE=java
  pushd $CC_SRC_PATH
  ./gradlew installDist
  popd
  CC_SRC_PATH=$CC_SRC_PATH/build/install/$CC_NAME
elif [ "$CC_SRC_LANGUAGE" = "javascript" ]; then
  CC_RUNTIME_LANGUAGE=node
elif [ "$CC_SRC_LANGUAGE" = "typescript" ]; then
  CC_RUNTIME_LANGUAGE=node
  pushd $CC_SRC_PATH
  npm install
  npm run build
  popd
else
  exit 1
fi

INIT_REQUIRED="--init-required"
if [ "$CC_INIT_FCN" = "NA" ]; then
  INIT_REQUIRED=""
fi
if [ "$CC_END_POLICY" = "NA" ]; then
  CC_END_POLICY=""
else
  CC_END_POLICY="--signature-policy $CC_END_POLICY"
fi
if [ "$CC_COLL_CONFIG" = "NA" ]; then
  CC_COLL_CONFIG=""
else
  CC_COLL_CONFIG="--collections-config $CC_COLL_CONFIG"
fi

. scripts/envVar.sh

packageChaincode() {
  ORG=$1
  PEER=$2
  setGlobals $ORG $PEER
  set -x
  peer lifecycle chaincode package ${CC_NAME}.tar.gz \
    --path ${CC_SRC_PATH} --lang ${CC_RUNTIME_LANGUAGE} \
    --label ${CC_NAME}_${CC_VERSION} >&log.txt
  res=$?
  set +x
  cat log.txt
}

installChaincode() {
  ORG=$1
  PEER=$2
  setGlobals $ORG $PEER
  set -x
  peer lifecycle chaincode install \
    ${CC_NAME}.tar.gz >&log.txt
  res=$?
  set +x
  cat log.txt
}

queryInstalled() {
  ORG=$1
  PEER=$2
  setGlobals $ORG $PEER
  set -x
  peer lifecycle chaincode queryinstalled >&log.txt
  res=$?
  set +x
  cat log.txt
  PACKAGE_ID=$(sed -n "/${CC_NAME}_${CC_VERSION}/{s/^Package ID: //; s/, Label:.*$//; p;}" log.txt)
}

approveForMyOrg() {
  ORG=$1
  PEER=$2
  setGlobals $ORG $PEER
  set -x
  # TODO: add real availiable orderer address on ethernet
  peer lifecycle chaincode approveformyorg \
    -o localhost:{{ orderer.port }} \
    --ordererTLSHostnameOverride {{ orderer.orderer_name | lower }}.{{ orderer.orderer_domain }} \
    --tls --cafile $ORDERER_CA \
    --channelID $CHANNEL_NAME \
    --name ${CC_NAME} --version ${CC_VERSION} \
    --package-id ${PACKAGE_ID} \
    --sequence ${CC_SEQUENCE} ${INIT_REQUIRED} ${CC_END_POLICY} ${CC_COLL_CONFIG} >&log.txt
  set +x
  cat log.txt
}

checkCommitReadiness() {
  ORG=$1
  PEER=$2
  setGlobals $ORG $PEER
  local rc=1
  local COUNTER=1
  while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ]; do
    sleep $DELAY
    set -x
    peer lifecycle chaincode checkcommitreadiness \
      --channelID $CHANNEL_NAME \
      --name ${CC_NAME} --version ${CC_VERSION} \
      --sequence ${CC_SEQUENCE} ${INIT_REQUIRED} ${CC_END_POLICY} ${CC_COLL_CONFIG} --output json >&log.txt
    res=$?
    set +x
    let rc=0
    for var in "$@"; do
      grep "$var" log.txt &>/dev/null || let rc=1
    done
    COUNTER=$(expr $COUNTER + 1)
  done
  cat log.txt
}

commitChaincodeDefinition() {
	set -x
	peer lifecycle chaincode commit \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --tls --cafile $ORDERER_CA \
    --channelID $CHANNEL_NAME \
    --name ${CC_NAME} $PEER_CONN_PARMS --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} ${INIT_REQUIRED} ${CC_END_POLICY} ${CC_COLL_CONFIG} >&log.txt
	res=$?
	set +x
	cat log.txt
}

# queryCommitted ORG
queryCommitted() {
  ORG=$1
  PEER=$2
  setGlobals $ORG $PEER
	EXPECTED_RESULT="Version: ${CC_VERSION}, Sequence: ${CC_SEQUENCE}, Endorsement Plugin: escc, Validation Plugin: vscc"
	local rc=1
	local COUNTER=1

	while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ]; do
		sleep $DELAY
		set -x
		peer lifecycle chaincode querycommitted --channelID $CHANNEL_NAME --name ${CC_NAME} >&log.txt
		res=$?
		set +x
		test $res -eq 0 && VALUE=$(cat log.txt | grep -o '^Version: '$CC_VERSION', Sequence: [0-9]*, Endorsement Plugin: escc, Validation Plugin: vscc')
		test "$VALUE" = "$EXPECTED_RESULT" && let rc=0
		COUNTER=$(expr $COUNTER + 1)
	done
	cat log.txt
}

chaincodeInvokeInit() {
	set -x
	fcn_call='{"function":"'${CC_INIT_FCN}'","Args":[]}'
	peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile $ORDERER_CA -C $CHANNEL_NAME -n ${CC_NAME} $PEER_CONN_PARMS --isInit -c ${fcn_call} >&log.txt
	res=$?
	set +x
	cat log.txt
}

# chaincodeQuery() {
#   ORG=$1
#   PEER=$2
#   setGlobals $ORG $PEER
#   local rc=1
#   local COUNTER=1
#   # continue to poll
#   # we either get a successful response, or reach MAX RETRY
#   while [ $rc -ne 0 -a $COUNTER -lt $MAX_RETRY ]; do
#     sleep $DELAY
#     set -x
#     peer chaincode query -C $CHANNEL_NAME -n ${CC_NAME} -c '{"Args":["queryAllCars"]}' >&log.txt
#     res=$?
#     set +x
#     let rc=$res
#     COUNTER=$(expr $COUNTER + 1)
#   done
#   cat log.txt
# }


packageChaincode 1

echo "Installing chaincode on peer0.org1..."
installChaincode 1
echo "Install chaincode on peer0.org2..."
installChaincode 2

## query whether the chaincode is installed
queryInstalled 1

## approve the definition for org1
approveForMyOrg 1

## check whether the chaincode definition is ready to be committed
## expect org1 to have approved and org2 not to
checkCommitReadiness 1 "\"Org1MSP\": true" "\"Org2MSP\": false"
checkCommitReadiness 2 "\"Org1MSP\": true" "\"Org2MSP\": false"

## now approve also for org2
approveForMyOrg 2

## check whether the chaincode definition is ready to be committed
## expect them both to have approved
checkCommitReadiness 1 "\"Org1MSP\": true" "\"Org2MSP\": true"
checkCommitReadiness 2 "\"Org1MSP\": true" "\"Org2MSP\": true"

## now that we know for sure both orgs have approved, commit the definition
commitChaincodeDefinition 1 2

## query on both orgs to see that the definition committed successfully
queryCommitted 1
queryCommitted 2

## Invoke the chaincode - this does require that the chaincode have the 'initLedger'
## method defined
if [ "$CC_INIT_FCN" = "NA" ]; then
	echo "===================== Chaincode initialization is not required ===================== "
	echo
else
	chaincodeInvokeInit 1 2
fi

exit 0
