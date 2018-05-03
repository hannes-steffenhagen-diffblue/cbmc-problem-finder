#!/usr/bin/env python3

from configure_db import open_db
import sys

assert (len(sys.argv) == 2)

db = open_db('problem.db')

cur = db.cursor()
cur.execute(sys.argv[1])
header = '|'.join(map(lambda col: col[0], cur.description))
print(header)
for row in cur.fetchall():
    row_text = '|'.join(map(str, row))
    print(row_text)
