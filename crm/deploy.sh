#!/bin/bash
set -eo pipefail

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bibale/ /output/mmm_bibale.ttl
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-bodley/ /output/mmm_bodley.ttl
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-sdbm/ /output/mmm_sdbm.ttl

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm/places/ /output/mmm_places.ttl

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/schema/mmm/ $FUSEKI_HOME/mmm-schema.ttl
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-cidoc/ $FUSEKI_HOME/mmm-schema.ttl

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/schema/mmm/ $FUSEKI_HOME/cidoc-crm.rdf
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-cidoc/ $FUSEKI_HOME/cidoc-crm.rdf

$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/schema/mmm/ $FUSEKI_HOME/frbroo.rdf
$FUSEKI_HOME/tdbloader --graph=http://ldf.fi/mmm-cidoc/ $FUSEKI_HOME/frbroo.rdf

$FUSEKI_HOME/tdbindexer
