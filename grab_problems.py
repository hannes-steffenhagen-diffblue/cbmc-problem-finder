#!/usr/bin/env python3
import sqlite3
import subprocess


def grab_problem(problem_type):
    values = []
    for line in subprocess.check_output(['git', 'grep', '-n', '\\b' + problem_type + '\\b']).splitlines():
        words = line.decode('utf-8').split(':')
        descr = ':'.join(words[2:]).strip()
        if not descr.startswith('//'):
            values.append((words[0], int(words[1]), problem_type, descr))
    return values


db_file = 'problem.db'

db = sqlite3.connect('problem.db')
db.execute('DROP TABLE IF EXISTS problem')
db.execute('CREATE TABLE problem(file TEXT, line INTEGER, type TEXT, description TEXT)')

problems = []
problems += grab_problem('throw')
problems += grab_problem('assert')
db.executemany('INSERT INTO problem VALUES (?,?,?,?)', problems)
db.commit()
db.close()
