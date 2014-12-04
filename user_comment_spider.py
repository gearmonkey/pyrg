#!/usr/bin/env python
# encoding: utf-8
"""
user_spider.py

run as >python user_comment_spider.py [max user ID] [sqlite db]

will randomly select a user, and collect all comments from that user.

will stash both users and comments (but not song lyrics, only song urls) in the db

does not grab song lyrics or contribution percentages yet, to minimize calls.

need to fetch full history, which for each comment can be found at /annotations/(anno_id)/history
"""

import sys, os
import random
import psycopg2
from user import user

# using this bit of magic to tunnel:
# ssh -M -S my-ctrl-socket -fnNT -L 63333:localhost:5432 rg@<host db address>
def create_or_open_db(connection_str="postgresql://rg:rg@localhost:63333/genius"):
    "setup the db connection, if needed create the tables"
    #close and reopen to deal with known if not exists bug
    with psycopg2.connect(connection_str) as conn:
        curs = conn.cursor()
        curs.execute("""CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY,
                                                            username TEXT)""")
        curs.execute("""CREATE TABLE IF NOT EXISTS annotation (id BIGINT PRIMARY KEY,
                                                                song_id TEXT,
                                                                comment TEXT)""")
        curs.execute("""CREATE TABLE IF NOT EXISTS user_contributed_annotation (user_id BIGINT,
                                                                                  annotation_id TEXT,
                                                                                  score REAL,
                                                                                  CONSTRAINT contrib PRIMARY KEY (user_id, annotation_id))""")
        curs.execute("""CREATE TABLE IF NOT EXISTS annotation_history (annotation_id BIGINT,
                                                                         entry_time TIMESTAMP,
                                                                         username TEXT,
                                                                         comment TEXT,
                                                                         CONSTRAINT entry PRIMARY KEY (annotation_id, entry_time))""")
        conn.commit()
    conn = psycopg2.connect(connection_str)
    curs = conn.cursor()
    return conn, curs

def known_users(curs):
    "fetch the list of stored user_ids"
    curs.execute("""SELECT id FROM users""")
    return curs.fetchall()

def fetch_user_sets(curs, max_id):
    "gather user_sets"
    collected_users = known_users(curs)
    users_remaining = set(range(1, max_id)) - set(collected_users)
    return users_remaining, collected_users

def store(curs, this_user):
    ####these all need to be upserts###
    curs.execute("""WITH upsert AS (UPDATE users SET username = %(name)s WHERE id = %(id)s RETURNING *) 
                    INSERT INTO users (id, username) SELECT %(id)s,%(name)s WHERE NOT EXISTS (SELECT * FROM upsert)""", 
                 {'id': this_user.rg_id, 'name': this_user.login})
    #insert comments
    curs.executemany("""WITH upsert AS (UPDATE annotation 
                                            SET song_id = %(song_link)s, comment = %(comment)s 
                                            WHERE id = %(id)s RETURNING *) 
                        INSERT INTO annotation (id, song_id, comment) SELECT %(id)s, %(song_link)s, %(comment)s WHERE NOT EXISTS (SELECT * FROM upsert)""", 
                     [{'id': a.rg_id,'song_link': a.song_link,'comment': a.text} for a in this_user.annotations])
    #tie comments to user
    curs.executemany("""WITH upsert AS (UPDATE user_contributed_annotation 
                                            SET user_id = %(user_id)s 
                                            WHERE annotation_id = %(annotation_id)s RETURNING *) 
                        INSERT INTO user_contributed_annotation (user_id, annotation_id) 
                            SELECT %(user_id)s, %(annotation_id)s WHERE NOT EXISTS (SELECT * FROM upsert)""",
                    [{'user_id':this_user.rg_id, 'annotation_id': a.rg_id} for a in this_user.annotations])
    #edit history
    for annotation in this_user.annotations:
        curs.executemany("""WITH upsert AS (UPDATE annotation_history 
                                                SET username = %(username)s, comment = %(comment)s 
                                                WHERE annotation_id = %(annotation_id)s AND entry_time = %(entry_time)s RETURNING *) 
                            INSERT INTO annotation_history (annotation_id, username, entry_time, comment) 
                                SELECT %(annotation_id)s, %(username)s, %(entry_time)s, %(comment)s WHERE NOT EXISTS (SELECT * FROM upsert)""",
                        [{'annotation_id':annotation.rg_id, 'username':a[0], 'entry_time':a[1], 'comment':a[2]} for a in annotation.history])

def main(argv=sys.argv):
    max_id = argv[-1]
    max_id = int(max_id)
    conn, curs = create_or_open_db()
    users_remaining, collected_users = fetch_user_sets(curs, max_id)
    sync_count = 0
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
        sync_count += 1
        if sync_count == 100:
            users_remaining, collected_users = fetch_user_sets(curs, max_id)
            sync_count = 0




if __name__ == '__main__':
    sys.exit(main())