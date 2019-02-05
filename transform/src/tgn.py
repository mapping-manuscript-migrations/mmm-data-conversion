#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Link Getty TGN places and retrieve data"""

import logging
from decimal import Decimal
from typing import Union

import requests
from rdflib import URIRef, Literal, RDF

from namespaces import *


class TGN:
    """
    Getty TGN querying via SPARQL
    """

    def __init__(self, endpoint='http://vocab.getty.edu/sparql.json'):
        self.endpoint = endpoint

        self.log = logging.getLogger(__name__)

    def query_tgn(self, query, retries=5):
        results = None
        while not results and retries:
            results = requests.post(self.endpoint,
                                    {'query': query},
                                    timeout=31).json()
            retries -= 1

        return results['results']['bindings']

    def search_tgn_place(self, place_name: str, lat: str, lon: str, radius='50km'):
        """
        Search for a single place in TGN based on name and coordinates

        :param place_name: Place name in English (or French)
        :param lat: Latitude (wgs84)
        :param lon: Longitude (wgs84)
        :param radius: Search radius
        :return: dict of TGN place information

        >>> TGN().search_tgn_place('Buarcos', '40.19', '-8.865', radius='5km')
        {'uri': 'http://vocab.getty.edu/tgn/7744552', 'pref_label': 'Buarcos', 'lat': '40.166039', 'long': '-8.876801', 'label': 'Buarcos', 'place_type': 'inhabited places', 'parent': 'http://vocab.getty.edu/tgn/7003820'}
        """
        query_template = """
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX xl: <http://www.w3.org/2008/05/skos-xl#>
            PREFIX gvp: <http://vocab.getty.edu/ontology#>
            prefix ontogeo: <http://www.ontotext.com/owlim/geo#>
            PREFIX wgs84: <http://www.w3.org/2003/01/geo/wgs84_pos#>
    
            SELECT ?uri ?pref_label ?lat ?long ?label ?place_type_en ?parent_uri {{
              ?uri foaf:focus [ ontogeo:nearby( {lat} {lon} "{radius}") ] .
              ?uri foaf:focus [ wgs84:lat ?lat ; wgs84:long ?long ] .
              OPTIONAL {{ ?uri gvp:placeTypePreferred/gvp:prefLabelGVP/xl:literalForm ?place_type_en }}
              ?uri gvp:prefLabelGVP/xl:literalForm ?gvp_pref_label .
              OPTIONAL {{ ?uri gvp:broaderPreferred ?parent_uri }}
    
              ?uri (xl:prefLabel|xl:altLabel)/xl:literalForm ?label .
              FILTER(LANG(?label) in ("en", "fr", ""))
    
              OPTIONAL {{
                ?uri (xl:prefLabel/xl:literalForm) ?pref_label_en .
                FILTER(LANG(?pref_label_en) in ("en"))
              }}
              BIND(COALESCE(?pref_label_en, ?gvp_pref_label) as ?pref_label)
            }}
        """

        self.log.info('Finding TGN place for: %s, %s, %s' % (place_name, lat, lon))

        results = self.query_tgn(query_template.format(lat=lat, lon=lon, radius=radius))

        tgn_match = {}
        for place in results:
            label = place['label']['value']
            pref_label = place['pref_label']['value']
            uri = place['uri']['value']

            # TODO: Fuzzy matching of labels
            if place_name in [label, pref_label] and tgn_match.get('uri') != uri:

                tgn = {'uri': uri,
                       'pref_label': pref_label,
                       'lat': place['lat']['value'],
                       'long': place['long']['value'],
                       'label': label,
                       'place_type': place.get('place_type_en', {}).get('value'),
                       'parent': place.get('parent_uri', {}).get('value'),
                       }

                if tgn_match:
                    if tgn['place_type'] != 'inhabited places':
                        self.log.info('Skipping new duplicate place: %s --- OLD: %s' % (tgn, tgn_match))
                        continue
                    else:
                        if tgn_match['place_type'] == 'inhabited places':
                            self.log.error('Duplicate good matches, using new one: %s --- OLD: %s' % (tgn, tgn_match))
                            # TODO: Calculate distance, take closer place
                        else:
                            self.log.warning('Taking new duplicate place into use: %s --- OLD: %s' % (tgn, tgn_match))

                tgn_match = tgn

        if tgn_match:
            self.log.info('Found TGN match for %s' % place_name)
        else:
            self.log.info('No TGN match for %s' % place_name)

        return tgn_match

    def get_place_by_uri(self, uri: URIRef):
        """
        Get place by TGN URI

        >>> TGN().get_place_by_uri('http://vocab.getty.edu/tgn/7003820')['pref_label']
        'Coimbra'
        >>> TGN().get_place_by_uri(URIRef('http://vocab.getty.edu/tgn/7003820'))['pref_label']
        'Coimbra'
        >>> TGN().get_place_by_uri('http://vocab.getty.edu/tgn/7003820_bad_uri')
        {}
        """

        query_template = """
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX xl: <http://www.w3.org/2008/05/skos-xl#>
            PREFIX gvp: <http://vocab.getty.edu/ontology#>
            prefix ontogeo: <http://www.ontotext.com/owlim/geo#>
            PREFIX wgs84: <http://www.w3.org/2003/01/geo/wgs84_pos#>
            
            SELECT ?uri ?pref_label ?lat ?long ?place_type_en ?parent_uri {{
              VALUES ?uri {{ <{place_uri}> }}
              OPTIONAL {{ ?uri foaf:focus [ wgs84:lat ?lat ; wgs84:long ?long ] }}
              OPTIONAL {{ ?uri gvp:placeTypePreferred/gvp:prefLabelGVP/xl:literalForm ?place_type_en }}
              ?uri gvp:prefLabelGVP/xl:literalForm ?gvp_pref_label .
              OPTIONAL {{ ?uri gvp:broaderPreferred ?parent_uri . }}
            
              OPTIONAL {{
                ?uri (xl:prefLabel/xl:literalForm) ?pref_label_en .
                FILTER(LANG(?pref_label_en) in ("en"))
              }}
              BIND(COALESCE(?pref_label_en, ?gvp_pref_label) as ?pref_label)
            }}
        """

        self.log.info('Retrieving TGN place %s' % uri)

        res = self.query_tgn(query_template.format(place_uri=str(uri)))

        if len(res):
            res = res[0]
        else:
            return {}

        tgn = {'uri': uri,
               'pref_label': res['pref_label']['value'],
               'lat': res.get('lat', {}).get('value'),
               'long': res.get('long', {}).get('value'),
               'place_type': res.get('place_type_en', {}).get('value'),
               'parent': res.get('parent_uri', {}).get('value'),
               }

        return tgn

    def place_rdf(self, uri: URIRef, tgn: dict):
        """
        Map place dict to an RDF graph

        >>> tgn = TGN()
        >>> place = tgn.get_place_by_uri('http://vocab.getty.edu/tgn/7003820')
        >>> len(tgn.place_rdf(URIRef('http://test.com/place_1'), place))
        8
        >>> len(tgn.place_rdf(URIRef('http://test.com/place_2'), {}))
        0
        """
        g = Graph()

        if not tgn:
            return g

        g.add((uri, RDF.type, CRM.E53_Place))
        g.add((uri, DCT.source, URIRef('http://vocab.getty.edu/tgn/')))
        g.add((uri, MMMS.tgn_uri, URIRef(tgn['uri'])))
        g.add((uri, SKOS.prefLabel, Literal(tgn['pref_label'])))
        if tgn.get('parent'):
            g.add((uri, GVP.broaderPreferred, URIRef(tgn['parent'])))

        if tgn.get('lat'):
            g.add((uri, WGS84.lat, Literal(Decimal(tgn['lat']))))
        if tgn.get('long'):
            g.add((uri, WGS84.long, Literal(Decimal(tgn['long']))))
        if tgn.get('place_type'):
            g.add((uri, GVP.placeTypePreferred, Literal(tgn['place_type'])))

        if tgn.get('label'):
            g.add((uri, SKOS.altLabel, Literal(tgn['label'])))

        return g
