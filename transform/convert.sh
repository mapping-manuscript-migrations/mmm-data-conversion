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

printf '\nAdding manual manuscript links\n\n'
python manuscripts.py manual_links output/bibale_cidoc.ttl output/bodley_cidoc.ttl output/sdbm_cidoc.ttl --input_csv /data/manuscript_links.csv --logfile $OUTPUT/logs/manuscript_linking.log

chmod a+r $OUTPUT/*
