import sqlite3
import re


def get_folder(file):
    return file.split(' ')[0]


def regex_match(regex, text):
    return re.match(regex, text) is not None


def open_db(path):
    db = sqlite3.connect(path)
    db.create_function('get_folder', 1, get_folder)
    db.create_function('regex_replace', 3, re.sub)
    db.create_function('regex_match', 2, regex_match)
    return db
