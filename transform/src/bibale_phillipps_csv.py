#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Convert Bibale Phillipps CSV"""

import argparse
import logging
import os
from collections import defaultdict
from decimal import Decimal
from itertools import chain

import pandas as pd
from rdflib import URIRef, Literal, RDF, OWL
from rdflib.util import guess_format

from geonames import GeoNames
from linker import redirect_refs
from namespaces import *
from tgn import TGN

log = logging.getLogger(__name__)


def read_csv(csv):
    csv_data = pd.read_csv(csv, header=0, keep_default_na=False,
                           names=["bibale", "phillipps", "notes"])

    g = Graph()

    for row in csv_data.itertuples(index=True):
        new_uri = MMMM['bibale_' + row.bibale.split('/')[-1]]
        for phillipp in str(row.phillipps).split(';'):
            g.add((URIRef(new_uri), MMMS.phillipps_number, Literal(phillipp.strip())))
            g.add((URIRef(new_uri), CRM.P46i_forms_part_of, URIRef('http://ldf.fi/mmm/collection/bibale_8500')))
        if row.notes:
            g.add((URIRef(new_uri), CRM.P3_has_note, Literal(row.notes)))

    return g


def main():
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    argparser.add_argument("input_csv", help="Input CSV file of manual links")
    argparser.add_argument("output", help="OutputRDF file")
    argparser.add_argument("--loglevel", default='DEBUG', help="Logging level",
                           choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    argparser.add_argument("--logfile", default='tasks.log', help="Logfile")

    args = argparser.parse_args()

    log = logging.getLogger()  # Get root logger
    log_handler = logging.FileHandler(args.logfile)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(log_handler)
    log.setLevel(args.loglevel)

    graph = read_csv(args.input_csv)

    log.info('Serializing output...')

    bind_namespaces(graph).serialize(args.output, format=guess_format(args.output))

    log.info('Task finished.')


if __name__ == '__main__':
    main()
