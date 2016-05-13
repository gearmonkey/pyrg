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

def fetch_N_unseen_users(curs, max_id, n, presample=10000):
    """grab 100 unseen users entire via sql for a smaller memory profile. takes a few seconds on a DO $10 vps, runtime scales to presample size"""
    curs.execute("""SELECT possible_users.ids from users, (select generate_series(1,%s) as ids order by random() limit %s) as possible_users where possible_users.ids not in (select id from users) limit %s""", (max_id, presample, n))
    users_to_visit = curs.fetchall()
    curs.execute("""select count(*) from users""")
    users_remaining = max_id - int(curs.fetchone()[0])
    return users_remaining, users_to_visit

def fetch_user_sets(curs, max_id):
    "gather user_sets"
    collected_users = known_users(curs)
    users_remaining = set(range(1, max_id)) - set(collected_users)
    return users_remaining, collected_users

def store(curs, this_user):
    #insert users
    curs.execute("""INSERT INTO users (id, username)
                       VALUES (%(id)s,%(name)s)
                       ON CONFLICT (id) DO UPDATE users SET username = %(name)s""",
                 {'id': this_user.rg_id, 'name': this_user.login})
    #insert comments
    curs.executemany("""INSERT INTO annotation (id, song_id, comment)
                           VALUES (%(id)s, %(song_link)s, %(comment)s)
                           ON CONFLICT (id) DO UPDATE annotation SET song_id = %(song_link)s, comment = %(comment)s""",
                     [{'id': a.rg_id,'song_link': a.song_link,'comment': a.text} for a in this_user.annotations])
    #tie comments to user
    curs.executemany("""INSERT INTO user_contributed_annotation (user_id, annotation_id)
                            VALUES (%(user_id)s, %(annotation_id)s)
                            ON CONFLICT (contrib) DO NOTHING""",
                    [{'user_id':this_user.rg_id, 'annotation_id': a.rg_id} for a in this_user.annotations])
    #edit history
    for annotation in this_user.annotations:
        curs.executemany("""INSERT INTO annotation_history (annotation_id, username, entry_time, comment)
                                VALUES (%(annotation_id)s, %(username)s, %(entry_time)s, %(comment)s)
                                ON CONFLICT (entry) DO UPDATE annotation_history SET username = %(username)s, comment = %(comment)s""",
                        [{'annotation_id':annotation.rg_id, 'username':a[0], 'entry_time':a[1], 'comment':a[2]} for a in annotation.history])

def main(argv=sys.argv):
    max_id = argv[-1]
    max_id = int(max_id)
    conn, curs = create_or_open_db()
    users_remaining = 1
    while users_remaining > 0:
        users_remaining, some_users = fetch_N_unseen_users(curs, max_id, 100)
        for (this_id,) in some_users:
            print "fetching contributions for user", this_id
            this_user = user(rg_id=this_id)
            this_user.get_annotations()
            print "\tuser has", len(this_user.annotations), "annotations, storing..."
            store(curs, this_user)
            conn.commit()




if __name__ == '__main__':
    sys.exit(main())