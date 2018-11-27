#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
echo 'Constructing Bodley manuscripts'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bod_manuscripts.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /tmp/bodley_manuscripts.ttl

echo "Inserting data to Fuseki"
cat /tmp/bodley_manuscripts.ttl > /tmp/bodley_cidoc.ttl

exec "$@"
