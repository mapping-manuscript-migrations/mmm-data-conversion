#!/bin/bash
set -eo pipefail

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bibale/ /output/bibale_cidoc.ttl
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bodley/ /output/bodley_cidoc.ttl
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm/ /output/sdbm_cidoc.ttl

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm/places/ /output/mmm_places.ttl

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/schema/mmm/ $FUSEKI_HOME/mmm-schema.ttl
$FUSEKI_HOME/tdbindexer

