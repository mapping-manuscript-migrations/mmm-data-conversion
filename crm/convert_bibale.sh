#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
echo 'Constructing Bibale manuscripts'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bibale_manuscripts.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /tmp/bibale_manuscripts.ttl

echo "Inserting data to Fuseki"
cat /tmp/bibale_manuscripts.ttl  > /tmp/bibale_cidoc.ttl

exec "$@"
