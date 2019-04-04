#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking manuscripts"""

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


def change_resource_uri(graph: Graph, old_uri: URIRef, new_uri: URIRef, handle_skos_labels=True):
    """Change the URI of a resource, point everything to new URI"""

    log.debug('Redirecting %s to %s' % (old_uri, new_uri))

    for p, o in list(graph.predicate_objects(old_uri)):
        if handle_skos_labels and p == SKOS.prefLabel:
            p = SKOS.altLabel
        graph.add((new_uri, p, o))

    graph = redirect_refs(graph, [old_uri], new_uri)  # Redirect and remove old resource

    return graph


def change_manuscript_uri(graph: Graph, old_uri, new_uri, new_pref_label):
    """
    Change manuscript URI, redirect links and add new prefLabel
    """
    graph = change_resource_uri(graph, old_uri, new_uri)

    graph.add((new_uri, SKOS.prefLabel, new_pref_label))
    graph.remove((new_uri, SKOS.altLabel, new_pref_label))

    return graph


def read_manual_links(bibale: Graph, bodley: Graph, sdbm: Graph, csv):
    """
    Read manuscript links from a CSV file and mash the manuscripts together
    """
    csv_data = pd.read_csv(csv, header=0, keep_default_na=False,
                           names=["bibale", "bodley", "sdbm_record", "sdbm_entry", "notes"])

    for row in csv_data.itertuples(index=True):
        new_uri = MMMM['manually_linked_' + str(row.Index + 1)]
        old_bib = MMMM['bibale_' + row.bibale.rstrip('/').split('/')[-1]] if row.bibale else None
        old_bod = MMMM['bodley_' + row.bodley.rstrip('/').split('/')[-1]] if row.bodley else None

        old_sdbm = None
        if row.sdbm_record:
            resources = sdbm.subjects(MMMS.data_provider_url, URIRef(row.sdbm_record.rstrip('/')))
            resources = [res for res in resources if sdbm.value(res, RDF.type) == FRBR.F4_Manifestation_Singleton]
            if len(resources) != 1:
                log.error('Ambiguous or unknown SDBM manuscript record: %s (%s)' % (row.sdbm_record, len(resources)))
            if resources:
                old_sdbm = resources[0]
        elif row.sdbm_entry:
            resources = sdbm.subjects(MMMS.data_provider_url, URIRef(row.sdbm_entry.rstrip('/')))
            resources = [res for res in resources if sdbm.value(res, RDF.type) == FRBR.F4_Manifestation_Singleton]
            if len(resources) != 1:
                log.error('Ambiguous or unknown SDBM entry record: %s (%s)' % (row.sdbm_entry, len(resources)))
            if resources:
                old_sdbm = resources[0]

        new_pref_label = bodley.value(old_bod, SKOS.prefLabel) or bibale.value(old_bib, SKOS.prefLabel) or \
            sdbm.value(old_sdbm, SKOS.prefLabel) or Literal('Harmonized manifestation singleton #%s' % (row.Index + 1))

        log.info('Linking manuscripts %s , %s , %s --> %s (%s)' % (old_bib, old_bod, old_sdbm, new_uri, new_pref_label))

        if old_bib:
            change_manuscript_uri(bibale, old_bib, new_uri, new_pref_label)

        if old_bod:
            change_manuscript_uri(bodley, old_bod, new_uri, new_pref_label)

        if old_sdbm:
            change_manuscript_uri(sdbm, old_sdbm, new_uri, new_pref_label)

    return bibale, bodley, sdbm


def main():
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    argparser.add_argument("task", help="Task to perform", choices=['manual_links'])
    argparser.add_argument("input_bibale", help="Input Bibale RDF file")
    argparser.add_argument("input_bodley", help="Input Bodley RDF file")
    argparser.add_argument("input_sdbm", help="Input SDBM RDF file")
    argparser.add_argument("--input_csv", help="Input CSV file of manual links")
    argparser.add_argument("--loglevel", default='DEBUG', help="Logging level",
                           choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    argparser.add_argument("--logfile", default='tasks.log', help="Logfile")

    args = argparser.parse_args()

    log = logging.getLogger()  # Get root logger
    log_handler = logging.FileHandler(args.logfile)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(log_handler)
    log.setLevel(args.loglevel)

    log.info('Reading input graphs.')

    input_bibale = Graph()
    input_bibale.parse(args.input_bibale, format=guess_format(args.input_bibale))
    input_bodley = Graph()
    input_bodley.parse(args.input_bodley, format=guess_format(args.input_bodley))
    input_sdbm = Graph()
    input_sdbm.parse(args.input_sdbm, format=guess_format(args.input_sdbm))

    if args.task == 'manual_links':
        bib, bod, sdbm = read_manual_links(input_bibale, input_bodley, input_sdbm, args.input_csv)
    else:
        log.error('No valid task given.')
        return

    log.info('Serializing output files...')

    bind_namespaces(bib).serialize(args.input_bibale, format=guess_format(args.input_bibale))
    bind_namespaces(bod).serialize(args.input_bodley, format=guess_format(args.input_bodley))
    bind_namespaces(sdbm).serialize(args.input_sdbm, format=guess_format(args.input_sdbm))

    log.info('Task finished.')


if __name__ == '__main__':
    main()
