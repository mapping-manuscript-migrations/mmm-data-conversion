#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""MMM entity linking"""
import logging
import re
from itertools import chain

from rdflib import URIRef, OWL, Graph

log = logging.getLogger(__name__)


def is_mmm_uri(uri: {str, URIRef}):
    return str(uri).startswith('^http://ldf\.fi/mmm/')


def is_bibale_uri(uri: {str, URIRef}):
    if re.match('^http://ldf\.fi/mmm/.*bibale', str(uri)):
        return True


def is_bodley_uri(uri: {str, URIRef}):
    if re.match('^http://ldf\.fi/mmm/.*bodley', str(uri)):
        return True


def is_sdbm_uri(uri: {str, URIRef}):
    if re.match('^http://ldf\.fi/mmm/.*sdbm', str(uri)):
        return True


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

