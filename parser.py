#!/usr/bin/env python
# encoding: utf-8
"""
parser.py

Created by Benjamin Fields on 2014-01-28.
Copyright (c) 2014 . All rights reserved.
"""

import sys
import os
import unittest

import requests
from bs4 import BeautifulSoup

from comment import comment


class parser:
    def __init__(self, rg_base="http://rapgenius.com"):
        self.rg_base = rg_base
        
    def search(self, terms=[]):
        rg_search = rg_base+"/search?hide_unexplained_songs=false&q={terms}"
        r = requests.get(rg_search.format(terms=u'+'.join(terms)))
        soup = BeautifulSoup(r.content)
        return [self._parse_song_result(s) for s in soup.select(".song_list li a")]
        
    def get_song(self, track_url):
        r = requests.get(track_url)
        print r
        soup = BeautifulSoup(r.content)
        raw_lyrics = soup.select("div.lyrics p")[0].get_text()
        lyrics = []
        phrase = []
        for line in raw_lyrics.split('\n'):
            if len(line) == 0 and len(phrase) > 0:
              lyrics.append(phrase)
              phrase = []
              continue
            if len(line) > 0 and line[0] != '[':
              #don't add functional phrase labels
              phrase.append(line)
        return lyrics
    
    def get_comment(self, comment_url, fetch_all=False):
        #fetch page
        #grab comment
        
        comment = soup.select("div#container div#main")[0].select("div.big_header")[0].fetchNextSiblings("p")[:-1]
        return comments
        
    
    def _parse_song_result(self, raw_song_result):
        uri = raw_song_result.get('href')
        raw_metadata = raw_song_result.select("span.title_with_artists")[0]
        artist, title = raw_metadata.get_text().strip().split(u' \u2013 ')
        return dict(uri=uri, artist=artist, title=title)
    

class parserTests(unittest.TestCase):
    def setUp(self):
        pass


if __name__ == '__main__':
    unittest.main()