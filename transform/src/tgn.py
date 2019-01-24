#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Link TGN places and retrieve data"""

import logging

import requests

log = logging.getLogger(__name__)


def search_tgn_place(place_name: str, lat: str, lon: str, radius='50km',
                     endpoint='http://vocab.getty.edu/sparql.json'):
    """
    Search for a single place in TGN based on name and coordinates

    :param place_name: Place name in English (or French)
    :param lat: Latitude (wgs84)
    :param lon: Longitude (wgs84)
    :param radius: Search radius
    :param endpoint: Getty endpoint
    :return: dict of TGN place information

    >>> search_tgn_place('Buarcos', '40.19', '-8.865', radius='5km')
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
          ?uri gvp:placeTypePreferred/gvp:prefLabelGVP/xl:literalForm ?place_type_en .
          ?uri gvp:prefLabelGVP/xl:literalForm ?gvp_pref_label .
          ?uri gvp:broaderPreferred ?parent_uri .

          ?uri (xl:prefLabel|xl:altLabel)/xl:literalForm ?label .
          FILTER(LANG(?label) in ("en", "fr", ""))

          OPTIONAL {{
            ?uri (xl:prefLabel/xl:literalForm) ?pref_label_en .
            FILTER(LANG(?pref_label_en) in ("en"))
          }}
          BIND(COALESCE(?pref_label_en, ?gvp_pref_label) as ?pref_label)
        }}
    """

    log.info('Finding TGN place for: %s, %s, %s' % (place_name, lat, lon))

    results = requests.post(endpoint, {'query': query_template.format(lat=lat, lon=lon, radius=radius)}).json()

    tgn_match = {}
    for place in results['results']['bindings']:
        label = place['label']['value']
        pref_label = place['pref_label']['value']
        uri = place['uri']['value']

        # TODO: Fuzzy match
        if place_name in [label, pref_label] and tgn_match.get('uri') != uri:

            tgn = {'uri': uri,
                   'pref_label': pref_label,
                   'lat': place['lat']['value'],
                   'long': place['long']['value'],
                   'label': label,
                   'place_type': place['place_type_en']['value'],
                   'parent': place['parent_uri']['value'],
                   }

            if tgn_match:
                if tgn['place_type'] != 'inhabited places':
                    log.info('Skipping new duplicate place: %s --- OLD: %s' % (tgn, tgn_match))
                    continue
                else:
                    if tgn_match['place_type'] == 'inhabited places':
                        log.error('Duplicate good matches, using new one: %s --- OLD: %s' % (tgn, tgn_match))
                        # TODO: Calculate distance, take closer place
                    else:
                        log.warning('Taking new duplicate place into use: %s --- OLD: %s' % (tgn, tgn_match))

            tgn_match = tgn

    if tgn_match:
        log.info('Found TGN match for %s' % place_name)
    else:
        log.info('No TGN match for %s' % place_name)

    return tgn_match


def get_place_by_uri(uri: str, endpoint='http://vocab.getty.edu/sparql.json'):
    """
    Get place by TGN URI

    >>> get_place_by_uri('http://vocab.getty.edu/tgn/7003820')['pref_label']
    'Coimbra'
    """

    query_template = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX xl: <http://www.w3.org/2008/05/skos-xl#>
        PREFIX gvp: <http://vocab.getty.edu/ontology#>
        prefix ontogeo: <http://www.ontotext.com/owlim/geo#>
        PREFIX wgs84: <http://www.w3.org/2003/01/geo/wgs84_pos#>
        
        SELECT ?uri ?pref_label ?lat ?long ?place_type_en ?parent_uri {{
          VALUES ?uri {{ <{place_uri}> }}
          ?uri foaf:focus [ wgs84:lat ?lat ; wgs84:long ?long ] .
          ?uri gvp:placeTypePreferred/gvp:prefLabelGVP/xl:literalForm ?place_type_en .
          ?uri gvp:prefLabelGVP/xl:literalForm ?gvp_pref_label .
          ?uri gvp:broaderPreferred ?parent_uri .
        
          OPTIONAL {{
            ?uri (xl:prefLabel/xl:literalForm) ?pref_label_en .
            FILTER(LANG(?pref_label_en) in ("en"))
          }}
          BIND(COALESCE(?pref_label_en, ?gvp_pref_label) as ?pref_label)
        }}
    """

    log.info('Retrieving TGN place %s' % uri)

    results = requests.post(endpoint, {'query': query_template.format(place_uri=str(uri))}).json()

    res = results['results']['bindings'][0]
    tgn = {'uri': uri,
           'pref_label': res['pref_label']['value'],
           'lat': res['lat']['value'],
           'long': res['long']['value'],
           'place_type': res['place_type_en']['value'],
           'parent': res['parent_uri']['value'],
           }

    return tgn
