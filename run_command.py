#!/usr/bin/env python3
import sqlite3
import sys
import re

assert(len(sys.argv) == 2)

def get_folder(path):
    return path.split('/')[0]

def regex_match(regex, text):
    return re.match(regex, text) != None

db = sqlite3.connect('problem.db')

db.create_function('get_folder', 1, get_folder)
db.create_function('regex_match', 2, regex_match)
db.create_function('regex_replace', 3, re.sub)

cur = db.cursor()
cur.execute(sys.argv[1])
header = ''

first = True
for col in cur.description:
    if not first:
        header += ', '
    header += col[0]
    first = False

print(header)
for row in cur.fetchall():
    row_text = ''
    first = True
    for col in row:
        if not first:
            row_text += ', '
        row_text += str(col)
        first = False
    print(row_text)
        
