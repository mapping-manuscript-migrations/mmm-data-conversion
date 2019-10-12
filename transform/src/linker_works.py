#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking manuscripts"""

import argparse
import logging
from datetime import datetime
from glob import glob

import re
from rdflib import Graph
from rdflib.namespace import SKOS
from rdflib.util import guess_format

from mmm import read_recon_links, get_mmm_resource_uri, change_resource_uri

log = logging.getLogger(__name__)


class WorkLinker:
    """Linking work instances between the databases"""

    def __init__(self, sdbm: Graph, bodley: Graph, bibale: Graph, recon_file_path='/data/recon_works_*.csv'):

        self.sdbm = sdbm
        self.bodley = bodley
        self.bibale = bibale

        self.links = []
        self.recon_file_path = recon_file_path

    def get_recon_links(self):
        """Get all recon links for works"""

        if not self.recon_file_path:
            return

        log.info('Finding recon files from %s' % self.recon_file_path)

        # Get Recon links
        for f in glob(self.recon_file_path):

            # Get date from filename
            date_match = re.match(r'.+_._(\d{4,}-\d\d-\d\d)\.csv', str(f))
            parsed_date = datetime.strptime(date_match.groups()[0], '%Y-%m-%d').date() if date_match else None

            self.links += read_recon_links(self.bibale, self.bodley, self.sdbm, f, parsed_date)

    def link_works(self):
        """
        Link works based on a list of tuples containing matches, by modifying resources in place.
        """
        self.links = sorted(set(self.links))

        log.info('Got {num} links for person linking'.format(num=len(self.links)))

        for (bib_hit, bod_hit, sdbm_hit) in self.links:

            assert bool(bib_hit) + bool(bod_hit) + bool(sdbm_hit) == 2  # Refactor if need to link all

            # Prioritize hits in order: Bodley, Bibale, SDBM. Follow sameAs links to newest URIs
            hit_order = [get_mmm_resource_uri(self.bibale, self.bodley, self.sdbm, bod_hit),
                         get_mmm_resource_uri(self.bibale, self.bodley, self.sdbm, bib_hit),
                         get_mmm_resource_uri(self.bibale, self.bodley, self.sdbm, sdbm_hit)]

            graph_order = [self.bodley, self.bibale, self.sdbm]

            new_uri = hit_order[0] or hit_order[1]
            redirected_uri = hit_order[2] or hit_order[1]
            redirected_graph = graph_order[2] if hit_order[2] else graph_order[1]

            new_pref_label = graph_order[0].value(hit_order[0], SKOS.prefLabel) if hit_order[0] else \
                graph_order[1].value(hit_order[1], SKOS.prefLabel)

            log.info('Reconciling work {bib} , {bod} , {sdbm} --> {new_uri} {label}'.
                     format(bib=bib_hit, bod=bod_hit, sdbm=sdbm_hit, new_uri=new_uri, label=new_pref_label))

            change_resource_uri(redirected_graph, redirected_uri, new_uri, new_pref_label, add_sameas=True)

