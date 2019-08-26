'''
Created on 30 Apr 2019

@author: petrileskinen
'''

import os
import pprint
import logging
import unittest
from io import StringIO

from datetime import date
from rdflib import URIRef, RDF, RDFS, OWL, Literal
from linker_people import PersonLinker, read_recon_links

# from linker import PlaceLinker
from manuscripts import read_manual_links, link_by_shelfmark, link_manuscripts, change_resource_uri
from mmm import get_mmm_resource_uri
from namespaces import *

log = logging.getLogger(__name__)

"""TODO : multiple births and deaths ?
"""


class TestStringMethods(unittest.TestCase):
    def test_person_linkage(self):
        bib = self.read_example_data(self.test_bibale)
        bod = self.read_example_data(self.test_bodley)
        sdbm = self.read_example_data(self.test_sdbm)

        p = PersonLinker(sdbm, bod, bib)

        p.find_viaf_links()
        p.link_people()

        #    test that all link tuples have two non-None elements
        for link in p.links:
            self.assertEqual(len(list(filter(lambda x: x is not None, list(link)))), 2)

        bib, bod, sdbm = p.datasets()

        """ # test saving the graph
        if False:
            oput = str(sdbm.serialize(format='turtle'))
            print(oput.replace("\\n","\n"))

            oput = str(bod.serialize(format='turtle'))
            print(oput.replace("\\n","\n"))

            oput = str(bib.serialize(format='turtle'))
            print(oput.replace("\\n","\n"))
        else:
            oput = str((sdbm+bod+bib).serialize(format='turtle'))
            print(oput.replace("\\n","\n"))
        """

        person = URIRef('http://ldf.fi/mmm/actor/bodley_person_88626271')
        self.assertTrue(len(list(bod.triples((person, SKOS.prefLabel, None)))) < 2)

        person_xyz = URIRef('http://ldf.fi/mmm/actor/bibale_person_XYZ')
        self.assertIsNone(bib.value(person_xyz, SKOS.prefLabel))
        self.assertIsNone(sdbm.value(URIRef('http://ldf.fi/mmm/actor/sdbm_xyz'), SKOS.prefLabel))

        self.assertEqual(str(bod.value(URIRef('http://ldf.fi/mmm/actor/bodley_person_88626271'), SKOS.prefLabel)),
                         "Herodianus, pseudo")
        self.assertEqual(str(bib.value(URIRef('http://ldf.fi/mmm/actor/bodley_person_88626271'), SKOS.prefLabel)),
                         "Herodianus, pseudo")
        self.assertEqual(str(sdbm.value(URIRef('http://ldf.fi/mmm/actor/bodley_person_88626271'), SKOS.prefLabel)),
                         "Herodianus, pseudo")

        #    test that unique entry is not linked:
        self.assertEqual(str(bib.value(URIRef('http://ldf.fi/mmm/actor/bibale_person_unique'), OWL.sameAs)),
                         "https://viaf.org/viaf/123unique")

        #    test that places are not linked:
        self.assertEqual(sdbm.value(URIRef('http://ldf.fi/mmm/actor/sdbm_nowhere'), RDF.type), MMMS.Place)
        self.assertEqual(bib.value(URIRef('http://ldf.fi/mmm/actor/bibale_nowhere'), RDF.type), MMMS.Place)
        self.assertEqual(bib.value(URIRef('http://ldf.fi/mmm/actor/bibale_nobody'), RDF.type), CRM.E21_Person)

    def test_recon_links(self):
        bib = self.read_example_data(self.test_bibale)
        bod = self.read_example_data(self.test_bodley)
        sdbm = self.read_example_data(self.test_sdbm)

        p = PersonLinker(sdbm, bod, bib)

        # p.find_viaf_links()
        p.links += read_recon_links(bib, bod, sdbm, StringIO(self.test_csv), date(2019, 6, 13))
        p.link_people()

        assert len(p.links) == 1
        assert p.links[0] == (URIRef('http://ldf.fi/mmm/actor/bibale_30530'),
                                  None,
                                  URIRef('http://ldf.fi/mmm/actor/sdbm_13159')), p.links

    def test_linking_process(self):
        bib = self.read_example_data(self.test_bibale)
        bod = self.read_example_data(self.test_bodley)
        sdbm = self.read_example_data(self.test_sdbm)

        p = PersonLinker(sdbm, bod, bib, recon_file_path=None)
        p.link()

    def read_example_data(self, data):
        g = Graph()
        g.parse(data=self.test_prefices + data, format='turtle')
        return g

    test_csv = """Name,Match,Notes,Birth_time,Death_time,Gender,URI,Databases
Yorkshire Archaeological Society,,,,,,http://ldf.fi/mmm/actor/sdbm_11161,SDBM
Yolande de Bar,,,,,female,http://ldf.fi/mmm/actor/bibale_2013,Bibale
"Yéméniz, Nicolas (1783-1871)",http://ldf.fi/mmm/actor/sdbm_13159,,precise 1783,precise 1871,male,http://ldf.fi/mmm/actor/bibale_30530,Bibale
"""

    #    test data produced with query http://yasgui.org/short/QNXAjx5qr
    test_prefices = """
    @prefix wgs:   <http://www.w3.org/2003/01/geo/wgs84_pos#> .
    @prefix dct:   <http://purl.org/dc/terms/> .
    @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix mmms:  <http://ldf.fi/mmm/schema/> .
    @prefix owl:   <http://www.w3.org/2002/07/owl#> .
    @prefix ecrm:  <http://erlangen-crm.org/current/> .
    @prefix mmma:  <http://ldf.fi/mmm/actor/> .
    @prefix afn:   <http://jena.hpl.hp.com/ARQ/function#> .
    @prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
    @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix mmm:   <http://ldf.fi/mmm/> .
    @prefix frbroo: <http://erlangen-crm.org/efrbroo/> .
    @prefix viaf:  <https://viaf.org/viaf/> .
    """

    test_sdbm = """
mmma:sdbm_1002  a               ecrm:E21_Person ;
        mmms:data_provider_url  <https://sdbm.library.upenn.edu/names/1002> ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:285172151 ;
        skos:prefLabel          "Simon de Hesdin" .

mmma:sdbm_1008  a               ecrm:E21_Person ;
        mmms:birth_date         "490" ;
        mmms:data_provider_url  <https://sdbm.library.upenn.edu/names/1008> ;
        mmms:death_date         "0560-01-01" ;
        mmms:person_place       <http://ldf.fi/mmm/place/tgn_7024407> , <http://ldf.fi/mmm/place/tgn_1000074> ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:71399875 ;
        skos:prefLabel          "Simplicius, of Cilicia" .

mmma:sdbm_1011  a               ecrm:E39_Actor ;
        mmms:birth_date         "1414-07-21" ;
        mmms:data_provider_url  <https://sdbm.library.upenn.edu/names/1011> ;
        mmms:death_date         "1484-08-13" ;
        mmms:person_place       <http://ldf.fi/mmm/place/tgn_7001168> , <http://ldf.fi/mmm/place/tgn_1000080> ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:37712552 ;
        skos:prefLabel          "Sixtus IV, Pope, 1414-1484" .

mmma:sdbm_xyz
        a                       ecrm:E21_Person ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_76393969> ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:88626271 ;
        skos:altLabel           "Herodianos, Sohn des Apollonios Dyskolos, ca. 2. Jh." , "Herodianos, Grammatiker, ca. 2. Jh." , "Herodianus, Rhetor, ca. 2. Jh." , "Herodianos, Ailios, ca. 2. Jh." , "Herodianos, Technikos, ca. 2. Jh." , "Hérodien, dÁlexandrie, ca. 2. Jh." , "Herodianus, Aelius, active 2nd century" , "Herodianus, Grammaticus, ca. 2. Jh." , "Herodianos, von Alexandreia, ca. 2. Jh." , "Herodianus, Romanus, ca. 2. Jh." , "Herodianus, Alexandrinus, ca. 2. Jh." , "Herodianus, Technicus, ca. 2. Jh." , "Pseudo-Herodianus, ca. 2. Jh." , "Aelius, Herodianus, ca. 2. Jh." , "Herodian, von Alexandreia, ca. 2. Jh." ;
        skos:prefLabel          "Herodianus, Aelius, active 2nd century" .

mmma:sdbm_101  a                ecrm:E21_Person ;
        mmms:birth_date         "1141" ;
        mmms:data_provider_url  <https://sdbm.library.upenn.edu/names/101> ;
        mmms:death_date         "1210" ;
        mmms:person_place       <http://ldf.fi/mmm/place/tgn_7008653> ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:61906944 ;
        skos:prefLabel          "Gervase, of Canterbury, approximately 1141-approximately 1210" .

mmma:sdbm_1001  a               ecrm:E21_Person ;
        mmms:birth_date         "26" ;
        mmms:data_provider_url  <https://sdbm.library.upenn.edu/names/1001> ;
        mmms:death_date         "101" ;
        mmms:person_place       <http://ldf.fi/mmm/place/tgn_1000080> , <http://ldf.fi/mmm/place/tgn_7000874> ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:27071645 ;
        skos:prefLabel          "Silius Italicus, Tiberius Catius" .

mmma:sdbm_1007  a               ecrm:E21_Person ;
        mmms:birth_date         "1285" ;
        mmms:data_provider_url  <https://sdbm.library.upenn.edu/names/1007> ;
        mmms:death_date         "1348-02-02" ;
        mmms:person_place       <http://ldf.fi/mmm/place/tgn_1000080> ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:4472713 ;
        skos:prefLabel          "Simone Fidati da Cascia, -1348 " .

mmma:sdbm_nowhere  a               mmms:Place ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:nowhere ;
        skos:prefLabel          "Nowhere" .
    """

    test_bodley = """
    mmma:bodley_person_4472713
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_4472713_death ;
        ecrm:P98i_was_born      mmma:bodley_person_4472713_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_4472713> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              <http://www.wikidata.org/entity/Q2384461> , viaf:4472713 , <http://www.idref.fr/092125611/id> ;
        skos:altLabel           "Simone, Fidati, -1348" , "Cascia, Simon Fidati von, -1348" , "Simon, Cassianus, -1348" , "Cassia OESA, Simon Fidati de, -1348" , "Simon Fidati, de Cassia, -1348" , "Simon, Fidati von Cascia, -1348" , "Fidati, Simone, -1348" , "Simon aus Cascia, -1348" , "Simon Fidati, de Cassia OESA, -1348" , "Cascia, Simone Fidati da, -1348" , "Fidati, Simon, -1348" , "Simon, von Cascia, -1348" , "Simon, da Cascia, -1348" , "Simon, de Cassia, -1348" , "Fidati da Cascia, Simone, -1348" , "Fidato, Simon, -1348" , "Cassia, Simon de, -1348" , "Cassia, Simon Fidati de, -1348" ;
        skos:prefLabel          "Fidati, Simone, -1348" .

mmma:bodley_person_61906944
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_61906944_death ;
        ecrm:P98i_was_born      mmma:bodley_person_61906944_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_61906944> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              <http://d-nb.info/gnd/10094275X> , <http://www.idref.fr/033568448/id> , viaf:61906944 , <http://id.loc.gov/authorities/names/n00032584> , <http://www.wikidata.org/entity/Q3104436> ;
        skos:altLabel           "Gervasius, Dorobernensis, 1141-1210" , "Gervasius, Dorobornensis, 1141-1210" , "Gervasius, von Canterbury, 1141-1210" , "Gervais, Jean, 1141-1210" , "Gervase, of Canterbury, 1141-1210" , "Gervais, de Cantorbury, 1141-1210" , "Gervasius, Cantuariensis, 1141-1210" , "Gervais, de Cantorbéry, 1141-1210" , "Gervasius, Cantabrigensis, 1141-1210" , "Gervase, of Canterbury, approximately 1141-approximately 1210" ;
        skos:prefLabel          "Gervase, of Canterbury, approximately 1141-approximately 1210" .

mmma:bodley_person_32352720
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_32352720_death ;
        ecrm:P98i_was_born      mmma:bodley_person_32352720_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_32352720> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              <http://www.wikidata.org/entity/Q7520146> , viaf:32352720 , <http://catalogue.bnf.fr/ark:/12148/cb123420577> , <http://id.loc.gov/authorities/names/n85125976> ;
        skos:altLabel           "Simon, Anglicus, -1306" , "Simon, Favershamensis, -1306" , "Simon, of Faversham, d. 1306" , "Simon, of Faversham, -1306" , "Simon, de Faverisham, -1306" , "Faversham, Simon of, -1306" ;
        skos:prefLabel          "Simon, of Faversham, -1306" .

mmma:bodley_person_27071645
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_27071645_death ;
        ecrm:P98i_was_born      mmma:bodley_person_27071645_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_27071645> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              <http://d-nb.info/gnd/118614347> , <http://www.wikidata.org/entity/Q316123> , <http://www.idref.fr/027138143/id> , viaf:27071645 , <http://catalogue.bnf.fr/ark:/12148/cb11924756s> , <http://id.loc.gov/authorities/names/n79120267> ;
        skos:altLabel           "Silius Italicus, Gaius, 26-101" , "Italicus, Tiberius Catius Asconius, 26-101" , "Silius Italicus, Catius, 26-101" , "Silius, Italicus, 26-101" , "Silius Italicus, Tiberius Catius" , "Sillius Italicus, Cajus, 26-101" , "Italicus, Tiberius, 26-101" , "Italicus, Tiberius Catius Asconius Silius, 26-101" , "Syllius Italicus, Gaius, 26-101" , "Italicus, Silius, 26-101" , "Silio Italico, Cajo, 26-101" , "Italicus, Sillius, 26-101" , "Sillius, Italicus, 26-101" , "Silius Italicus, Titus C., 26-101" , "Silio, Italico, 26-101" , "Silius Italicus, Cajus, 26-101" , "Catius Asconius Silius Italicus, Tiberius, 26-101" , "Silius, Tiberius Catius, 26-101" , "Italicus, Cajus S., 26-101" , "Silius Italicus, Caius, 26-101" , "Silius Italicus, Tiberius C., 26-101" , "Silius Italicus, Tiberius Catius, 26-101" , "Silius Italicus, Titus Catius, 26-101" , "Silio, 26-101" , "Asconius Silius Italicus, Tiberius Catius, 26-101" , "Sylius Italicus, Gaius, 26-101" , "Tiberius Catius Asconius Silius, Italicus, 26-101" , "Silius, 26-101" , "Silius, Gaius, 26-101" , "Italicus, Caius S., 26-101" , "Silius, Epicus, 26-101" , "Italicus, Tiberius Catius, 26-101" , "Tiberius Catius Asconius Silius, 26-101" , "Italicus, Tiberius Catius Silius, 26-101" , "Italicus, Tiberius C., 26-101" ;
        skos:prefLabel          "Silius Italicus, Tiberius Catius" .

mmma:bodley_person_88626271
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_88626271_death ;
        ecrm:P98i_was_born      mmma:bodley_person_88626271_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_88626271> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              <http://catalogue.bnf.fr/ark:/12148/cb12361935k> , <http://www.idref.fr/032625073/id> , <http://id.loc.gov/authorities/names/no2011029666> , viaf:88626271 , <http://www.wikidata.org/entity/Q380826> ;
        skos:altLabel           "Herodianus, pseudo" , "Pseudo-Herodianus" , "Pseudo-Herodian" , "Ps.-Herodian" ;
        skos:prefLabel          "Herodianus, pseudo" .

mmma:bodley_person_310715648
        a                       ecrm:E21_Person ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_310715648> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              viaf:310715648 , viaf:20072061 , <http://id.loc.gov/authorities/names/n2014188541> , <http://d-nb.info/gnd/102515735> ;
        skos:altLabel           "Philippus, Clericus Tripolitanus, ca. 1243" , "Tripolitanus, Philippus" , "Philippus, Tripolitanus" , "Philip, of Tripoli, fl. 1243" ;
        skos:prefLabel          "Philip, of Tripoli, fl. 1243" .

mmma:bodley_person_37712552
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_37712552_death ;
        ecrm:P98i_was_born      mmma:bodley_person_37712552_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_37712552> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              <http://catalogue.bnf.fr/ark:/12148/cb12372622v> , <http://d-nb.info/gnd/118797476> , <http://id.loc.gov/authorities/names/n86044822> , <http://www.wikidata.org/entity/Q163514> , <http://www.idref.fr/032758545/id> , viaf:37712552 ;
        skos:altLabel           "Sixte, IV., Pape, 1414-1484" , "Sisto IV, Papst, 1414-1484" , "Sixtus, IV., Pape, 1414-1484" , "Sixtus, IV, Pope, 1414-1484" , "Rovere, Francesco della, 1414-1484" , "Sixtus, IV, Papa, 1414-1484" , "Albescola della Rovere, Francesco d', 1414-1484" , "Della Rovere, Francesco, 1414-1484" , "Franciscus, de Rovere, 1414-1484" , "Sisto, Pope, 4, 1414-1484" , "Sisto, IV, Papst, 1414-1484" , "Xystus, IV., Papa, 1414-1484" , "Rovere, Francesco della, Pape, 4, 1414-1484" , "Francesco, di Savona, 1414-1484" , "Sisto, Papst, 4, 1414-1484" , "Sixtus, Episcopus, 1414-1484" , "Sisto IV, Pape, 1414-1484" , "Della Rovere, Francesco d'Albescola, 1414-1484" , "Della Rovere, Francesco, Papst, 4, 1414-1484" , "Sixtus, Papst, 4, 1414-1484" , "Sixtus, IV., Pope, 1414-1484" , "DellaRovere, Francesco d'Albescola, 1414-1484" , "Rovere, Francesco della, Papst, 4, 1414-1484" , "Sixtus, IV, Papst, 1414-1484" , "Francesco, della Rovere, 1414-1484" , "François, delle Rovere, 1414-1484" , "Sisto IV, Pope, 1414-1484" , "Della Rovere, Francesco, Pape, 4, 1414-1484" , "Sisto, Pape, 4, 1414-1484" , "Rovere, Francesco della, Pope, 4, 1414-1484" , "Della Rovere, Francesco, Pope, 4, 1414-1484" , "Sisto, IV., Papa, 1414-1484" , "DellaRovere, Francesco, 1414-1484" , "Sixtus, 4, Papa, 1414-1484" , "Rovere, Francesco d'Albescola della, 1414-1484" , "Sixtus, IV., Papa, 1414-1484" , "Sixtus, IV., Pontifex Maximus, 1414-1484" ;
        skos:prefLabel          "Sixtus, IV, Pope, 1414-1484" .

mmma:bodley_person_20072061
        a                       ecrm:E21_Person ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_20072061> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              viaf:20072061 , <http://d-nb.info/gnd/102515735> ;
        skos:altLabel           "Tripolitanus, Philippus, ca. 1243" , "Philippus, Tripolitanus, ca. 1243" , "Philippus, Clericus Tripolitanus, ca. 1243" ;
        skos:prefLabel          "Philippus, Tripolitanus, ca. 1243" .

mmma:sdbm_1004  a               ecrm:E21_Person ;
        mmms:birth_date         "1260" ;
        mmms:data_provider_url  <https://sdbm.library.upenn.edu/names/1004> ;
        mmms:death_date         "1306" ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:32352720 ;
        skos:prefLabel          "Simon, of Faversham, -1306" .

mmma:bodley_person_285172151
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_285172151_death ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_285172151> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              <http://d-nb.info/gnd/104150823> , viaf:283616028 , viaf:12145541705296601293 , <http://catalogue.bnf.fr/ark:/12148/cb16844263m> , viaf:285172151 ;
        skos:altLabel           "Hesdin, Simon de, -1383" ;
        skos:prefLabel          "Hesdin, Simon de, -1383" .

mmma:sdbm_1003  a               ecrm:E21_Person ;
        mmms:birth_date         "1270" ;
        mmms:data_provider_url  <https://sdbm.library.upenn.edu/names/1003> ;
        mmms:death_date         "1303" ;
        mmms:person_place       <http://ldf.fi/mmm/place/tgn_1000080> ;
        dct:source              mmms:SDBM ;
        owl:sameAs              viaf:165124171 ;
        skos:prefLabel          "Simon, of Genoa, active 13th century " .

mmma:bodley_person_71399875
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_71399875_death ;
        ecrm:P98i_was_born      mmma:bodley_person_71399875_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_71399875> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              viaf:71399875 , <http://id.loc.gov/authorities/names/n82102480> , <http://www.idref.fr/02790850X/id> , <http://d-nb.info/gnd/118642421> , <http://catalogue.bnf.fr/ark:/12148/cb11984924z> , <http://www.wikidata.org/entity/Q351518> ;
        skos:altLabel           "Pseudo-Simplicius, ca. 6.Jh." , "Simplicius, Pseudo-, ca. 6.Jh." , "Simplicius, Neuplatoniker, ca. 6.Jh." , "Simplicius, Neapolitanus, ca. 6.Jh." , "Simplicius, Neoplatonicus, ca. 6.Jh." , "Simplicius, de Cilicia, ca. 6.Jh." , "Simplicius, Atheniensis, ca. 6.Jh." , "Cilicius, Simplicius, ca. 6.Jh." , "Simplicius, Philosoph, ca. 6.Jh." , "Simplicius, Aristotelicus, ca. 6.Jh." , "Simplicius, ca. 6.Jh." , "Simplicius, Perepateticus, ca. 6.Jh." , "Simplicius, of Cilicia, ca. 6.Jh." , "Simplicius, of Cilicia" , "Simplicio, ca. 6.Jh." , "Simplicius, Philosophus, ca. 6.Jh." , "Simplicius, aus Kilikien, ca. 6.Jh." , "Simplikios, ca. 6.Jh." , "Simplikios, von Kilikien, ca. 6.Jh." , "Simplicius, Peripateticus, ca. 6.Jh." ;
        skos:prefLabel          "Simplicius, of Cilicia" .

mmma:bodley_person_165124171
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_165124171_death ;
        ecrm:P98i_was_born      mmma:bodley_person_165124171_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_165124171> ;
        dct:source              mmms:Bodley ;
        owl:sameAs              viaf:165124171 ;
        skos:altLabel           "Cordo, Simone, -1300" ;
        skos:prefLabel          "Cordo, Simone, -1300" .

    """

    test_bibale = """
    mmma:bibale_person_4472713
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_4472713_death ;
        ecrm:P98i_was_born      mmma:bodley_person_4472713_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_4472713> ;
        dct:source              mmms:Bibale ;
        owl:sameAs              viaf:NO_LINK ;
        skos:altLabel           "Simone, Fidati, -1348" , "Cascia, Simon Fidati von, -1348" , "Simon, Cassianus, -1348" , "Cassia OESA, Simon Fidati de, -1348" , "Simon Fidati, de Cassia, -1348" , "Simon, Fidati von Cascia, -1348" , "Fidati, Simone, -1348" , "Simon aus Cascia, -1348" , "Simon Fidati, de Cassia OESA, -1348" , "Cascia, Simone Fidati da, -1348" , "Fidati, Simon, -1348" , "Simon, von Cascia, -1348" , "Simon, da Cascia, -1348" , "Simon, de Cassia, -1348" , "Fidati da Cascia, Simone, -1348" , "Fidato, Simon, -1348" , "Cassia, Simon de, -1348" , "Cassia, Simon Fidati de, -1348" ;
        skos:prefLabel          "Fidati, Simone, -1348" .

    mmma:bibale_person_XYZ
        a                       ecrm:E21_Person ;
        ecrm:P100i_died_in      mmma:bodley_person_76393969_death ;
        ecrm:P98i_was_born      mmma:bodley_person_76393969_birth ;
        mmms:data_provider_url  <https://medieval.bodleian.ox.ac.uk/catalog/person_76393969> ;
        dct:source              mmms:Bibale ;
        owl:sameAs              viaf:88626271 ;
        skos:prefLabel          "Herodianos, Sohn des Apollonios Dyskolos, ca. 2. Jh." .

    mmma:bibale_person_unique
        a                       ecrm:E39_Actor ;
        dct:source              mmms:Bibale ;
        owl:sameAs              viaf:123unique ;
        skos:prefLabel          "unique" .

    mmma:bibale_nowhere  a               mmms:Place ;
        dct:source              mmms:Bibale ;
        owl:sameAs              viaf:nowhere ;
        skos:prefLabel          "In the middle of Nothing and Nowhere" .

    mmma:bibale_nobody  a               ecrm:E21_Person ;
        dct:source              mmms:Bibale ;
        owl:sameAs              viaf:nowhere ;
        skos:prefLabel          "Nobody" .

        """

    def get_mmm_resource_uri(self):
        bib = self.read_example_data(self.test_bibale)
        bod = self.read_example_data(self.test_bodley)
        sdbm = self.read_example_data(self.test_sdbm)

        self.assertEqual(get_mmm_resource_uri(bib, bod, sdbm, URIRef('http://ldf.fi/mmm/actor/bibale_person_XYZ')),
                         URIRef('http://ldf.fi/mmm/actor/bibale_person_XYZ'))

        sdbm.add((URIRef('http://ldf.fi/mmm/actor/bibale_person_XYZ'), OWL.sameAs,
                  URIRef('http://ldf.fi/mmm/actor/bodley_person_165124171')))

        self.assertEqual(get_mmm_resource_uri(bib, bod, sdbm, URIRef('http://ldf.fi/mmm/actor/bibale_person_XYZ')),
                         URIRef('http://ldf.fi/mmm/actor/bodley_person_165124171'))


if __name__ == '__main__':
    unittest.main()
