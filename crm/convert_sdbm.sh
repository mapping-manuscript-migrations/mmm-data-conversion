#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
echo 'Constructing SDBM manuscripts'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sdbm_manuscripts.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /tmp/sdbm_manuscripts.ttl
echo 'Constructing SDBM actors'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sdbm_people.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /tmp/sdbm_people.ttl
echo 'Constructing SDBM places'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sdbm_places.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /tmp/sdbm_places.ttl
echo 'Constructing SDBM sources'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sdbm_sources.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /tmp/sdbm_sources.ttl

cat /tmp/sdbm_manuscripts.ttl /tmp/sdbm_people.ttl /tmp/sdbm_places.ttl /tmp/sdbm_sources.ttl > /tmp/sdbm_cidoc.ttl

exec "$@"
