#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking Bibale places"""

import argparse
from collections import defaultdict
import logging

from rdflib import Graph, URIRef, Literal, RDF, Namespace, OWL
from rdflib.util import guess_format

CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
MMMS = Namespace('http://ldf.fi/mmm/schema/')
MMMP = Namespace('http://ldf.fi/mmm/places/')

log = logging.getLogger(__name__)


def generate_place_key(country: str, region: str, settlement: str):
    return country.lower().strip(), region.lower().strip(), settlement.lower().strip()


def group_places(graph: Graph):
    places = defaultdict(list)

    for place in graph[:RDF.type:CRM.E53_Place]:
        place_country = str(graph[place:MMMS.bibale_country])
        place_region = str(graph[place:MMMS.bibale_region])
        place_settlement = str(graph[place:MMMS.bibale_settlement])
        place_authority_uri = graph[place:OWL.sameAs]

        key = generate_place_key(place_country, place_region, place_settlement)

        places[key].append((place_country, place_region, place_settlement, place, place_authority_uri))

    return places


def handle_places(graph: Graph):
    places = group_places(graph)

    for (place, place_data) in places.items():
        # TODO: Get most common values for place_data parts
        log.debug(place)

    # TODO: Mint new URI for the linked place

    # TODO: Point references to old places to new URIs

    # TODO: Remove old place instances

    # TODO: Create new place instances for linked places

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
