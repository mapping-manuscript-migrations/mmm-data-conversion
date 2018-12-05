#!/bin/bash

set -eo pipefail

# run the SPARQL construct query
printf '\nConstructing SDBM manuscripts\n'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sdbm_manuscripts.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /tmp/sdbm_manuscripts.ttl
printf '\nConstructing SDBM actors\n'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sdbm_people.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /tmp/sdbm_people.ttl
printf '\nConstructing SDBM places\n'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sdbm_places.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /tmp/sdbm_places.ttl
printf '\nConstructing SDBM sources\n'
curl -f --data-urlencode "query=$(cat $FUSEKI_HOME/construct_sdbm_sources.sparql)" $INPUT_SDBM_SPARQL_ENDPOINT -v > /tmp/sdbm_sources.ttl

cat /tmp/sdbm_manuscripts.ttl /tmp/sdbm_people.ttl /tmp/sdbm_places.ttl /tmp/sdbm_sources.ttl > /tmp/sdbm_cidoc.ttl

exec "$@"
