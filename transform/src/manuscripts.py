#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking manuscripts"""

import argparse
import logging

import pandas as pd
from rdflib import URIRef, Literal, RDF, OWL
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


def change_resource_uri(graph: Graph, old_uri, new_uri, new_pref_label: Literal, add_sameas: bool=True):
    """
    Change resource URI, redirect links and add new prefLabel
    """
    if old_uri == new_uri:
        return graph

    triples = len(list(graph.predicate_objects(old_uri)))
    if triples <= 1:
        log.warning('Redirecting URI used as subject in only {num} triples: {uri}'.format(num=triples, uri=old_uri))

    graph = redirect_resource(graph, old_uri, new_uri)

    if new_pref_label:
        graph.add((new_uri, SKOS.prefLabel, new_pref_label))
        graph.remove((new_uri, SKOS.altLabel, new_pref_label))

    if add_sameas:
        graph.add((old_uri, OWL.sameAs, new_uri))

    return graph


def form_preflabel(labels: Iterable, default: str):
    """
    Get first existing label from a list of labels or use default

    >>> form_preflabel(['Christ Church MS. 343', 'SDBM_MS_18044'], 'Linked manuscript')
    rdflib.term.Literal('Christ Church MS. 343')
    >>> form_preflabel(['', None], 'Linked manuscript')
    rdflib.term.Literal('Linked manuscript')
    """
    return Literal(next((lbl for lbl in labels if lbl), default))


def link_manuscripts(bibale: Graph, bodley: Graph, sdbm: Graph, links: list):
    """
    Link manuscripts based on a list of tuples containing matches
    """
    links = sorted(set(links))

    log.info('Got {num} links for manuscript linking'.format(num=len(links)))

    for (bib_hit, bod_hit, sdbm_hit) in links:

        # Redirect based on created owl:sameAs links if found
        bib_hit = bibale.value(bib_hit, OWL.sameAs, any=False) or bib_hit
        bod_hit = bodley.value(bod_hit, OWL.sameAs, any=False) or bod_hit
        sdbm_hit = sdbm.value(sdbm_hit, OWL.sameAs, any=False) or sdbm_hit

        new_uri = bod_hit or bib_hit or sdbm_hit

        labels = (bibale.value(bib_hit, SKOS.prefLabel) if bib_hit else None,
                  bodley.value(bod_hit, SKOS.prefLabel) if bod_hit else None,
                  sdbm.value(sdbm_hit, SKOS.prefLabel) if sdbm_hit else None)

        new_pref_label = form_preflabel(labels, 'Harmonized manuscript')

        log.info(
            'Harmonizing manuscript {bib} , {bod} , {sdbm} --> {new_uri} {label}'.
                format(bib=bib_hit, bod=bod_hit, sdbm=sdbm_hit, new_uri=new_uri, label=new_pref_label))

        if bib_hit:
            change_resource_uri(bibale, bib_hit, new_uri, new_pref_label)

        if bod_hit:
            change_resource_uri(bodley, bod_hit, new_uri, new_pref_label)

        if sdbm_hit:
            change_resource_uri(sdbm, sdbm_hit, new_uri, new_pref_label)

    return bibale, bodley, sdbm


def read_manual_links(bibale: Graph, bodley: Graph, sdbm: Graph, csv):
    """
    Read manuscript links from a CSV file
    """
    csv_data = pd.read_csv(csv, header=0, keep_default_na=False,
                           names=["bibale", "bodley", "sdbm_record", "sdbm_entry", "notes"])

    links = []

    for row in csv_data.itertuples(index=True):
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

        links.append((old_bib, old_bod, old_sdbm))

    log.info('Found {num} manual manuscript links'.format(num=len(links)))

    return links


def link_by_shelfmark(bibale: Graph, bodley: Graph, sdbm: Graph, prop: URIRef, name: str):
    """
    Find manuscript links using shelfmark numbers
    """
    log.info('Finding manuscript links by {name} shelfmark/number ({prop})'.format(name=name, prop=prop))
    manuscripts_bib = {shelfmark: uri for uri, shelfmark in bibale[:prop:]}
    manuscripts_bod = {shelfmark: uri for uri, shelfmark in bodley[:prop:]}
    manuscripts_sdbm = {shelfmark: uri for uri, shelfmark in sdbm[:prop:]}

    shelfmark_numbers = manuscripts_bib.keys() | \
                        manuscripts_bod.keys() | \
                        manuscripts_sdbm.keys()

    log.info('Got {num} {name} numbers from Bibale'.format(name=name, num=len(manuscripts_bib)))
    log.info('Got {num} {name} numbers from Bodley'.format(name=name, num=len(manuscripts_bod)))
    log.info('Got {num} {name} numbers from SDBM'.format(name=name, num=len(manuscripts_sdbm)))

    links = []

    for number in sorted(shelfmark_numbers):
        bib_hit = manuscripts_bib.get(number)
        bod_hit = manuscripts_bod.get(number)
        sdbm_hit = manuscripts_sdbm.get(number)

        if bool(bib_hit) + bool(bod_hit) + bool(sdbm_hit) < 2:
            log.debug('Not enough matches to harmonize {name} number {num}'.format(name=name, num=number))
            continue

        links.append((bib_hit, bod_hit, sdbm_hit))

    log.info('Found {num} manuscript links for {name} shelfmark/number'.format(num=len(links), name=name))

    return links


def main():
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    argparser.add_argument("task", help="Task to perform", choices=['manual_links', 'link_shelfmark', 'all'])
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

    bibale = Graph()
    bibale.parse(args.input_bibale, format=guess_format(args.input_bibale))
    bodley = Graph()
    bodley.parse(args.input_bodley, format=guess_format(args.input_bodley))
    sdbm = Graph()
    sdbm.parse(args.input_sdbm, format=guess_format(args.input_sdbm))
    links = []

    if args.task in ['manual_links', 'all']:
        log.info('Adding manual manuscript links')
        links += read_manual_links(bibale, bodley, sdbm, args.input_csv)

    if args.task in ['link_shelfmark', 'all']:
        log.info('Finding manuscript links by shelfmark numbers')

        links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.phillipps_number, "Phillipps")
        links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_buchanan, "Buchanan")
        links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_bnf_latin, "BNF Latin")
        links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_bnf_hebreu, "BNF Hébreu")
        links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_bnf_nal, "BNF NAL")
        links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_arsenal, "Arsenal")
        links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_christ_church, "Christ Church")
        links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_barocci, "Barocci")

    if links:
        log.info('Linking manuscripts using found links')

        bibale, bodley, sdbm = link_manuscripts(bibale, bodley, sdbm, links)

        log.info('Serializing output files...')

        filename_suffix = '_' + args.task + '.ttl'
        bind_namespaces(bibale).serialize(args.input_bibale.split('.')[0] + filename_suffix, format='turtle')
        bind_namespaces(bodley).serialize(args.input_bodley.split('.')[0] + filename_suffix, format='turtle')
        bind_namespaces(sdbm).serialize(args.input_sdbm.split('.')[0] + filename_suffix, format='turtle')
    else:
        log.warning('No links found')

    log.info('Task finished.')


if __name__ == '__main__':
    main()
