#!/usr/bin/env python3
import sqlite3

def get_folder(path):
    return path.split('/')[0]

db = sqlite3.connect('problem.db')
db.create_function('get_folder', 1, get_folder)
cur = db.cursor()
cur.execute('SELECT get_folder(file) as folder, count(*) as problem_count FROM problem GROUP BY folder')
print('folder, problem_count')
for folder in cur.fetchall():
    print('{:s}, {:d}'.format(folder[0], folder[1]))
