#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking people of three datasets with owl:sameAs links to same viaf links"""

import argparse
import logging
import re
from datetime import datetime
from glob import glob

from rdflib import RDF, OWL
from rdflib.util import guess_format
from linker import change_resource_uri  # form_preflabel,
from mmm import get_mmm_resource_uri, read_recon_links, change_resource_uri
from namespaces import *

log = logging.getLogger(__name__)


class PersonLinker:
    ACTOR_CLASSES = [CRM.E21_Person, CRM.E74_Group, CRM.E39_Actor]

    def __init__(self, sdbm: Graph, bodley: Graph, bibale: Graph, recon_file_path='/data/recon_actors_*.csv'):

        self.sdbm = sdbm
        self.bodley = bodley
        self.bibale = bibale

        self.links = []
        self.recon_file_path = recon_file_path

    def link(self):
        """Initiate the full linking process"""
        self.find_viaf_links()
        self.get_recon_links()
        self.link_people()

    def get_recon_links(self):
        """Get all recon links for persons"""

        if not self.recon_file_path:
            return

        log.info('Finding recon files from %s' % self.recon_file_path)

        # Get Recon links
        for f in glob(self.recon_file_path):

            # Get date from filename
            date_match = re.match(r'.*recon_actors_._(\d{4,}-\d\d-\d\d)\.csv', str(f))
            parsed_date = datetime.strptime(date_match.groups()[0], '%Y-%m-%d').date() if date_match else None

            self.links += read_recon_links(self.bibale, self.bodley, self.sdbm, f, parsed_date)

    def find_viaf_links(self):
        """Find links with VIAF identifiers"""
        links = self.links
        sdbm = self.sdbm
        bodley = self.bodley
        bibale = self.bibale

        #    corresponding sparql query: http://yasgui.org/short/YuGL7V0Bp
        for s1, _, o in sdbm.triples((None, OWL.sameAs, None)):
            if self.qualify_link(str(o)) and self.qualify_class(sdbm, s1):
                for s2, _, _ in bibale.triples((None, OWL.sameAs, o)):
                    if self.qualify_class(bibale, s2):
                        links.append((s2, None, s1))

                for s2, _, _ in bodley.triples((None, OWL.sameAs, o)):
                    if self.qualify_class(bodley, s2):
                        links.append((None, s2, s1))

        for s1, _, o in bodley.triples((None, OWL.sameAs, None)):
            if self.qualify_link(str(o)) and self.qualify_class(bodley, s1):
                for s2, _, _ in bibale.triples((None, OWL.sameAs, o)):
                    if self.qualify_class(bibale, s2):
                        links.append((s2, s1, None))

    def qualify_link(self, txt):
        #    check format viaf.org/viaf/
        return "viaf.org/viaf/" in txt

    def qualify_class(self, g, obj):
        #    check that class is Person, Actor or Organization
        return g.value(obj, RDF.type) in self.ACTOR_CLASSES

    def link_people(self):
        """
        Link people based on a list of tuples containing matches
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

            log.info('Harmonizing actor {bib} , {bod} , {sdbm} --> {new_uri} {label}'.
                     format(bib=bib_hit, bod=bod_hit, sdbm=sdbm_hit, new_uri=new_uri, label=new_pref_label))

            change_resource_uri(redirected_graph, redirected_uri, new_uri, new_pref_label, add_sameas=True)

    def datasets(self):
        return self.bibale, self.bodley, self.sdbm


def main():
    argparser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')

    # argparser.add_argument("task", help="Task to perform", choices=['link_people', 'all'], default='link_people')
    argparser.add_argument("input_bibale", help="Input Bibale RDF file")
    argparser.add_argument("input_bodley", help="Input Bodley RDF file")
    argparser.add_argument("input_sdbm", help="Input SDBM RDF file")
    argparser.add_argument("--loglevel", default='DEBUG', help="Logging level",
                           choices=["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    argparser.add_argument("--logfile", default='tasks.log', help="Logfile")

    args = argparser.parse_args()

    log = logging.getLogger()  # Get root logger
    log_handler = logging.FileHandler(args.logfile)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(log_handler)
    log.setLevel(args.loglevel)

    log.info('Reading input graphs.')

    bibale = Graph()
    bibale.parse(args.input_bibale, format=guess_format(args.input_bibale))
    bodley = Graph()
    bodley.parse(args.input_bodley, format=guess_format(args.input_bodley))
    sdbm = Graph()
    sdbm.parse(args.input_sdbm, format=guess_format(args.input_sdbm))

    # if args.task in ['link_people', 'all']:
    log.info('Linking people of three graphs')
    p = PersonLinker(sdbm, bodley, bibale)

    p.link()

    if p.links:
        bibale, bodley, sdbm = p.datasets()

        log.info('Serializing output files...')

        filename_suffix = '_people.ttl'  # '_' + args.task + '.ttl'
        bind_namespaces(bibale).serialize(args.input_bibale.split('.')[0] + filename_suffix, format='turtle')
        bind_namespaces(bodley).serialize(args.input_bodley.split('.')[0] + filename_suffix, format='turtle')
        bind_namespaces(sdbm).serialize(args.input_sdbm.split('.')[0] + filename_suffix, format='turtle')
    else:
        log.warning('No links found')

    log.info('Task finished.')


if __name__ == '__main__':
    main()
