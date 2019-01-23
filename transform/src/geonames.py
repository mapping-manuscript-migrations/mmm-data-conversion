#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-
"""Linking Bibale places"""

import logging

import os
from time import sleep

import geocoder

import pycountry


class GeoNamesAPI:
    """
    GeoNames querying with geocoder library and API key switching when needed
    """

    def __init__(self, apikeys: list):
        self.apikey_index = 0
        self.apikeys = apikeys

        self.log = logging.getLogger(__name__)

    def _query(self, q, **kwargs):
        """Query GeoNames, change API key if hourly limit reached for current key, """
        g = None

        while (not hasattr(g, 'status')) or ('Read timed out' in g.status) or ('hourly limit' in g.status):
            g = geocoder.geonames(q, **kwargs, key=self.get_apikey())
            if 'hourly limit' in g.status:
                self.change_apikey()
                if self.apikey_index == 0:
                    self.log.info('Hourly limit reached for all keys, waiting for 10 minutes')
                    sleep(60 * 10)

        return g

    def get_apikey(self):
        return self.apikeys[self.apikey_index]

    def change_apikey(self):
        self.apikey_index = (self.apikey_index + 1) % len(self.apikeys)
        self.log.info('Changed to GeoNames API key %s' % (self.get_apikey()))

    def get_place_data(self, geonames_id: str):
        """Fetch data from GeoNames API based on GeoNames ID"""
        if not geonames_id:
            return {}

        self.log.info('Fetching data for GeoNames id %s' % geonames_id)
        g = self._query(geonames_id, method='details')

        if (not g) or g.status != 'OK':
            return {}

        wikipedia = ('https://' + g.wikipedia) if hasattr(g, 'wikipedia') and g.wikipedia else None

        return {'lat': g.lat,
                'lon': g.lng,
                'feature_class': g.feature_class,
                'class_description': g.class_description,
                'wikipedia': wikipedia,
                'address': g.address,
                'adm1': g.state,
                'country': g.country,
                'name': g.address,
                'id': g.geonames_id
                }

    def search_country(self, country: str):
        """
        Search for a country in any language and return it's English label

        >>> geo = GeoNamesAPI([os.environ['GEONAMES_KEY']])
        >>> geo.search_country('Allemagne')
        'Germany'
        >>> geo.search_country('Foo') is None
        True
        """

        g = self._query(country)

        if (not g) or g.address != g.country:
            # Received None or a too specific place, ignore it
            self.log.info('Country not found for %s' % country)
            return None

        return g.country

    def _usa_state(self, place: str):
        """
        Handle case 'USA (state name)'

        >>> geo = GeoNamesAPI([os.environ['GEONAMES_KEY']])
        >>> geo._usa_state('USA (CALIFORNIE)')
        ('United States', 'Californie')
        >>> geo._usa_state('USA (NEW YORK)')
        ('United States', 'New York')
        """
        country = 'United States'
        region = place.split('(')[-1].strip(' ()').title()

        return country, region

    def search_place(self, country: str, region: str, settlement: str):
        """
        Search for a place from GeoNames API and return place data

        >>> geo = GeoNamesAPI([os.environ['GEONAMES_KEY']])
        >>> geo.search_place('Royaume Uni / Angleterre',  'Dorset', 'Abbotsbury').get('wikipedia')
        'https://en.wikipedia.org/wiki/Abbotsbury'
        """
        country_mapping = {
            "états-unis": "United States",
            "royaume uni / angleterre": "United Kingdom",
            "royaume uni / ecosse": "United Kingdom",
            "royaume uni / irlande du nord": "United Kingdom",
            "royaume uni / pays de galles": "United Kingdom",
            "russie": "Russian Federation",
            "vatican": "Holy See (Vatican City State)",
        }

        region_mapping = {
            'Indéterminée': '',
            'Picardie': 'Hauts-de-France',
        }

        region = region_mapping.get(region, region)

        if (not region) or (not settlement):
            self.log.info('Place search with lacking information: %s - %s' % (country, region or settlement or ''))

        if country.startswith('USA (') and not region:
            country, region = self._usa_state(country)

        country_en = country_mapping.get(country.lower()) or self.search_country(country)

        kw_params = dict(featureClass=['A', 'P'])
        if country_en:
            q = '%s %s' % (region, settlement)
            pyc = pycountry.countries.get(name=country_en)
            if not pyc:
                self.log.warning('Country not found in pycountry: %s' % country_en)
            kw_params['country'] = pyc.alpha_2 if pyc else country_en
        else:
            q = '%s %s %s' % (country, region, settlement)

        g = self._query(q, **kw_params)

        return self.get_place_data(g.geonames_id) if g else None


