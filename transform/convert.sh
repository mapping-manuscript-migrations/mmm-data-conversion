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
  "skip")
    printf 'Skipping dataset conversions'
  ;;
  *)
    ./convert_bibale.sh
    ./convert_bodley.sh
    ./convert_sdbm.sh
  ;;
esac

printf '\nAdding manual manuscript links and shelfmark links\n\n'
python manuscripts.py all /output/_bibale_linked.ttl /output/_bodley_linked.ttl /output/_sdbm_linked.ttl --input_csv /data/manuscript_links.csv --logfile /output/logs/manuscript_linking.log

printf '\nLinking people\n\n'
python linker_people.py /output/_bibale_linked_all.ttl /output/_bodley_linked_all.ttl /output/_sdbm_linked_all.ttl --logfile /output/logs/person_linking.log

printf '\nSorting triples with rapper\n\n'
rapper -i turtle /output/_bibale_linked_all_people.ttl -o turtle > /output/mmm_bibale.ttl
rapper -i turtle /output/_bodley_linked_all_people.ttl -o turtle > /output/mmm_bodley.ttl
rapper -i turtle /output/_sdbm_linked_all_people.ttl -o turtle > /output/mmm_sdbm.ttl

chmod a+r $OUTPUT/*
