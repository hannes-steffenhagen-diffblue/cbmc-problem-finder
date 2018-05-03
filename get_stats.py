#!/usr/bin/env python3
import sqlite3
from configure_db import open_db

db = open_db('problem.db')
cur = db.cursor()
cur.execute('SELECT get_folder(file) as folder, count(*) as problem_count FROM problem GROUP BY folder')
print('folder, problem_count')
for folder in cur.fetchall():
    print('{}, {}'.format(folder[0], folder[1]))
