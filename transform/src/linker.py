#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking places to GeoNames and TGN"""

import argparse
import logging
import os
from collections import defaultdict
from decimal import Decimal

from rdflib import Graph, URIRef, Literal, RDF, Namespace, OWL
from rdflib.util import guess_format

from geonames import GeoNamesAPI
from tgn import TGN
from namespaces import *


log = logging.getLogger(__name__)


def generate_place_key(country: str, region: str, settlement: str):
    """
    Generate a key for the place from country, region and settlement

    >>> generate_place_key('Finland  ', 'Uusimaa', '  Espoo')
    ('finland', 'uusimaa', 'espoo')
    """
    return country.lower().strip(), region.lower().strip(), settlement.lower().strip()


def group_places(graph: Graph):
    """Group places into a dict"""
    places = defaultdict(list)

    for place in graph[:RDF.type:CRM.E53_Place]:
        place_country = str(graph.value(place, MMMS.bibale_country, default=''))
        place_region = str(graph.value(place, MMMS.bibale_region, default=''))
        place_settlement = str(graph.value(place, MMMS.bibale_settlement, default=''))
        place_authority_uri = graph.value(place, OWL.sameAs)

        if place_country == '?':
            place_country = ''
        if place_region == '?':
            place_region = ''
        if place_settlement == '?':
            place_settlement = ''

        key = generate_place_key(place_country, place_region, place_settlement)

        places[key].append((place_country, place_region, place_settlement, place, place_authority_uri))

    return places


def redirect_refs(graph: Graph, old_uris: list, new_uri: URIRef):
    """Remove old instances and redirect old URI references to the new URI"""
    for uri in old_uris:
        for s, p in graph.subject_predicates(uri):
            graph.add((s, p, new_uri))

        graph.remove((None, None, uri))
        graph.remove((uri, None, None))

    return graph


def handle_bibale_places(geonames: GeoNamesAPI, tgn: TGN, bibale: Graph):
    """Modify places, link them to GeoNames and TGN, and create a new place ontology"""
    places = group_places(bibale)
    place_ontology = Graph()

    log.info('Got %s places for Bibale place handling.' % len(places))

    for (key, place_data) in places.items():
        # Get most common values (any of them) for place literals and authority URI
        countries, regions, settlements, old_uris, authority_uris = zip(*place_data)

        country = max(set(countries), key=countries.count)
        region = max(set(regions), key=regions.count)
        settlement = max(set(settlements), key=settlements.count)
        authority_uri_set = set(authority_uris) - {None}
        geonames_uri = max(authority_uri_set, key=authority_uris.count) if authority_uri_set else None

        place_label = settlement or region or country
        place_type = bibale.value(old_uris[0], MMMS.place_type)

        # Fetch GeoNames data based on GeoNames id
        geo_match = None
        tgn_match = None
        if geonames_uri:
            geo_match = geonames.get_place_data(str(geonames_uri).split('/')[-1])

        if not geo_match:
            geo_match = geonames.search_place(country, region, settlement)
            if not geo_match and country and region:
                geo_match = geonames.search_place(country, region, '')

        if geo_match:
            place_label = geo_match.get('name') or place_label
            geonames_uri = 'http://sws.geonames.org/%s' % geo_match.get('id')
            tgn_match = tgn.search_tgn_place(place_label, geo_match['lat'], geo_match['lon'])
        else:
            log.error('No GeoNames ID found for %s, %s, %s' % (country, region, settlement))

        if tgn_match:
            uri = tgn.mint_mmm_tgn_uri(tgn_match['uri'])
        else:
            uri = MMMP['bibale_' + str(sorted(old_uris)[0]).split(':')[-1]]

        # Modify graph
        bibale = redirect_refs(bibale, old_uris, uri)

        if geonames_uri:
            place_ontology.add((uri, MMMS.geonames_uri, URIRef(geonames_uri)))
        if country:
            place_ontology.add((uri, MMMS.bibale_country, Literal(country)))
        if region:
            place_ontology.add((uri, MMMS.bibale_region, Literal(region)))
        if settlement:
            place_ontology.add((uri, MMMS.bibale_settlement, Literal(settlement)))

        place_ontology.add((uri, RDF.type, CRM.E53_Place))
        place_ontology.add((uri, MMMS.place_type, place_type))
        place_ontology.add((uri, DCT.source, MMMS.Bibale))
        place_ontology.add((uri, SKOS.prefLabel, Literal(place_label)))

        if tgn_match:
            place_ontology += tgn.place_rdf(uri, tgn_match)
        if geo_match:
            place_ontology.add((uri, MMMS.geonames_lat, Literal(Decimal(geo_match['lat']))))
            place_ontology.add((uri, MMMS.geonames_long, Literal(Decimal(geo_match['lon']))))
            place_ontology.add((uri, MMMS.geonames_class_description, Literal(geo_match['class_description'])))
            if geo_match.get('wikipedia'):
                place_ontology.add((uri, GEO.wikipediaArticle, URIRef(geo_match['wikipedia'])))
            place_ontology.add((uri, GEO.name, Literal(geo_match['address'])))
            place_ontology.add((uri, GEO.parentADM1, Literal(geo_match['adm1'])))
            place_ontology.add((uri, MMMS.geonames_country, Literal(geo_match['country'])))
            place_ontology.add((uri, DCT.source, URIRef('http://www.geonames.org')))

    log.info('Place linking finished.')
    return bibale, place_ontology


def handle_sdbm_places(geonames: GeoNamesAPI, tgn: TGN, sdbm: Graph, places: Graph):
    """Handle SDBM places"""

    for place in sdbm.subjects(RDF.type, CRM.E53_Place):
        data_provider_url = sdbm.value(place, MMMS.data_provider_url)
        place_authority_uri = sdbm.value(place, OWL.sameAs)
        label = sdbm.value(place, SKOS.prefLabel)

        if str(place_authority_uri).startswith('http://vocab.getty.edu/tgn/'):
            mmm_uri = tgn.mint_mmm_tgn_uri(place_authority_uri)

            if not len(list(places.triples((mmm_uri, MMMS.tgn_uri, place_authority_uri)))):
                # Place doesn't exist in place ontology

                tgn_match = tgn.get_place_by_uri(place_authority_uri)
                places += tgn.place_rdf(mmm_uri, tgn_match)
                if str(label) != tgn_match['pref_label']:
                    places.add((mmm_uri, SKOS.altLabel, label))

            places.add((mmm_uri, MMMS.data_provider_url, data_provider_url))
        else:
            mmm_uri = MMMP['sdbm_' + str(place).split('/')[-1]]
            for triple in sdbm.triples((place, None, None)):
                places.add((mmm_uri, triple[1], triple[2]))

        sdbm = redirect_refs(sdbm, [place], mmm_uri)

    return sdbm, places


def main():
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    argparser.add_argument("task", help="Task to perform", choices=['bibale_places', 'sdbm_places'])
    argparser.add_argument("input", help="Input RDF file")
    argparser.add_argument("output", help="Output RDF file")
    argparser.add_argument("--place_ontology", help="Output place ontology RDF file",
                           default="/output/mmm_places.ttl")
    argparser.add_argument("--loglevel", default='INFO', help="Logging level",
                           choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    argparser.add_argument("--logfile", default='tasks.log', help="Logfile")

    args = argparser.parse_args()

    GEONAMES_APIKEYS = [os.environ['GEONAMES_KEY']]
    try:
        GEONAMES_APIKEYS.append(os.environ['GEONAMES_KEY2'])
        GEONAMES_APIKEYS.append(os.environ['GEONAMES_KEY3'])
        GEONAMES_APIKEYS.append(os.environ['GEONAMES_KEY4'])
        GEONAMES_APIKEYS.append(os.environ['GEONAMES_KEY5'])
        GEONAMES_APIKEYS.append(os.environ['GEONAMES_KEY6'])
    except KeyError:
        pass

    geo = GeoNamesAPI(GEONAMES_APIKEYS)
    tgn = TGN()

    log = logging.getLogger()  # Get root logger
    log_handler = logging.FileHandler(args.logfile)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(log_handler)
    log.setLevel(args.loglevel)

    input_graph = Graph()
    input_graph.parse(args.input, format=guess_format(args.input))

    if args.task == 'bibale_places':
        g, place_g = handle_bibale_places(geo, tgn, input_graph)
    elif args.task == 'sdbm_places':
        place_g = Graph()
        place_g.parse(args.place_ontology, format=guess_format(args.place_ontology))
        g, place_g = handle_sdbm_places(geo, tgn, input_graph, place_g)
    else:
        log.error('No valid task given.')
        return

    bind_namespaces(g).serialize(args.output, format=guess_format(args.output))
    bind_namespaces(place_g).serialize(args.place_ontology, format=guess_format(args.place_ontology))


if __name__ == '__main__':
    main()
