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
from comment import comment
from bs4 import BeautifulSoup


class user:
    def __init__(self, rg_id=None, login=None, photo=None):
        self.host = "http://rapgenius.com"
        self.rg_id = rg_id
        self.login = login
        self.photo = photo

    def get_annotations(self, cap=None):
        '''Collect the annotations of the user, is cap is given, only collect the most recent ones, otherwise fetch all (requires <Number of annotations>/10 calls)'''
        next_page = self.host + "/annotations/for_profile_page?page=1&user_id={user_id}".format(user_id=self.rg_id)
        self.annotations = []
        while next_page != None:
            print next_page
            r = requests.get(next_page)
            soup = BeautifulSoup(r.content)
            if self.login == None:
                #if we don't have the login, attempt to scrap it here
                try:
                    #this works if there are no annotations
                    self.login = soup.select(".empty_message")[0].text.strip().replace(u" hasn't annotated any lines!", '')
                except IndexError:
                    try:
                        #this should work if there are annotations (maybe there are other a classes for some users, but I can't find any)
                        self.login = soup.select('div.annotation_unit_label a.community_contributor')[0].text
                    except IndexError:
                        try:
                            #this one is for staff
                            self.login = soup.select('div.annotation_unit a.login')[0].attrs['href'].split('/')[-1]
                        except IndexError:
                            #giving up
                            pass
            for annotation in soup.select("div.stand_alone_annotation_container"):
                annotation_id = annotation.select("div.annotation_unit")[0].get("data-id")  
                # print "id:", annotation_id
                annotation_content = annotation.find(attrs={'class':'annotation_body'}).text
                try:
                    song_link = annotation.find('a', attrs={'class':'title'}).get('href')
                except AttributeError:
                    #alt rendering puts it in a prior div, try there.
                    try:
                        song_link = annotation.findPrevious('div', attrs={'class':'stand_alone_referent'}).find('a', attrs={'class':'title'}).get('href')
                    except:
                        #print the annotation id and give up
                        print "**couldn't grab annotation", annotation_id,"from user", self.rg_id, "moving on"
                        continue
                self.annotations.append(comment(rg_id=annotation_id, text=annotation_content, song=song_link))
                self.annotations[-1].get_full_history()
            pagination_block = soup.find("div", attrs={"class":"pagination"})
            try:
                next_page = pagination_block.find(attrs={'class':"next_page"}).get('href') #if last page this gives None
                if next_page != None:
                    next_page = self.host + next_page
            except AttributeError, err:
                #if we're here, there's no pagination block, due to exactly one page of annons, so, done.
                next_page = None
                


class userTests(unittest.TestCase):
    def setUp(self):
        pass


if __name__ == '__main__':
    unittest.main()
