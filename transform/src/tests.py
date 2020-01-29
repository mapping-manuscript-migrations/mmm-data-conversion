#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""
Tests for linking places of MMM datasets to GeoNames and TGN

Requires GeoNames API key, and also that GeoNames and TGN APIs are accessible. The linking requires is completely
dependent on these APIs, hence they get also tested to work as expected with these tests.
"""

import os
import pprint
import unittest
from io import StringIO

from rdflib import URIRef, RDF, OWL, Literal

from linker_places import PlaceLinker
from linker import read_manuscript_links, link_by_shelfmark, link_manuscripts, get_last_known_locations
from mmm import change_resource_uri
from namespaces import *


class TestLinkerSDBM(unittest.TestCase):
    test_sdbm_data = """
    @prefix :      <https://sdbm.library.upenn.edu/> .
    @prefix wgs:   <http://www.w3.org/2003/01/geo/wgs84_pos#> .
    @prefix mmms: <http://ldf.fi/schema/mmm/> .
    @prefix dct:   <http://purl.org/dc/terms/> .
    @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix owl:   <http://www.w3.org/2002/07/owl#> .
    @prefix afn:   <http://jena.hpl.hp.com/ARQ/function#> .
    @prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
    @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix mmm:   <http://ldf.fi/mmm/> .
    @prefix ecrm:   <http://erlangen-crm.org/current/> .
    @prefix frbroo: <http://erlangen-crm.org/efrbroo/> .

    <http://ldf.fi/mmm/production/orphan_61316>
        a                      ecrm:E12_Production ;
        dct:source             mmms:SDBM ;
        ecrm:P108_has_produced  <http://ldf.fi/mmm/manifestation_singleton/orphan_61316> ;
        ecrm:P4_has_time-span   <http://ldf.fi/mmm/time/59403> ;
        ecrm:P7_took_place_at   <http://ldf.fi/mmm/place/1012> .

    <http://ldf.fi/mmm/place/2121>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://sdbm.library.upenn.edu/place/2121> ;
            dct:source                    mmms:SDBM ;
            ecrm:P89_falls_within          <http://ldf.fi/mmm/place/214> ;
            owl:sameAs                    <http://vocab.getty.edu/tgn/1005755> ;
            wgs:lat                       51.5833 ;
            wgs:long                      -0.0833 ;
            skos:prefLabel                "Tottenham" .

    <http://ldf.fi/mmm/place/1012>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://sdbm.library.upenn.edu/place/1012> ;
            dct:source                    mmms:SDBM ;
            ecrm:P89_falls_within          <http://ldf.fi/mmm/place/3991> ;
            owl:sameAs                    <http://vocab.getty.edu/tgn/7005560> ;
            wgs:lat                       "23"^^<http://www.w3.org/2001/XMLSchema#decimal> ;
            wgs:long                      "-102"^^<http://www.w3.org/2001/XMLSchema#decimal> ;
            skos:prefLabel                "Mexico" .

    <http://ldf.fi/mmm/place/847>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://sdbm.library.upenn.edu/place/847> ;
            dct:source                    mmms:SDBM ;
            ecrm:P89_falls_within          <http://ldf.fi/mmm/place/2398> ;
            owl:sameAs                    <http://vocab.getty.edu/tgn/7024079> ;
            wgs:lat                       "32"^^<http://www.w3.org/2001/XMLSchema#decimal> ;
            wgs:long                      "56"^^<http://www.w3.org/2001/XMLSchema#decimal> ;
            skos:prefLabel                "Persia" .
    """

    def test_handle_tgn_places_sdbm(self):
        place1 = URIRef('http://ldf.fi/mmm/place/2121')

        g = Graph()
        g.parse(data=self.test_sdbm_data, format='turtle')

        places = Graph()

        self.assertIsNotNone(g.value(place1, SKOS.prefLabel))

        GEONAMES_APIKEYS = [os.environ['GEONAMES_KEY']]
        linker = PlaceLinker(GEONAMES_APIKEYS, places)

        g = linker.handle_tgn_places(g, 'sdbm_', MMMS.SDBM)

        self.assertIsNone(g.value(place1, SKOS.prefLabel))

        pprint.pprint(sorted(places))

        self.assertEquals(len(list(places.triples((None, RDF.type, CRM.E53_Place)))), 11)
        self.assertEquals(len(list(places.triples((None, OWL.sameAs, None)))), 11)

        self.assertEquals(len(list(g.triples((None, RDF.type, CRM.E53_Place)))), 0)
        self.assertEquals(len(list(g.triples((None, CRM.P7_took_place_at, None)))), 1)
        self.assertEquals(
            len(list(g.triples((None, CRM.P7_took_place_at, URIRef('http://ldf.fi/mmm/place/tgn_7005560'))))), 1)

        self.assertEquals(len(list(places.triples((None, WGS84.lat, None)))), 10)  # All except World
        self.assertEquals(len(list(places.triples((None, WGS84.long, None)))), 10)

        # Test all parents have labels

        for parent in places.objects(None, GVP.broaderPreferred):
            print(parent)
            self.assertIsNotNone(places.value(parent, SKOS.prefLabel))


class TestLinkerBodley(unittest.TestCase):
    test_bodley_data = """
    @prefix :      <https://sdbm.library.upenn.edu/> .
    @prefix wgs:   <http://www.w3.org/2003/01/geo/wgs84_pos#> .
    @prefix mmms: <http://ldf.fi/schema/mmm/> .
    @prefix dct:   <http://purl.org/dc/terms/> .
    @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix owl:   <http://www.w3.org/2002/07/owl#> .
    @prefix afn:   <http://jena.hpl.hp.com/ARQ/function#> .
    @prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
    @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix mmm:   <http://ldf.fi/mmm/> .
    @prefix ecrm:   <http://erlangen-crm.org/current/> .
    @prefix frbroo: <http://erlangen-crm.org/efrbroo/> .

    <https://medieval.bodleian.ox.ac.uk/catalog/place_1029598>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/place_1029598> ;
            dct:source                    mmms:Bodley ;
            ecrm:P89_falls_within          <https://medieval.bodleian.ox.ac.uk/catalog/place_place_7002445> ;
            wgs:lat                       "51.983333" ;
            wgs:long                      "-1.483333" ;
            owl:sameAs                    <http://vocab.getty.edu/tgn/7011931> ;
            skos:altLabel                 "Hochenartone" , "Hook Norton, Oxfordshire" ;
            skos:prefLabel                "Hook Norton, Oxfordshire" .

    <https://medieval.bodleian.ox.ac.uk/catalog/place_7002445>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/place_7002445> ;
            dct:source                    mmms:Bodley ;
            wgs:lat                       "53.0" ;
            wgs:long                      "-2.0" ;
            skos:altLabel                 "Angleterre" , "English"@en , "English" , "Britannia Romana" , "Inglaterra" , "Britannia propria" , "Anglia" , "Britannia maior" , "Inghilterra" , "Engleterre" , "England"@en , "England" ;
            skos:prefLabel                "England" .

    <https://medieval.bodleian.ox.ac.uk/catalog/manuscript_3947/production>
            a                      ecrm:E12_Production ;
            dct:source             mmms:Bodley ;
            ecrm:P108_has_produced  <https://medieval.bodleian.ox.ac.uk/catalog/manuscript_3947> ;
            ecrm:P4_has_time-span   <https://medieval.bodleian.ox.ac.uk/catalog/manuscript_3947/production-time-span> ;
            ecrm:P7_took_place_at   <https://medieval.bodleian.ox.ac.uk/catalog/place_1029598> ,
                                   <https://medieval.bodleian.ox.ac.uk/catalog/place_7002445> .

    <https://medieval.bodleian.ox.ac.uk/catalog/manuscript_3947>
            a                             frbroo:F4_Manifestation_Singleton ;
            mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/manuscript_3947> ;
            mmms:manuscript_work    <https://medieval.bodleian.ox.ac.uk/catalog/work_16002> ;
            dct:source                    mmms:Bodley ;
            ecrm:P128_carries              <https://medieval.bodleian.ox.ac.uk/catalog/manuscript_3947%23Christ_Church_MS_343-item1/expression> ;
            ecrm:P51_has_former_or_current_owner
                    <https://medieval.bodleian.ox.ac.uk/catalog/person_37261411> , <https://medieval.bodleian.ox.ac.uk/catalog/person_2677> , <https://medieval.bodleian.ox.ac.uk/catalog/org_155836576> ;
            skos:prefLabel                "Christ Church MS. 343"@en .
    """

    def test_handle_tgn_places_bodley(self):
        place1 = URIRef('https://medieval.bodleian.ox.ac.uk/catalog/place_1029598')

        g = Graph()
        g.parse(data=self.test_bodley_data, format='turtle')

        self.assertIsNotNone(g.value(place1, SKOS.prefLabel))

        GEONAMES_APIKEYS = [os.environ['GEONAMES_KEY']]
        places = Graph()
        linker = PlaceLinker(GEONAMES_APIKEYS, places)

        pprint.pprint(sorted(places))
        self.assertEquals(len(places), 0)

        g = linker.handle_tgn_places(g, 'bodley_', MMMS.Bodley)

        pprint.pprint(sorted(places))

        self.assertIsNone(g.value(place1, SKOS.prefLabel))

        self.assertEquals(len(list(places.triples((None, RDF.type, CRM.E53_Place)))), 7)
        self.assertEquals(len(list(places.triples((None, OWL.sameAs, None)))), 6)  # Oxford and her 5 parents

        self.assertEquals(len(list(g.triples((None, RDF.type, CRM.E53_Place)))), 0)
        self.assertEquals(len(list(g.triples((None, CRM.P7_took_place_at, None)))), 2)

        pprint.pprint(list(g.triples((None, CRM.P7_took_place_at, None))))

        self.assertEquals(
            len(list(g.triples((None, CRM.P7_took_place_at, URIRef('http://ldf.fi/mmm/place/tgn_7011931'))))), 1)

        self.assertEquals(len(list(places.triples((None, WGS84.lat, None)))), 6)
        self.assertEquals(len(list(places.triples((None, WGS84.long, None)))), 6)

        # Test all parents have labels

        for parent in places.objects(None, GVP.broaderPreferred):
            print(parent)
            self.assertIsNotNone(places.value(parent, SKOS.prefLabel))


class TestLinkerBibale(unittest.TestCase):
    test_bibale_data = """
    @prefix mmms: <http://ldf.fi/schema/mmm/> .
    @prefix dct:   <http://purl.org/dc/terms/> .
    @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix owl:   <http://www.w3.org/2002/07/owl#> .
    @prefix afn:   <http://jena.hpl.hp.com/ARQ/function#> .
    @prefix frbroo2: <http://www.cidoc-crm.org/frbroo/> .
    @prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
    @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix mmm:   <http://ldf.fi/mmm/> .
    @prefix frbroo: <http://erlangen-crm.org/efrbroo/> .
    @prefix ecrm:   <http://erlangen-crm.org/current/> .
    @prefix bibale: <http://bibale.irht.cnrs.fr/> .

    bibale:element:876437
            a                             ecrm:E53_Place ;
            mmms:bibale_country     "France" ;
            mmms:bibale_region      "Grand Est" ;
            mmms:bibale_settlement  "Épinal" ;
            mmms:place_type         bibale:type:settlement ;
            dct:source                    mmms:Bibale ;
            owl:sameAs                    <http://www.geonames.org/3020035> ;
            skos:altLabel                 "France, Grand Est, Épinal" ;
            skos:prefLabel                "Épinal" .

    bibale:element:57644-272
            a                             ecrm:E53_Place ;
            mmms:bibale_country     "Allemagne" ;
            mmms:bibale_region      "Rheinland-Pfalz (Rhénanie-Palatinat)" ;
            mmms:bibale_settlement  "Trier (Trèves)" ;
            mmms:place_type         bibale:type:settlement ;
            dct:source                    mmms:Bibale ;
            skos:altLabel                 "Allemagne, Rheinland-Pfalz (Rhénanie-Palatinat), Trier (Trèves)" ;
            skos:prefLabel                "Trier (Trèves)" .
    """

    def test_bibale_places(self):
        g = Graph()
        g.parse(data=self.test_bibale_data, format='turtle')

        GEONAMES_APIKEYS = [os.environ['GEONAMES_KEY']]
        linker = PlaceLinker(GEONAMES_APIKEYS)
        places = linker.places

        g = linker.handle_bibale_places(g)

        self.assertEquals(len(g), 0)

        self.assertEquals(len(list(places.triples((None, RDF.type, CRM.E53_Place)))), 8)
        self.assertEquals(len(list(places.triples((None, GVP.broaderPreferred, None)))), 7)

        self.assertEquals(len(list(places.triples((None, WGS84.lat, None)))), 7)
        self.assertEquals(len(list(places.triples((None, WGS84.long, None)))), 7)

        # Test all parents have labels

        for parent in places.objects(None, GVP.broaderPreferred):
            print(parent)
            self.assertIsNotNone(places.value(parent, SKOS.prefLabel))


class TestLinkerTGN(unittest.TestCase):
    test_bodley_data_extra = """
        <https://medieval.bodleian.ox.ac.uk/catalog/manuscript_7875/production>
            a                      ecrm:E12_Production ;
            ecrm:P108_has_produced  <http://ldf.fi/mmm/manifestation_singleton/bodley_manuscript_7875> ;
            ecrm:P4_has_time-span   <https://medieval.bodleian.ox.ac.uk/catalog/manuscript_7875/production-time-span> ;
            ecrm:P7_took_place_at   <https://medieval.bodleian.ox.ac.uk/catalog/place_7415093> ,
                <https://medieval.bodleian.ox.ac.uk/catalog/place_7005560> .

        <https://medieval.bodleian.ox.ac.uk/catalog/place_21>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/place_21> ;
            dct:source                    mmms:Bodley ;
            owl:sameAs                    <http://placenames.org.uk/id/placename/24/005479> ;
            wgs:lat                       "51.89493" ;
            wgs:long                      "-1.52538" ;
            skos:altLabel                 "Catsham Lane and Bridge [in Chadlington], Oxfordshire" ;
            skos:prefLabel                "Catsham Lane and Bridge [in Chadlington], Oxfordshire" .

        <https://medieval.bodleian.ox.ac.uk/catalog/place_7291891>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/place_7291891> ;
            dct:source                    mmms:Bodley ;
            owl:sameAs                    <http://www.geonames.org/7291891> , <http://www.visionofbritain.org.uk/place/7116> ;
            wgs:lat                       "52.14707" ;
            wgs:long                      " 1.31332" ;
            skos:altLabel                 "Dallinghoo" , "Dallinghoe, Suffolk" ;
            skos:prefLabel                "Dallinghoe, Suffolk" .

        <https://medieval.bodleian.ox.ac.uk/catalog/place_7005560>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/place_7005560> ;
            dct:source                    mmms:Bodley ;
            owl:sameAs                    <http://vocab.getty.edu/tgn/7005560> ;
            wgs:lat                       "23.0" ;
            wgs:long                      "-102.0" ;
            skos:altLabel                 "United Mexican States" , "Mexiko" , "المىس مَ" , "Mexico"@en , "Mexico" ,
                    "Мексиканские Соединенные Штаты" , "MX00" , "México" , "República Méjico" ,
                    "Mexicanos, Estados Unidos" , "ا وًلايات المخحدة المىس ىَ ةِ" , "Estados Unidos Mexicanos" ,
                    "Mejicana, República" , "MEX" , "República Mejicana" , "États-Unis du Mexique" ,
                    "Méjico, República" , "Mèssico" , "Mexican Republic" , "Messco" ,
                    "Mexicana, Republica" , "Мексика" , "ISO484" , "Mexique" , "Mexican" , "Mexican"@en ,
                    "墨西哥合众国" , "Republica Mexicana" , "墨西哥" , "Méjico" ;
            skos:prefLabel                "Mexico" .
    """

    test_sdbm_extra = """
        <http://ldf.fi/mmm/place/5>
            a                             ecrm:E53_Place ;
            mmms:data_provider_url  <https://sdbm.library.upenn.edu/place/5> ;
            dct:source                    mmms:SDBM ;
            ecrm:P89_falls_within          <http://ldf.fi/mmm/place/2351> ;
            owl:sameAs                    <http://vocab.getty.edu/tgn/7002445> ;
            wgs:lat                       53.0 ;
            wgs:long                      -2.0 ;
            skos:prefLabel                "England" .
    """

    test_sdbm_data = TestLinkerSDBM.test_sdbm_data + test_sdbm_extra

    test_bodley_data = TestLinkerBodley.test_bodley_data + test_bodley_data_extra

    def test_handle_tgn_places_sdbm_bod(self):
        g = Graph()
        g2 = Graph()

        g.parse(data=self.test_bodley_data, format='turtle')
        g2.parse(data=self.test_sdbm_data, format='turtle')

        places = Graph()

        GEONAMES_APIKEYS = [os.environ['GEONAMES_KEY']]
        linker = PlaceLinker(GEONAMES_APIKEYS, places)

        g = linker.handle_tgn_places(g, 'bodley_', MMMS.Bodley)
        self.assertEquals(len(list(places.triples((None, RDF.type, CRM.E53_Place)))), 11)

        # Add SDBM places
        g2 = linker.handle_tgn_places(g2, 'sdbm_', MMMS.SDBM)
        self.assertEquals(len(list(places.triples((None, RDF.type, CRM.E53_Place)))), 16)

        # Check corrected references
        self.assertEquals(
            len(list(g.triples((None, CRM.P7_took_place_at, URIRef('http://ldf.fi/mmm/place/tgn_7005560'))))), 1)
        self.assertEquals(
            len(list(g2.triples((None, CRM.P7_took_place_at, URIRef('http://ldf.fi/mmm/place/tgn_7005560'))))), 1)

        pprint.pprint(sorted(places.subjects(RDF.type, CRM.E53_Place)))

        pprint.pprint(sorted(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7029392'))))

        # Check place annotations
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/bodley_place_21')))) >= 8)
        self.assertTrue(
            len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/bodley_place_7002445')))) >= 8)
        self.assertTrue(
            len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/bodley_place_7291891')))) >= 8)

        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_1005755')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7005560')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7011931')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7018917')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7024079')))) >= 8)

        # Parent places
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_1000001')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_1000003')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_1000004')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7002445')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7008136')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7008168')))) >= 8)
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7008591')))) >= 8)

        # World
        self.assertTrue(len(list(places.predicate_objects(URIRef('http://ldf.fi/mmm/place/tgn_7029392')))) >= 5)


class TestManuscriptLinking(unittest.TestCase):
    test_csv = """Bibale URL,Bodley URL,SDBM MS Record URL,SDBM Entry URL,Notes
bibale.irht.cnrs.fr/29147,https://medieval.bodleian.ox.ac.uk/catalog/manuscript_4560,,https://sdbm.library.upenn.edu/entries/99694,
http://bibale.irht.cnrs.fr/10832,,https://sdbm.library.upenn.edu/manuscripts/18044,,PHILLIPPS"""

    test_sdbm = """
        @base <http://ldf.fi/mmm/> .
        @prefix :      <https://sdbm.library.upenn.edu/> .
        @prefix wgs:   <http://www.w3.org/2003/01/geo/wgs84_pos#> .
        @prefix mmms: <http://ldf.fi/schema/mmm/> .
        @prefix dct:   <http://purl.org/dc/terms/> .
        @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix owl:   <http://www.w3.org/2002/07/owl#> .
        @prefix afn:   <http://jena.hpl.hp.com/ARQ/function#> .
        @prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
        @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix mmm:   <http://ldf.fi/mmm/> .
        @prefix ecrm:   <http://erlangen-crm.org/current/> .
        @prefix frbroo: <http://erlangen-crm.org/efrbroo/> .

        <manifestation_singleton/18044>
            mmms:data_provider_url <https://sdbm.library.upenn.edu/manuscripts/18044> ;
            mmms:entry <https://sdbm.library.upenn.edu/entries/194739>, <https://sdbm.library.upenn.edu/entries/79641> ;
            mmms:manuscript_author <actor/599> ;
            mmms:manuscript_record <https://sdbm.library.upenn.edu/manuscripts/18044> ;
            mmms:manuscript_work <work/100826>, <work/298734> ;
            dct:source mmms:SDBM ;
            ecrm:P128_carries <expression/100826>, <expression/298734> ;
            a frbroo:F4_Manifestation_Singleton ;
            skos:prefLabel "SDBM_MS_18044" .

        <manifestation_singleton/orphan_99694>
            mmms:data_provider_url <https://sdbm.library.upenn.edu/entries/99694> ;
            mmms:entry <https://sdbm.library.upenn.edu/entries/99694> ;
            mmms:manuscript_author <actor/661> ;
            mmms:manuscript_work <work/125620> ;
            dct:source mmms:SDBM ;
            ecrm:P128_carries <expression/125620> ;
            a frbroo:F4_Manifestation_Singleton ;
            skos:prefLabel "SDBM_MS_orphan_99694" .
        """

    def test_read_manual_links(self):
        bib = Graph()
        bod = Graph()
        sdbm = Graph()

        sdbm.parse(data=self.test_sdbm, format='turtle')

        links = read_manuscript_links(bib, bod, sdbm, StringIO(self.test_csv))

        bib, bod, sdbm = link_manuscripts(bib, bod, sdbm, links)

        pprint.pprint(sorted(sdbm))

        assert len(list(sdbm.triples((URIRef('http://ldf.fi/mmm/manifestation_singleton/bibale_10832'),
                                      RDF.type,
                                      FRBR.F4_Manifestation_Singleton)))) == 1
        assert len(list(sdbm.triples((URIRef('http://ldf.fi/mmm/manifestation_singleton/bodley_manuscript_4560'),
                                      RDF.type,
                                      FRBR.F4_Manifestation_Singleton)))) == 1

    def test_change_manuscript_uri(self):
        bib = Graph()
        bod = Graph()
        sdbm = Graph()

        sdbm.parse(data=self.test_sdbm, format='turtle')

        old_uri = URIRef('http://ldf.fi/mmm/manifestation_singleton/bibale_007')
        bib.add((old_uri, MMMS.phillipps_number, Literal(500)))
        bib.add((old_uri,
                 SKOS.prefLabel,
                 Literal('Bibale test manuscript')))

        change_resource_uri(bib, old_uri, old_uri, Literal('Test'))

        # Nothing should change if old and new URI are the same
        assert len(list(bib)) == 2

        change_resource_uri(bib, old_uri, URIRef('http://example.com/test'), Literal('Test'))

        # The URI should be changed and a new prefLabel added
        assert len(list(bib.predicate_objects(URIRef('http://example.com/test')))) == 3

    def test_link_by_shelfmark(self):
        bib = Graph()
        bod = Graph()
        sdbm = Graph()

        sdbm.parse(data=self.test_sdbm, format='turtle')

        bib.add((URIRef('http://ldf.fi/mmm/manifestation_singleton/bibale_007'), MMMS.phillipps_number, Literal(500)))
        bib.add((URIRef('http://ldf.fi/mmm/manifestation_singleton/bibale_007'),
                 SKOS.prefLabel,
                 Literal('Bibale test manuscript')))
        sdbm.add((URIRef('http://ldf.fi/mmm/manifestation_singleton/18044'), MMMS.phillipps_number, Literal(500)))

        links = link_by_shelfmark(bib, bod, sdbm, MMMS.phillipps_number, "Phillipps")
        links += link_by_shelfmark(bib, bod, sdbm, MMMS.phillipps_number, "Phillipps")

        bib, bod, sdbm = link_manuscripts(bib, bod, sdbm, links)

        pprint.pprint(sorted(bib))
        pprint.pprint(sorted(sdbm))

        assert len(list(bib.predicate_objects(URIRef('http://ldf.fi/mmm/manifestation_singleton/bibale_007')))) > 1
        assert len(list(sdbm.predicate_objects(URIRef('http://ldf.fi/mmm/manifestation_singleton/bibale_007')))) > 1


class TestLinker(unittest.TestCase):
    test_csv = """PAYS,VILLE_ID MEDIUM,VILLE,ID_GEONAMES
Allemagne,5,Aachen,3247449
Suisse,120,Aarau,2661881
Italie,1551,Abbadia san Salvatore,3183581
France,652,Paris,2988507
"""

    extra_sdbm = """
        @prefix :      <https://sdbm.library.upenn.edu/> .
        @prefix wgs:   <http://www.w3.org/2003/01/geo/wgs84_pos#> .
        @prefix mmms: <http://ldf.fi/schema/mmm/> .
        @prefix dct:   <http://purl.org/dc/terms/> .
        @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix owl:   <http://www.w3.org/2002/07/owl#> .
        @prefix afn:   <http://jena.hpl.hp.com/ARQ/function#> .
        @prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
        @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix mmm:   <http://ldf.fi/mmm/> .
        @prefix ecrm:   <http://erlangen-crm.org/current/> .
        @prefix frbroo: <http://erlangen-crm.org/efrbroo/> .

        <http://ldf.fi/mmm/manifestation_singleton/18044>
            ecrm:P46i_forms_part_of <http://ldf.fi/mmm/source/sdbm_34056> .

        <http://ldf.fi/mmm/event/sdbm_source_observation_11348>
            a                           ecrm:E7_Activity ;
            ecrm:P4_has_time-span       <http://ldf.fi/mmm/time/sdbm_sources_19640000> ;
            ecrm:P70i_is_documented_in  <http://ldf.fi/mmm/source/sdbm_34056> ;
            ecrm:P7_took_place_at       <http://ldf.fi/mmm/place/2121> , <http://ldf.fi/mmm/place/1012> , <http://ldf.fi/mmm/place/847> ;
            mmms:carried_out_by_as_selling_agent
                    <http://ldf.fi/mmm/actor/sdbm_11674> ;
            mmms:data_provider_url      <https://sdbm.library.upenn.edu/entries/11348> ;
            mmms:had_sales_price        <http://ldf.fi/mmm/monetary_amounts/sdbm_11338> ;
            mmms:observed_manuscript    <http://ldf.fi/mmm/manifestation_singleton/18044> ;
            <http://purl.org/dc/terms/source>
                    mmms:SDBM ;
            skos:prefLabel              "15" .

    <http://ldf.fi/mmm/source/sdbm_34056>
            a       <http://ldf.fi/schema/mmm/Source> ;
            <http://ldf.fi/schema/mmm/data_provider_url>
                    <https://sdbm.library.upenn.edu/sources/34056> ;
            <http://ldf.fi/schema/mmm/source_agent>
                    <http://ldf.fi/mmm/actor/sdbm_11674> ;
            <http://ldf.fi/schema/mmm/source_date>
                    <http://ldf.fi/mmm/time/sdbm_sources_19640000> ;
            <http://ldf.fi/schema/mmm/source_location>
                    <http://ldf.fi/mmm/place/tgn_7004333> , <http://ldf.fi/mmm/place/tgn_7014456> , <http://ldf.fi/mmm/place/tgn_7003765> , <http://ldf.fi/mmm/place/tgn_7007567> ;
            <http://purl.org/dc/terms/source>
                    <http://ldf.fi/schema/mmm/SDBM> ;
            <http://www.w3.org/2004/02/skos/core#prefLabel>
                    "15" .

    <http://ldf.fi/mmm/time/sdbm_sources_19640000>
            a                             ecrm:E52_Time-Span ;
            ecrm:P82a_begin_of_the_begin  "1964-01-01"^^<http://www.w3.org/2001/XMLSchema#date> ;
            ecrm:P82b_end_of_the_end      "1964-12-31"^^<http://www.w3.org/2001/XMLSchema#date> ;
            <http://purl.org/dc/terms/source>
                    mmms:SDBM ;
            skos:prefLabel                "1964" .

    <http://ldf.fi/mmm/event/sdbm_actor_activity_8780>
            a                         mmms:PlaceNationality ;
            ecrm:P11_had_participant  <http://ldf.fi/mmm/actor/sdbm_11674> ;
            ecrm:P4_has_time-span     <http://ldf.fi/mmm/time/sdbm_actor_activity_timespan_8780> ;
            ecrm:P7_took_place_at     <http://ldf.fi/mmm/place/tgn_7003765> ;
            <http://purl.org/dc/terms/source>
                    <http://ldf.fi/schema/mmm/SDBM> ;
            <http://www.w3.org/2004/02/skos/core#prefLabel>
                    "Place/nationality activity event" .

    <http://ldf.fi/mmm/time/sdbm_actor_activity_timespan_8780>
            a                             ecrm:E52_Time-Span ;
            ecrm:P82a_begin_of_the_begin  "1949-01-01"^^<http://www.w3.org/2001/XMLSchema#date> ;
            ecrm:P82b_end_of_the_end      "1951-12-31"^^<http://www.w3.org/2001/XMLSchema#date> ;
            <http://purl.org/dc/terms/source>
                    <http://ldf.fi/schema/mmm/SDBM> ;
            <http://www.w3.org/2004/02/skos/core#prefLabel>
                    "1949 - 1951" .

    <http://ldf.fi/mmm/event/sdbm_actor_activity_3143>
            a                         mmms:PlaceNationality ;
            ecrm:P11_had_participant  <http://ldf.fi/mmm/actor/sdbm_11674> ;
            ecrm:P4_has_time-span     <http://ldf.fi/mmm/time/sdbm_actor_activity_timespan_3143> ;
            ecrm:P7_took_place_at     <http://ldf.fi/mmm/place/tgn_7004333> ;
            <http://purl.org/dc/terms/source>
                    <http://ldf.fi/schema/mmm/SDBM> ;
            <http://www.w3.org/2004/02/skos/core#prefLabel>
                    "Place/nationality activity event" .

    <http://ldf.fi/mmm/time/sdbm_actor_activity_timespan_3143>
            a                             ecrm:E52_Time-Span ;
            ecrm:P82a_begin_of_the_begin  "1920-01-01"^^<http://www.w3.org/2001/XMLSchema#date> ;
            ecrm:P82b_end_of_the_end      "1939-12-31"^^<http://www.w3.org/2001/XMLSchema#date> ;
            <http://purl.org/dc/terms/source>
                    <http://ldf.fi/schema/mmm/SDBM> ;
            <http://www.w3.org/2004/02/skos/core#prefLabel>
                    "1920 - 1939" .

    <http://ldf.fi/mmm/event/sdbm_actor_activity_8486>
            a                         mmms:PlaceNationality ;
            ecrm:P11_had_participant  <http://ldf.fi/mmm/actor/sdbm_11674> ;
            ecrm:P4_has_time-span     <http://ldf.fi/mmm/time/sdbm_actor_activity_timespan_8486> ;
            ecrm:P7_took_place_at     <http://ldf.fi/mmm/place/tgn_7007567> ;
            <http://purl.org/dc/terms/source>
                    <http://ldf.fi/schema/mmm/SDBM> ;
            <http://www.w3.org/2004/02/skos/core#prefLabel>
                    "Place/nationality activity event" .

    <http://ldf.fi/mmm/time/sdbm_actor_activity_timespan_8486>
            a                             ecrm:E52_Time-Span ;
            ecrm:P82a_begin_of_the_begin  "1951-01-01"^^<http://www.w3.org/2001/XMLSchema#date> ;
            ecrm:P82b_end_of_the_end      "1970-12-31"^^<http://www.w3.org/2001/XMLSchema#date> ;
            <http://purl.org/dc/terms/source>
                    <http://ldf.fi/schema/mmm/SDBM> ;
            <http://www.w3.org/2004/02/skos/core#prefLabel>
                    "1951 - 1970" .
    """

    test_sdbm_data = TestLinkerSDBM.test_sdbm_data + TestManuscriptLinking.test_sdbm + extra_sdbm
    test_bodley_data = TestLinkerBodley.test_bodley_data
    test_bibale_data = '''
    @prefix mmms: <http://ldf.fi/schema/mmm/> .
    @prefix dct:   <http://purl.org/dc/terms/> .
    @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix owl:   <http://www.w3.org/2002/07/owl#> .
    @prefix afn:   <http://jena.hpl.hp.com/ARQ/function#> .
    @prefix frbroo2: <http://www.cidoc-crm.org/frbroo/> .
    @prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
    @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix mmm:   <http://ldf.fi/mmm/> .
    @prefix frbroo: <http://erlangen-crm.org/efrbroo/> .
    @prefix ecrm:   <http://erlangen-crm.org/current/> .
    @prefix bibale: <http://bibale.irht.cnrs.fr/> .

    <http://ldf.fi/mmm/manifestation_singleton/bibale_11267>
        a                        frbroo:F4_Manifestation_Singleton ;
        dct:source               mmms:Bibale ;
        skos:prefLabel           "PARIS, Bibliothèque nationale de France, Manuscrits, ital. 2080" .

    '''

    def test_get_last_known_locations(self):
        bib = Graph()
        bib.parse(data=self.test_bibale_data, format='turtle')
        bod = Graph()
        bod.parse(data=self.test_bodley_data, format='turtle')
        sdbm = Graph()
        sdbm.parse(data=self.test_sdbm_data, format='turtle')

        GEONAMES_APIKEYS = [os.environ['GEONAMES_KEY']]
        linker = PlaceLinker(GEONAMES_APIKEYS)

        bib, bod, sdbm = get_last_known_locations(bib, bod, sdbm, linker, csv=StringIO(self.test_csv))

        self.assertEqual(len(list(bib.triples((None, MMMS.last_known_location_bibale, None)))), 1)
        self.assertEqual(len(list(bod.triples((None, MMMS.last_known_location_bodley, None)))), 1)
        self.assertEqual(len(list(sdbm.triples((None, MMMS.last_known_location_sdbm, None)))), 1)
        self.assertEqual(len(list(sdbm.triples((None, MMMS.last_known_location, None)))), 3)
