#!/usr/bin/env python
# encoding: utf-8
"""
comment.py

Created by Benjamin Fields on 2014-02-11.
Copyright (c) 2014 . All rights reserved.
"""

import sys
import os
import unittest

import requests
import re
from bs4 import BeautifulSoup


class comment(object):
    def __init__(self, rg_id=None, text=None, links=[], contributors=[], song=None):
        self.rg_id = rg_id
        self.text = text
        self.links = links
        self.contributors = contributors
        self.song_link = song

    def get_contributors(self, url='http://genius.com/annotations/full_credits?annotation_id={anno_id}'):
        '''fetches conntributers and the strength of their contributions'''
        r = requests.get(url.format(anno_id=self.rg_id))
        soup = BeautifulSoup(r.content)
        self.contributors = []
        for user in soup.select("div.user_badge"):
            user_name = self._get_username(user)
            user_id = self._get_userid(user)
            #contribution percentage
            perc_contribution = self._get_contribution(user)
            self.contributors.append((user_id, user_name, perc_contribution))

    def get_full_history(self, url = "http://genius.com/annotations/{anno_id}/history"):
        """fetches the history of the comment with attribution and timestamps,
        can optionally generate and store diffs instead of the native complete comment"""
        r = requests.get(url.format(anno_id=self.rg_id))
        soup = BeautifulSoup(r.content)

        self.history = []
        for entry in soup.select("div.annotation_version"):
            user_name = entry.p.b.strings.next().strip().replace('Updated by ', '')
            time_of_change = entry.p.b.span.attrs['data-timeago']
            body = entry.div.text
            self.history.append((user_name, time_of_change, body))

    def _get_contribution(self, user):
        '''parse out the contribution as a percentage for the user associated with the passed in soup'''
        css_regex = re.compile('width: (\d*?)\%')
        raw_css = user.nextSibling.nextSibling.select("div.fill")[0].get('style')
        return float(css_regex.findall(raw_css)[0])/100

    def _get_username(self, user):
        '''extract the login username from user block'''
        return user.div(attrs={'class':'login'})[0].text

    def _get_userid(self, user):
        '''extract the user id from the user block'''
        return user.get('data-id')


class commentTests(unittest.TestCase):
    def setUp(self):
        pass


if __name__ == '__main__':
    unittest.main()