#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_cidoc_crm.sparql)" $INPUT_SPARQL_ENDPOINT -v > /tmp/manuscripts.ttl
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_people.sparql)" $INPUT_SPARQL_ENDPOINT -v > /tmp/people.ttl
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_places.sparql)" $INPUT_SPARQL_ENDPOINT -v > /tmp/places.ttl

cat /tmp/manuscripts.ttl /tmp/people.ttl /tmp/places.ttl > /tmp/cidoc.ttl

# load the result to a new Fuseki
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm-cidoc-crm/ /tmp/cidoc.ttl \
  && $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm-cidoc-crm/ $FUSEKI_HOME/mmm-schema.ttl \
  && rm /tmp/*

exec "$@"
