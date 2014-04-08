#!/usr/bin/env python
# encoding: utf-8
"""
user_spider.py

run as >python user_comment_spider.py [max user ID] [sqlite db]

will randomly select a user, and collect all comments from that user.

will stash both users and comments (but not song lyrics, only song urls) in the db

does not grab song lyrics or contribution percentages yet, to minimize calls.
"""

import sys, os
import random
import sqlite3
from user import user

def create_or_open_db(db_file_path):
	"setup the db connection, if needed create the tables"
	#close and reopen to deal with known if not exists bug
	with sqlite3.connect(db_file_path) as conn:
		curs = conn.cursor()
		curs.execute("""CREATE TABLE IF NOT EXISTS 'users' (id BIGINT,
															username TEXT)""")
		curs.execute("""CREATE TABLE IF NOT EXISTS 'annotation' (id BIGINT,
																song_id TEXT,
																comment TEXT)""")
		curs.execute("""CREATE TABLE IF NOT EXISTS 'user_contributed_annotation' (user_id BIGINT,
																				  annotation_id TEXT,
																				  score REAL)""")
		conn.commit()
	conn = sqlite3.connect(db_file_path)
	curs = conn.cursor()
	return conn, curs


def known_users(curs):
	"fetch the list of stored user_ids"
	curs.execute("""SELECT id FROM users""")
	return curs.fetchall()

def store(curs, this_user):
	curs.execute('INSERT INTO users (id, username) VALUES (?,?)', 
		         (this_user.rg_id, this_user.login))
	#insert comments
	curs.executemany('INSERT INTO annotation (id, song_id, comment) VALUES (?,?,?)', 
					 [(a.rg_id, a.song_link, a.text) for a in this_user.annotations])
	#tie comments to user
	curs.executemany('INSERT INTO user_contributed_annotation (user_id, annotation_id) VALUES (?,?)',
			     	[(this_user.rg_id, a.rg_id) for a in this_user.annotations])

def main(argv=sys.argv):
	max_id, db_file_path = argv[-2:]
	max_id = int(max_id)
	conn, curs = create_or_open_db(db_file_path)
	collected_users = known_users(curs)
	users_remaining = set(range(1, max_id)) - set(collected_users)
	while len(users_remaining) < max_id:
		this_id = random.sample(users_remaining, 1)[0]
		print "fetching contributions for user", this_id
		this_user = user(rg_id=this_id)
		this_user.get_annotations()
		print "\tuser has", len(this_user.annotations), "annotations, storing..."
		store(curs, this_user)
		conn.commit()
		users_remaining.remove(this_id)
		collected_users.append(this_id)




if __name__ == '__main__':
	sys.exit(main())