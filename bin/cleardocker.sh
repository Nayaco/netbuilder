#/bin/sh
docker stop orderer.example.com peer0.org1.example.com peer0.org2.example.com bold_colden friendly_hoover
docker rm orderer.example.com peer0.org1.example.com peer0.org2.example.com bold_colden friendly_hoover
docker volume rm $(docker volume ls -q)
