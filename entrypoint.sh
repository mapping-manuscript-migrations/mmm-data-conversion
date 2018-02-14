#!/bin/bash

# wait for input Fuseki to start
sleep 5

# run the SPARQL construct query
echo 'query=' | cat - /tmp/construct_cidoc_crm.sparql | curl -d @- http://input:3030/ds/sparql -v > /tmp/cidoc.ttl

# load the result to a new Fuseki
$TDBLOADER --graph=http://ldf.fi/mmm-sdbm-cidoc-crm/ /tmp/cidoc.ttl \
    && $JAVA_CMD jena.textindexer --desc=$ASSEMBLER \
    && $JAVA_CMD jena.spatialindexer --desc=$ASSEMBLER \
    && $JAVA_CMD tdb.tdbstats --desc=$ASSEMBLER --graph urn:x-arq:UnionGraph > /tmp/stats.opt \
    && mv /tmp/stats.opt /fuseki-base/databases/tdb/ \
    && rm /tmp/*

exec "$@"
