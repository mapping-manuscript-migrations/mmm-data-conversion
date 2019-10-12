#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Functions for MMM entity linking"""

import logging
import re
from datetime import date
from itertools import chain

import pandas as pd
from rdflib import OWL, Graph, URIRef, Literal
from rdflib import URIRef, Graph, Literal

from linker_places import redirect_refs
from namespaces import MMMS, SKOS

log = logging.getLogger(__name__)


def is_mmm_uri(uri: {str, URIRef}):
    return str(uri).startswith('^http://ldf\.fi/mmm/')


def is_bibale_uri(uri: {str, URIRef}):
    """
    Check if the URI format should contain a Bibale resource

    >>> is_bibale_uri('foo')
    False
    >>> is_bibale_uri('http://ldf.fi/mmm/manifestation_singleton/bibale_10022')
    True
    >>> is_bibale_uri('http://ldf.fi/mmm/manifestation_singleton/sdbm_10')
    False
    >>> is_bibale_uri(URIRef('http://ldf.fi/mmm/manifestation_singleton/sdbm_10'))
    False
    >>> is_bibale_uri(URIRef('http://ldf.fi/mmm/manifestation_singleton/bodley_manuscript_100'))
    False
    """
    if re.match('^http://ldf\.fi/mmm/.*bibale', str(uri)):
        return True

    return False


def is_bodley_uri(uri: {str, URIRef}):
    """
    Check if the URI format should contain a Bodleian resource

    >>> is_bodley_uri('foo')
    False
    >>> is_bodley_uri('http://ldf.fi/mmm/manifestation_singleton/bibale_10022')
    False
    >>> is_bodley_uri('http://ldf.fi/mmm/manifestation_singleton/sdbm_10')
    False
    >>> is_bodley_uri(URIRef('http://ldf.fi/mmm/manifestation_singleton/sdbm_10'))
    False
    >>> is_bodley_uri(URIRef('http://ldf.fi/mmm/manifestation_singleton/bodley_manuscript_100'))
    True
    """
    if re.match('^http://ldf\.fi/mmm/.*bodley', str(uri)):
        return True

    return False


def is_sdbm_uri(uri: {str, URIRef}):
    """
    Check if the URI format should contain an SDBM resource

    >>> is_sdbm_uri('foo')
    False
    >>> is_sdbm_uri('http://ldf.fi/mmm/manifestation_singleton/bibale_10022')
    False
    >>> is_sdbm_uri('http://ldf.fi/mmm/manifestation_singleton/sdbm_10')
    True
    >>> is_sdbm_uri(URIRef('http://ldf.fi/mmm/manifestation_singleton/sdbm_10'))
    True
    >>> is_sdbm_uri(URIRef('http://ldf.fi/mmm/manifestation_singleton/bodley_manuscript_100'))
    False
    >>> is_sdbm_uri(URIRef('http://ldf.fi/mmm/work/100018'))
    True
    """
    if re.match('^http://ldf\.fi/mmm/.*sdbm', str(uri)) or re.match('^http://ldf\.fi/mmm/work/[0-9]', str(uri)):
        return True

    return False


def get_mmm_resource_uri(bib: Graph, bod: Graph, sdbm: Graph, original_uri: URIRef):
    """
    Follow sameAs-links to find the latest URI for the resource
    """

    links = chain((bib.objects(original_uri, OWL.sameAs)), bod.objects(original_uri, OWL.sameAs),
                  sdbm.objects(original_uri, OWL.sameAs))
    good_uris = []

    for new_uri in links:
        if is_mmm_uri(new_uri):
            good_uris.append(new_uri)

    good_uris = list(set(good_uris))

    if len(good_uris) == 1:
        return get_mmm_resource_uri(bib, bod, sdbm, good_uris[0])
    elif len(good_uris) > 1:
        log.error('Multiple owl:sameAs links from resource %s  (following one link)' % original_uri)
        return get_mmm_resource_uri(bib, bod, sdbm, good_uris[0])
    else:
        return original_uri


def _add_recon_date(graph: Graph, uri: str, recon_date: date):
    if recon_date:
        graph.add((URIRef(uri), MMMS.recon_date, Literal(recon_date)))


def read_recon_links(bibale: Graph, bodley: Graph, sdbm: Graph, csv, csv_date: date):
    """
    Read entity links from a CSV file
    """
    csv_data = pd.read_csv(csv, header=0, keep_default_na=False, usecols=["Match", "URI"])

    links = []

    for row in csv_data.itertuples(index=True):

        uri = row.URI
        matches = row.Match  # type: str
        for match in matches.split(", "):

            if not match:
                continue

            bib_uri = None
            bod_uri = None
            sdbm_uri = None

            if is_bibale_uri(uri):
                bib_uri = uri
                _add_recon_date(bibale, uri, csv_date)
            elif is_bodley_uri(uri):
                bod_uri = uri
                _add_recon_date(bodley, uri, csv_date)
            elif is_sdbm_uri(uri):
                sdbm_uri = uri
                _add_recon_date(sdbm, uri, csv_date)
            else:
                log.error('Unidentified URI %s' % uri)
                continue

            if is_bibale_uri(match):
                bib_uri = match
            elif is_bodley_uri(match):
                bod_uri = match
            elif is_sdbm_uri(match):
                sdbm_uri = match
            else:
                log.error('Unidentified URI %s' % match)
                continue

            if bool(bib_uri) + bool(bod_uri) + bool(sdbm_uri) >= 2:
                links.append((URIRef(bib_uri) if bib_uri else None,
                              URIRef(bod_uri) if bod_uri else None,
                              URIRef(sdbm_uri) if sdbm_uri else None))
            else:
                log.error('Source database internal hit: %s  -  %s' % (uri, match))

    log.info('Found {num} links with date {date}'.format(num=len(links), date=csv_date))

    return links


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