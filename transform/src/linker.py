#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking tasks"""

import argparse
import logging
import re
from itertools import chain
from operator import itemgetter
from typing import Iterable, DefaultDict

import os
import pandas as pd
from rdflib import URIRef, Literal, RDF, OWL
from rdflib.util import guess_format

from linker_places import PlaceLinker
from linker_works import WorkLinker
from mmm import change_resource_uri
from namespaces import *

log = logging.getLogger(__name__)


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


def read_manuscript_links(bibale: Graph, bodley: Graph, sdbm: Graph, csv):
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


def get_last_known_locations(bibale: Graph, bodley: Graph, sdbm: Graph, place_linker,
                             csv='/data/bibale_locations.csv'):
    """
    Estimate last known location for each manuscripts based on the datasets
    """

    # BODLEIAN

    for manuscript in bodley.subjects(RDF.type, FRBR.F4_Manifestation_Singleton):
        bodley.add((manuscript, MMMS.last_known_location_bodley, MMMP.tgn_7011931))

    # BIBALE

    csv_data = pd.read_csv(csv, header=0, keep_default_na=False, names=["pays", "ville_id", "ville", "geonames_id"])

    cities = DefaultDict(dict)
    for row in csv_data.itertuples(index=True):
        city = str(row.ville).strip().lower()
        geonames_id = str(row.geonames_id).strip()
        if not geonames_id:
            continue

        cities[city]['geonames'] = geonames_id
        cities[city]['country'] = str(row.pays).strip().lower()

        log.debug('Got a Bibale shelfmark city link for %s: %s' % (city, geonames_id))

    for manuscript in bibale.subjects(RDF.type, FRBR.F4_Manifestation_Singleton):
        label = str(bibale.value(manuscript, SKOS.prefLabel))
        shelfmark_city = label.split(',')[0].strip().lower() if ',' in label else None

        tgn_uri = cities.get(shelfmark_city, {}).get('tgn')
        geonames_uri = cities.get(shelfmark_city, {}).get('geonames')
        country = cities.get(shelfmark_city, {}).get('country')

        log.info('City %s, country %s, TGN %s, GeoNames %s' % (shelfmark_city, country, tgn_uri, geonames_uri))

        if not tgn_uri:
            if geonames_uri:
                log.debug('Matching to TGN with GeoNames URI %s' % geonames_uri)
                tgn_match, geo_match = place_linker.link_geonames_place_to_tgn(geonames_uri)
            else:
                log.info('Matching to TGN with place name %s, %s' % (country, shelfmark_city))
                tgn_match, geo_match = place_linker.link_geonames_place_to_tgn(
                    country=country, settlement=shelfmark_city)

            if tgn_match and tgn_match['uri']:
                tgn_uri = place_linker.tgn.mint_mmm_tgn_uri(tgn_match['uri'])
                cities[shelfmark_city]['tgn'] = tgn_uri
            else:
                log.warning('No TGN match for %s (%s)' % (shelfmark_city, geonames_uri))

        if tgn_uri:
            log.info('Adding manuscript %s last known location %s' % (manuscript, tgn_uri))
            bibale.add((manuscript, MMMS.last_known_location_bibale, URIRef(tgn_uri)))

    # SDBM

    for manuscript in sdbm.subjects(RDF.type, FRBR.F4_Manifestation_Singleton):

        # TODO: Create tuples (location, date) and order by date and pick all with the most recent date. date = end_of_end or begin_of_begin (plus other 2)

        sources = chain(sdbm.objects(manuscript, CRM.P46i_forms_part_of),
                        sdbm.objects(manuscript, CRM.P70i_is_documented_in))

        # events = chain(sdbm.subjects(CRM.P30_transferred_custody_of, manuscript),
        #                sdbm.subjects(MMMS.observed_manuscript, manuscript))

        valid_undated_places = []
        valid_date_places = []

        for source in sources:
            actors = chain(sdbm.objects(source, CRM.P51_has_former_or_current_owner),
                           sdbm.objects(source, MMMS.source_agent))

            source_timespan = sdbm.value(source, MMMS.source_date)
            source_time_begin = sdbm.value(source_timespan, CRM.P82a_begin_of_the_begin)
            source_time_end = sdbm.value(source_timespan, CRM.P82b_end_of_the_end)

            log.debug('SDBM source %s times %s - %s' % (source, source_time_begin, source_time_end))

            # Get location from actors place/nationality events
            for actor in actors:
                events = sdbm.subjects(CRM.P11_had_participant, actor)
                for event in events:
                    if not sdbm.triples((event, RDF.type, MMMS.PlaceNationality)):
                        continue

                    event_timespan = sdbm.value(event, CRM['P4_has_time-span'])
                    event_time_begin = sdbm.value(event_timespan, CRM.P82a_begin_of_the_begin)
                    event_time_end = sdbm.value(event_timespan, CRM.P82b_end_of_the_end)

                    log.debug('SDBM domicile event %s times %s - %s' % (event, event_time_begin, event_time_end))

                    if ((source_time_begin and event_time_begin) and (source_time_begin < event_time_begin)) or \
                            ((source_time_begin and event_time_begin) and (source_time_end > event_time_end)):
                        continue

                    place_triples = sdbm.triples((event, CRM.P7_took_place_at, None))
                    for (_, _, place) in place_triples:
                        source_date = event_time_end or source_time_end or event_time_begin or source_time_begin or None
                        if source_date:
                            valid_date_places.append((place, source_date))
                        else:
                            valid_undated_places.append(place)

        log.info('SDBM last known locations for %s are %s' % (manuscript, valid_undated_places + valid_date_places))
        if valid_date_places:
            place = sorted(valid_date_places, key=itemgetter(1), reverse=True)[0][0]
            sdbm.add((manuscript, MMMS.last_known_location_sdbm, URIRef(place)))
        else:
            for place in valid_undated_places:
                sdbm.add((manuscript, MMMS.last_known_location_sdbm, URIRef(place)))

    # Get a last known location with a priority list

    manuscripts = set(chain(bodley.subjects(RDF.type, FRBR.F4_Manifestation_Singleton),
                            bibale.subjects(RDF.type, FRBR.F4_Manifestation_Singleton),
                            sdbm.subjects(RDF.type, FRBR.F4_Manifestation_Singleton)))

    for manu in manuscripts:
        location = bodley.value(manu, MMMS.last_known_location_bodley, any=False) or \
                   bibale.value(manu, MMMS.last_known_location_bibale, any=False) or \
                   sdbm.value(manu, MMMS.last_known_location_sdbm)  # NOTE: Can contain multiple values, now picking one

        if location:
            sdbm.add((manu, MMMS.last_known_location, location))  # Note: Adding all to SDBM graph
            log.debug('Manuscript %s last known location is %s' % (manu, location))
        else:
            log.warning('No last known location for %s' % manu)

    return bibale, bodley, sdbm


def annotate_decades(bibale: Graph, bodley: Graph, sdbm: Graph):
    for g in [bibale, bodley, sdbm]:
        for sub in g.subjects(RDF.type, CRM['E52_Time-Span']):

            # TODO: If time-span is open-ended, assume 100 years as the maximum length, add this to data

            # TODO: decades_start = begin_begin or begin_end
            # TODO: decades_end = end_end or end_begin

            # TODO: Loop over decades from start to end (YYY_), annotate each to time-span
            pass

    return bibale, bodley, sdbm


def main():
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    # argparser.add_argument("task", help="Task to perform", choices=['manual_links', 'link_shelfmark', 'all'])
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
    manuscript_links = []

    log.info('Adding manual manuscript links')
    manuscript_links += read_manuscript_links(bibale, bodley, sdbm, args.input_csv)

    log.info('Finding manuscript links by shelfmark numbers')
    manuscript_links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.phillipps_number, "Phillipps")
    manuscript_links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_buchanan, "Buchanan")
    manuscript_links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_bnf_latin, "BNF Latin")
    manuscript_links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_bnf_hebreu, "BNF Hébreu")
    manuscript_links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_bnf_nal, "BNF NAL")
    manuscript_links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_arsenal, "Arsenal")
    manuscript_links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_christ_church, "Christ Church")
    manuscript_links += link_by_shelfmark(bibale, bodley, sdbm, MMMS.shelfmark_barocci, "Barocci")

    if manuscript_links:
        log.info('Linking manuscripts using found links')

        bibale, bodley, sdbm = link_manuscripts(bibale, bodley, sdbm, manuscript_links)
    else:
        log.warning('No manuscript links found')

    log.info('Adding manual work links')
    work_linker = WorkLinker(sdbm, bodley, bibale)
    work_linker.get_recon_links()
    work_linker.link_works()

    log.info('Getting last known locations')

    geonames_apikeys = [os.environ['GEONAMES_KEY']]
    try:
        geonames_apikeys.append(os.environ['GEONAMES_KEY2'])
        geonames_apikeys.append(os.environ['GEONAMES_KEY3'])
        geonames_apikeys.append(os.environ['GEONAMES_KEY4'])
        geonames_apikeys.append(os.environ['GEONAMES_KEY5'])
        geonames_apikeys.append(os.environ['GEONAMES_KEY6'])
    except KeyError:
        pass

    linker = PlaceLinker(geonames_apikeys)
    bibale, bodley, sdbm = get_last_known_locations(bibale, bodley, sdbm, linker)

    log.info('Improving time-spans and annotating decades')

    bibale, bodley, sdbm = annotate_decades(bibale, bodley, sdbm)

    log.info('Serializing output files...')
    filename_suffix = '_all.ttl'
    bind_namespaces(bibale).serialize(args.input_bibale.split('.')[0] + filename_suffix, format='turtle')
    bind_namespaces(bodley).serialize(args.input_bodley.split('.')[0] + filename_suffix, format='turtle')
    bind_namespaces(sdbm).serialize(args.input_sdbm.split('.')[0] + filename_suffix, format='turtle')

    log.info('Task finished.')


if __name__ == '__main__':
    main()
