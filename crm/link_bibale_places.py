#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking Bibale places"""

import argparse
from collections import defaultdict
import logging

import os

from rdflib import Graph, URIRef, Literal, RDF, Namespace, OWL
from rdflib.util import guess_format

GEONAMES_APIKEY = os.environ['GEONAMES_KEY']

CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
DCT = Namespace('http://purl.org/dc/terms/')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')

MMMS = Namespace('http://ldf.fi/mmm/schema/')
MMMP = Namespace('http://ldf.fi/mmm/places/')

log = logging.getLogger(__name__)


def generate_place_key(country: str, region: str, settlement: str):
    """Generate a key for the place from country, region and settlement"""
    return country.lower().strip(), region.lower().strip(), settlement.lower().strip()


def group_places(graph: Graph):
    """Group places into a dict"""
    places = defaultdict(list)

    for place in graph[:RDF.type:CRM.E53_Place]:
        place_country = str(graph.value(place, MMMS.bibale_country, default=''))
        place_region = str(graph.value(place, MMMS.bibale_region, default=''))
        place_settlement = str(graph.value(place, MMMS.bibale_settlement, default=''))
        place_authority_uri = graph.value(place, OWL.sameAs)

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


def handle_places(graph: Graph):
    """Modify places and create new instances"""
    places = group_places(graph)

    log.info('Got %s places.' % len(places))

    for (key, place_data) in places.items():
        # Get most common values (any of them) for place literals and authority URI
        countries, regions, settlements, place_uris, authority_uris = zip(*place_data)

        country = max(set(countries), key=countries.count)
        region = max(set(regions), key=regions.count)
        settlement = max(set(settlements), key=settlements.count)
        authority_uri_set = set(authority_uris) - {None}
        authority_uri = max(authority_uri_set, key=authority_uris.count) if authority_uri_set else None

        place_type = graph.value(place_uris[0], MMMS.place_type)
        place_label = settlement or region or country

        # Mint new URI
        new_uri = MMMP['bibale_' + str(sorted(place_uris)[0]).split(':')[-1]]

        # Modify graph
        graph = redirect_refs(graph, place_uris, new_uri)

        if authority_uri:
            graph.add((new_uri, OWL.sameAs, authority_uri))
        if country:
            graph.add((new_uri, MMMS.bibale_country, Literal(country)))
        if region:
            graph.add((new_uri, MMMS.bibale_region, Literal(region)))
        if settlement:
            graph.add((new_uri, MMMS.bibale_settlement, Literal(settlement)))

        graph.add((new_uri, RDF.type, CRM.E53_Place))
        graph.add((new_uri, MMMS.place_type, place_type))
        graph.add((new_uri, DCT.source, MMMS.Bibale))
        graph.add((new_uri, SKOS.prefLabel, Literal(place_label)))

    # TODO: Get place coordinates from GeoNames

    return graph


def main():
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    argparser.add_argument("input", help="Input RDF file")
    argparser.add_argument("output", help="Output RDF file")
    argparser.add_argument("--loglevel", default='DEBUG', help="Logging level, default is DEBUG.",
                           choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    argparser.add_argument("--logfile", default='tasks.log', help="Logfile")

    args = argparser.parse_args()

    log = logging.getLogger()  # Get root logger
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(log_handler)
    log.setLevel(args.loglevel)

    input_graph = Graph()
    input_graph.parse(args.input, format=guess_format(args.input))

    handle_places(input_graph).serialize(args.output, format=guess_format(args.output))


if __name__ == '__main__':
    main()
