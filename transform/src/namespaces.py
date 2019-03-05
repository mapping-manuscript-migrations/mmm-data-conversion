#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""
Define common RDF namespaces
"""
from rdflib import Namespace, Graph

CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
DCT = Namespace('http://purl.org/dc/terms/')
GEO = Namespace('http://www.geonames.org/ontology#')
GVP = Namespace('http://vocab.getty.edu/ontology#')
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
WGS84 = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
FRBR = Namespace('http://erlangen-crm.org/efrbroo/')

MMMS = Namespace('http://ldf.fi/mmm/schema/')
MMMP = Namespace('http://ldf.fi/mmm/place/')
MMMM = Namespace('http://ldf.fi/mmm/manifestation_singleton/')


def bind_namespaces(graph: Graph):
    """Bind common namespaces to the graph"""
    graph.bind("dct", DCT)
    graph.bind("crm", CRM)
    graph.bind("geo", GEO)
    graph.bind("gvp", GVP)
    graph.bind("skos", SKOS)
    graph.bind("wgs84", WGS84)

    graph.bind("mmms", MMMS)
    graph.bind("mmmp", MMMP)

    return graph

