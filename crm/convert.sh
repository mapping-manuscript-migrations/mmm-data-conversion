#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
echo 'Constructing SDBM manuscripts'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_cidoc_crm.sparql)" $INPUT_SPARQL_ENDPOINT -v > /tmp/manuscripts.ttl
echo 'Constructing SDBM actors'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_people.sparql)" $INPUT_SPARQL_ENDPOINT -v > /tmp/people.ttl
echo 'Constructing SDBM places'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_places.sparql)" $INPUT_SPARQL_ENDPOINT -v > /tmp/places.ttl
echo 'Constructing SDBM sources'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sources.sparql)" $INPUT_SPARQL_ENDPOINT -v > /tmp/sources.ttl

echo "Inserting data to Fuseki"
cat /tmp/manuscripts.ttl /tmp/people.ttl /tmp/places.ttl /tmp/sources.ttl > /tmp/cidoc.ttl

# load the result to a new Fuseki
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm-cidoc-crm/ /tmp/cidoc.ttl \
  && $FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm-cidoc-crm/ $FUSEKI_HOME/mmm-schema.ttl \
  && rm /tmp/*

exec "$@"
