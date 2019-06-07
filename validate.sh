#!/bin/bash
set -eo pipefail

# run the SPARQL construct query
printf '\nUnknown objects in statements\n\n'
curl -f -H "Accept: text/csv" --data-urlencode "query=$(cat validation/unknown_objects.sparql)" http://localhost:3050/ds/sparql -v > output/validation_unknown_objects.csv

printf '\nMissing skos:prefLabel\n\n'
curl -f -H "Accept: text/csv" --data-urlencode "query=$(cat validation/missing_preflabel.sparql)" http://localhost:3050/ds/sparql -v > output/validation_missing_preflabel.csv

printf '\nMultiple skos:prefLabels\n\n'
curl -f -H "Accept: text/csv" --data-urlencode "query=$(cat validation/multiple_preflabels.sparql)" http://localhost:3050/ds/sparql -v > output/validation_multiple_preflabels.csv

# TODO: Resources missing class annotation

# TODO: Timespan ends before it begins
