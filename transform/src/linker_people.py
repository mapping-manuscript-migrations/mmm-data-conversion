#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking people of three datasets with owl:sameAs links to same viaf links"""

import argparse
import logging
import os
import re

from rdflib import URIRef, Literal, RDF, OWL
from rdflib.util import guess_format
from manuscripts import change_manuscript_uri # form_preflabel,
from namespaces import *

log = logging.getLogger(__name__)


class PersonLinker:

    ACTOR_CLASSES = [CRM.E21_Person, CRM.E74_Group, CRM.E39_Actor]

    def __init__(self, sdbm: Graph, bodley: Graph, bibale: Graph):

        self.links = []
        self.sdbm = sdbm
        self.bodley = bodley
        self.bibale = bibale

        self.findLinks()
        self.link_people()


    def findLinks(self):
        links = self.links
        sdbm = self.sdbm
        bodley = self.bodley
        bibale = self.bibale

        #    corresponding sparql query: http://yasgui.org/short/YuGL7V0Bp
        for s1,_,o in sdbm.triples( (None, OWL.sameAs, None) ):
            if self.qualifyLink(str(o)) and self.qualifyClass(sdbm,s1):
                for s2,_,_ in bibale.triples( (None, OWL.sameAs, o) ):
                    if self.qualifyClass(bibale,s2):
                        links.append((s2, None, s1))
                for s2,_,_ in bodley.triples( (None, OWL.sameAs, o) ):
                    if self.qualifyClass(bodley,s2):
                        links.append((None, s2, s1))

        for s1,_,o in bodley.triples( (None, OWL.sameAs, None) ):
            if self.qualifyLink(str(o)) and self.qualifyClass(bodley,s1):
                for s2,_,_ in bibale.triples( (None, OWL.sameAs, o) ):
                    if self.qualifyClass(bibale,s2):
                        links.append((s2, s1, None))




    def qualifyLink(self, txt):
        #    check format viaf.org/viaf/
        return "viaf.org/viaf/" in txt

    def qualifyClass(self, g, obj):
        #    check that class is Person, Actor or Organization
        return g.value(obj, RDF.type) in self.ACTOR_CLASSES


    def link_people(self):
        """
        Link manuscripts based on a list of tuples containing matches
        """
        self.links = sorted(set(self.links))

        #    log.info('Got {num} links for manuscript linking'.format(num=len(links)))

        for (bib_hit, bod_hit, sdbm_hit) in self.links:

            if bib_hit is None:

                new_uri = bod_hit
                new_pref_label = self.bodley.value(bod_hit, SKOS.prefLabel)
                change_manuscript_uri(self.sdbm, sdbm_hit, new_uri, new_pref_label,
                                      add_sameas=True)
            elif sdbm_hit is None:

                new_uri = bod_hit
                new_pref_label = self.bodley.value(bod_hit, SKOS.prefLabel)
                change_manuscript_uri(self.bibale, bib_hit, new_uri, new_pref_label,
                                      add_sameas=True)
            elif bod_hit is None:

                new_uri = bib_hit
                new_pref_label = self.bibale.value(bib_hit, SKOS.prefLabel)
                change_manuscript_uri(self.sdbm, sdbm_hit, new_uri, new_pref_label,
                                      add_sameas=True)


            """
            elif bod_hit is None:
                change_manuscript_uri(bodley, bod_hit, new_uri, new_pref_label)

            if sdbm_hit:
                change_manuscript_uri(sdbm, sdbm_hit, new_uri, new_pref_label)

            """

            log.info(
                'Harmonizing actor {bib} , {bod} , {sdbm} --> {new_uri} {label}'.
                    format(bib=bib_hit, bod=bod_hit, sdbm=sdbm_hit, new_uri=new_uri, label=new_pref_label))

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

    if p.links:
        log.info('Linking manuscripts using found links')

        bibale, bodley, sdbm = p.datasets()

        log.info('Serializing output files...')

        filename_suffix = '_people.ttl' # '_' + args.task + '.ttl'
        bind_namespaces(bibale).serialize(args.input_bibale.split('.')[0] + filename_suffix, format='turtle')
        bind_namespaces(bodley).serialize(args.input_bodley.split('.')[0] + filename_suffix, format='turtle')
        bind_namespaces(sdbm).serialize(args.input_sdbm.split('.')[0] + filename_suffix, format='turtle')
    else:
        log.warning('No links found')

    log.info('Task finished.')


if __name__ == '__main__':
    main()
