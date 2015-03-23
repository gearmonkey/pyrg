#!/usr/bin/env python
# encoding: utf-8
"""
user.py

Created by Benjamin Fields on 2014-02-11.
Copyright (c) 2014 . All rights reserved.
"""

import sys
import os
import unittest
import requests
import logging
from bs4 import BeautifulSoup


class song:
    def __init__(self, rg_url=None, rg_id=None, retrieve_metadata=False):
        self.host = "http://genius.com"
        self.rg_url = rg_url
        self.rg_id = rg_id
        if self.rg_url == None and self.rg_id == None:
            raise ValueError("Must give either a song url or song id at initialisation")
        self.tags = None
        self.category = None
        self.artist = None
        self.title = None
        self.document_type = None
        self.featuring = None
        self.producers = None
        if retrieve_metadata:
            self.get_metadata()

    def get_metadata(self):
        '''Collect the annotations of the user, is cap is given, only collect the most recent ones, otherwise fetch all (requires <Number of annotations>/10 calls)'''
        if self.rg_url != None:
            page = self.host + self.rg_url
        elif self.rg_id != None:
            page = self.host+'/songs/'+self.rg_id
        r = requests.get(page)
        soup = BeautifulSoup(r.content)
        try:
            self.category = soup.find('div', id="beefy_header")['class'][0]
        except Exception, err:
            logging.warning('unable to scrape category for %s.Msg: %s'%(page, err))
        try:
            self.tags = map(lambda t:(t.text, t['href']), soup.select('p.tags a'))
        except Exception, err:
            logging.warning('unable to scrape tags for %s.Msg: %s'%(page, err))
        try:
            self.title = soup.find('span', class_='text_title').text.strip()
        except Exception, err:
            logging.warning('unable to scrape title for %s.Msg: %s'%(page, err))
        try:
            self.artist = soup.find('span', class_='text_artist').text.strip()
        except Exception, err:
            logging.warning('unable to scrape artist name for %s.Msg: %s'%(page, err))
        try:
            self.document_type = soup.find('span', class_='text_type').text.strip()
        except Exception, err:
            logging.warning('unable to scrape doc type for %s.Msg: %s'%(page, err))
        try:
            self.featuring = map(lambda a:(a.text, a['href']), soup.select('span.featured_artists a'))
        except Exception, err:
            logging.warning('unable to scrape featured artists for %s.Msg: %s'%(page, err))
        try:
            self.producers = map(lambda a:(a.text, a['href']), soup.select('span.producer_artists a'))
        except Exception, err:
            logging.warning('unable to scrape producers for %s.Msg: %s'%(page, err))


class userTests(unittest.TestCase):
    def setUp(self):
        pass


if __name__ == '__main__':
    unittest.main()
