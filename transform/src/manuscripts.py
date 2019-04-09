#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking manuscripts"""

import argparse
import logging

import pandas as pd
from rdflib import URIRef, Literal, RDF
from rdflib.util import guess_format
from typing import Iterable

from linker import redirect_refs
from namespaces import *

log = logging.getLogger(__name__)


def redirect_resource(graph: Graph, old_uri: URIRef, new_uri: URIRef, handle_skos_labels=True):
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
    graph = redirect_resource(graph, old_uri, new_uri)

    graph.add((new_uri, SKOS.prefLabel, new_pref_label))
    graph.remove((new_uri, SKOS.altLabel, new_pref_label))

    return graph


def form_preflabel(labels: Iterable, default: str):
    """
    Form a new prefLabel for a combined manuscript

    >>> form_preflabel(['Christ Church MS. 343', 'SDBM_MS_18044'], 'Linked manuscript')
    rdflib.term.Literal('Christ Church MS. 343; SDBM_MS_18044')
    >>> form_preflabel(['', None], 'Linked manuscript')
    rdflib.term.Literal('Linked manuscript')
    """

    return Literal(('; '.join(str(lbl) for lbl in labels if lbl)) or default)


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

        labels = (bodley.value(old_bod, SKOS.prefLabel) if old_bod else None,
                  bibale.value(old_bib, SKOS.prefLabel) if old_bib else None,
                  sdbm.value(old_sdbm, SKOS.prefLabel) if old_sdbm else None)
        new_pref_label = form_preflabel(labels, 'Harmonized manifestation singleton #%s' % (row.Index + 1))

        log.info('Linking manuscripts %s , %s , %s --> %s (%s)' % (old_bib, old_bod, old_sdbm, new_uri, new_pref_label))

        if old_bib:
            change_manuscript_uri(bibale, old_bib, new_uri, new_pref_label)

        if old_bod:
            change_manuscript_uri(bodley, old_bod, new_uri, new_pref_label)

        if old_sdbm:
            change_manuscript_uri(sdbm, old_sdbm, new_uri, new_pref_label)

    return bibale, bodley, sdbm


def link_phillipps(bibale: Graph, bodley: Graph, sdbm: Graph):
    """
    Link manuscripts by Phillipps numbers
    """
    phillips_manuscripts_bib = {phillips: uri for uri, phillips in bibale[:MMMS.phillipps_number:]}
    phillips_manuscripts_bod = {phillips: uri for uri, phillips in bodley[:MMMS.phillipps_number:]}
    phillips_manuscripts_sdbm = {phillips: uri for uri, phillips in sdbm[:MMMS.phillipps_number:]}

    phillipps_numbers = phillips_manuscripts_bib.keys() | \
                        phillips_manuscripts_bod.keys() | \
                        phillips_manuscripts_sdbm.keys()

    log.info('Got %s Phillipps numbers from Bibale' % len(phillips_manuscripts_bib))
    log.info('Got %s Phillipps numbers from Bodley' % len(phillips_manuscripts_bod))
    log.info('Got %s Phillipps numbers from SDBM' % len(phillips_manuscripts_sdbm))
    log.info('List of known Phillipps numbers: %s' % sorted(phillipps_numbers))

    for number in sorted(phillipps_numbers):
        bib_hit = phillips_manuscripts_bib.get(number)
        bod_hit = phillips_manuscripts_bod.get(number)
        sdbm_hit = phillips_manuscripts_sdbm.get(number)

        if bool(bib_hit) + bool(bod_hit) + bool(sdbm_hit) < 2:
            log.debug('Not enough matches to harmonize manuscripts for Phillipps number %s' % number)
            continue

        new_uri = MMMM['phillipps_' + str(number)]

        labels = (bodley.value(bod_hit, SKOS.prefLabel) if bod_hit else None,
                  bibale.value(bib_hit, SKOS.prefLabel) if bib_hit else None,
                  sdbm.value(sdbm_hit, SKOS.prefLabel) if sdbm_hit else None)

        new_pref_label = form_preflabel(labels, 'Phillipps manuscript #%s' % number)

        log.info(
            'Harmonizing Phillipps manuscript %s: %s , %s , %s --> %s (%s)' %
            (number, bib_hit, bod_hit, sdbm_hit, new_uri, new_pref_label))

        if bib_hit:
            change_manuscript_uri(bibale, bib_hit, new_uri, new_pref_label)

        if bod_hit:
            change_manuscript_uri(bodley, bod_hit, new_uri, new_pref_label)

        if sdbm_hit:
            change_manuscript_uri(sdbm, sdbm_hit, new_uri, new_pref_label)

    return bibale, bodley, sdbm


def main():
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    argparser.add_argument("task", help="Task to perform", choices=['manual_links', 'link_phillipps'])
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
    elif args.task == 'link_phillipps':
        bib, bod, sdbm = link_phillipps(input_bibale, input_bodley, input_sdbm)
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
