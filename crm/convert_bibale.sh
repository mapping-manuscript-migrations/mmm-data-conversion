#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
echo 'Constructing Bibale manuscripts'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bibale_manuscripts.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /tmp/bibale_manuscripts.ttl
echo 'Constructing Bibale places'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bibale_places.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /tmp/bibale_places.ttl
echo 'Constructing Bibale actors'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_bibale_actors.sparql)" $INPUT_BIBALE_SPARQL_ENDPOINT -v > /tmp/bibale_actors.ttl

echo "Inserting data to Fuseki"
cat /tmp/bibale_manuscripts.ttl /tmp/bibale_places.ttl /tmp/bibale_actors.ttl > /tmp/bibale_cidoc.ttl

exec "$@"
