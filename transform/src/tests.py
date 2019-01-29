#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking places to GeoNames and TGN"""

import argparse
import logging
import os
import pprint
from collections import defaultdict
from decimal import Decimal
import unittest

import copy
from rdflib import Graph, URIRef, Literal, RDF, Namespace, OWL
from rdflib.compare import graph_diff
from rdflib.util import guess_format

from geonames import GeoNamesAPI
from linker import handle_sdbm_places
from tgn import TGN
from namespaces import *


class TestLinker(unittest.TestCase):

    test_sdbm_data = """
    @prefix :      <https://sdbm.library.upenn.edu/> .
    @prefix wgs:   <http://www.w3.org/2003/01/geo/wgs84_pos#> .
    @prefix mmm-schema: <http://ldf.fi/mmm/schema/> .
    @prefix dct:   <http://purl.org/dc/terms/> .
    @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix owl:   <http://www.w3.org/2002/07/owl#> .
    @prefix afn:   <http://jena.hpl.hp.com/ARQ/function#> .
    @prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
    @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix mmm:   <http://ldf.fi/mmm/> .
    @prefix crm:   <http://www.cidoc-crm.org/cidoc-crm/> .
    @prefix frbroo: <http://erlangen-crm.org/efrbroo/> .
    
    <http://ldf.fi/mmm/production/orphan_61316>
        a                      crm:E12_Production ;
        dct:source             mmm-schema:SDBM ;
        crm:P108_has_produced  <http://ldf.fi/mmm/manifestation_singleton/orphan_61316> ;
        crm:P4_has_time-span   <http://ldf.fi/mmm/timespan/59403> ;
        crm:P7_took_place_at   <http://ldf.fi/mmm/places/2121> .

    <http://ldf.fi/mmm/places/2121>
            a                             crm:E53_Place ;
            mmm-schema:data_provider_url  <https://sdbm.library.upenn.edu/places/2121> ;
            dct:source                    mmm-schema:SDBM ;
            crm:P89_falls_within          <http://ldf.fi/mmm/places/214> ;
            owl:sameAs                    <http://vocab.getty.edu/tgn/1005755> ;
            wgs:lat                       51.5833 ;
            wgs:long                      -0.0833 ;
            skos:prefLabel                "Tottenham" .

    <http://ldf.fi/mmm/places/1012>
            a                             crm:E53_Place ;
            mmm-schema:data_provider_url  <https://sdbm.library.upenn.edu/places/1012> ;
            dct:source                    mmm-schema:SDBM ;
            crm:P89_falls_within          <http://ldf.fi/mmm/places/3991> ;
            owl:sameAs                    <http://vocab.getty.edu/tgn/7005560> ;
            wgs:lat                       "23"^^<http://www.w3.org/2001/XMLSchema#decimal> ;
            wgs:long                      "-102"^^<http://www.w3.org/2001/XMLSchema#decimal> ;
            skos:prefLabel                "Mexico" .
    """

    def test_handle_sdbm_places(self):
        place1 = URIRef('http://ldf.fi/mmm/places/2121')

        g = Graph()
        g.parse(data=self.test_sdbm_data, format='turtle')

        places = Graph()

        self.assertIsNotNone(g.value(place1, SKOS.prefLabel))

        GEONAMES_APIKEYS = [os.environ['GEONAMES_KEY']]
        geo = GeoNamesAPI(GEONAMES_APIKEYS)
        tgn = TGN()

        g, places = handle_sdbm_places(geo, tgn, g, places)

        self.assertIsNone(g.value(place1, SKOS.prefLabel))

        pprint.pprint(list(g))
        pprint.pprint(list(places))

        self.assertEquals(len(list(places.triples((None, RDF.type, CRM.E53_Place)))), 2)
        self.assertEquals(len(list(places.triples((None, MMMS.tgn_uri, None)))), 2)

        self.assertEquals(len(list(g.triples((None, RDF.type, CRM.E53_Place)))), 0)
        self.assertEquals(len(list(g.triples((None, CRM.P7_took_place_at, None)))), 1)
        self.assertEquals(len(list(g.triples((None, CRM.P7_took_place_at, URIRef('http://ldf.fi/mmm/places/tgn_1005755'))))), 1)

