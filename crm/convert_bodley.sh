#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
echo 'Constructing Bodley manuscripts'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bod_manuscripts.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /tmp/bodley_manuscripts.ttl
echo 'Constructing Bodley people'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bod_people.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /tmp/bodley_people.ttl
echo 'Constructing Bodley places'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bod_places.sparql)" $INPUT_BODLEY_SPARQL_ENDPOINT -v > /tmp/bodley_places.ttl

cat /tmp/bodley_manuscripts.ttl /tmp/bodley_people.ttl /tmp/bodley_places.ttl > /tmp/bodley_cidoc.ttl

exec "$@"
