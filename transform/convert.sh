#!/bin/bash
set -eo pipefail

mkdir -p $OUTPUT/logs

case "$1" in
  "bibale")
    ./convert_bibale.sh
  ;;
  "bodley")
    ./convert_bodley.sh
  ;;
  "sdbm")
    ./convert_sdbm.sh
  ;;
  *)
    ./convert_bibale.sh
    ./convert_bodley.sh
    ./convert_sdbm.sh
  ;;
esac

printf '\nAdding manual manuscript links and shelfmark links\n\n'
python manuscripts.py all /output/_bibale_linked.ttl /output/_bodley_linked.ttl /output/_sdbm_linked.ttl --input_csv /data/manuscript_links.csv --logfile /output/logs/manuscript_linking.log

printf '\nSorting triples with rapper\n\n'
rapper -i turtle /output/_bibale_linked_all.ttl -o turtle > /output/bibale_cidoc.ttl
rapper -i turtle /output/_bodley_linked_all.ttl -o turtle > /output/bodley_cidoc.ttl
rapper -i turtle /output/_sdbm_linked_all.ttl -o turtle > /output/sdbm_cidoc.ttl

chmod a+r $OUTPUT/*
