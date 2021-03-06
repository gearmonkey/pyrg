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


class song(object):
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
        self.lyrics = None
        self.annotations = []
        if retrieve_metadata:
            self.get_metadata()

    def __str__(self):
        if self.artist != None and self.title != None:
            return "%s by %s"%(self.title, self.artist)
        else:
            return repr(self)

    def get_metadata(self):
        '''Collect metadata for a song'''
        if self.rg_url != None:
            page = self.host + self.rg_url
        elif self.rg_id != None:
            page = self.host+'/songs/'+self.rg_id
        r = requests.get(page)
        soup = BeautifulSoup(r.content)
        if self.rg_id == None:
            try:
                self.rg_id = soup.find('meta', attrs={"property":"twitter:app:url:iphone"})['content'].split('/')[-1]
            except Exception, err:
                logging.warning('unable to scrape id for %s.Msg: %s', page, err)
        if self.rg_url == None:
            try:
                self.rg_url = soup.find('meta', attrs={"property":"og:url"})['content']
            except Exception, err:
                logging.warning('unable to scrape url for %s.Msg: %s', page, err)
        try:
            self.category = soup.find('div', id="beefy_header")['class'][0]
        except Exception, err:
            logging.warning('unable to scrape category for %s.Msg: %s', page, err)
        try:
            self.tags = map(lambda t:(t.text, t['href']), soup.select('p.tags a'))
        except Exception, err:
            logging.warning('unable to scrape tags for %s.Msg: %s', page, err)
        try:
            self.title = soup.find('h1', class_='song_header-primary_info-title').text.strip()
        except Exception, err:
            logging.warning('unable to scrape title for %s.Msg: %s', page, err)
        try:
            self.artist = soup.find('a', class_='song_header-primary_info-primary_artist').text.strip()
        except Exception, err:
            logging.warning('unable to scrape artist name for %s.Msg: %s', page, err)
        try:
            self.document_type = soup.find('span', class_='text_type').text.strip()
        except Exception, err:
            logging.warning('unable to scrape doc type for %s.Msg: %s', page, err)
        try:
            self.featuring = map(lambda a:(a.text, a['href']), soup.find("additional-artists", attrs={'label':'Featuring'}).find_all('a'))
        except Exception, err:
            logging.warning('unable to scrape featured artists for %s.Msg: %s', page, err)
        try:
            self.producers = map(lambda a:(a.text, a['href']), soup.find("additional-artists", attrs={'label':'Produced By'}).find_all('a'))
        except Exception, err:
            logging.warning('unable to scrape producers for %s.Msg: %s', page, err)
        try:
            self.lyrics = soup.select("div.song_body-lyrics")[0].lyrics.text
        except Exception, err:
            logging.warning('unable to scrape lyrics for %s.Msg: %s', page, err)
        try:
            #note that this only grabs the annotation id and referent text
            #getting the annotation body/author/history would require more calls
            self.annotations = map(lambda a:(a.attrs['data-id'], a.text), soup.select("div.song_body-lyrics")[0].find_all('a', class_="referent"))
        except Exception, err:
            logging.warning('unable to scrape annotation list for %s.Msg: %s', page, err)

class userTests(unittest.TestCase):
    def setUp(self):
        pass


if __name__ == '__main__':
    unittest.main()
