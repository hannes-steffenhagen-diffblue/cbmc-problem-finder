#!/usr/bin/env python3
import curses
import curses.textpad
import re
import sqlite3
import subprocess
import argparse

input_box = None
checkmark = '\u2713'
crossmark = '\U0001f5d9'
problem_classes = []

def get_folder(path):
    return path.split('/')[0]

def make_choice_window(description):
    lines = len(problem_classes) + 3
    window = curses.newwin(lines, curses.COLS, curses.LINES-lines-2, 0)
    window.addstr(0, 0, description)
    window.addstr(lines-2, 0, 'A) Add class')
    window.addstr(lines-1, 0, 'C) Confirm classes and display next choice')
    return window

def redraw_choices(window, choices):
    assert(len(choices) == len(problem_classes))
    for i in range(0,len(problem_classes)):
        mark = checkmark if choices[i] else crossmark
        window.addstr(i+1, 0, mark + ' ' + str(i+1) +') ' + problem_classes[i])

def handle_problem(screen, db, problem):
    subprocess.run(['emacsclient', '-n', '+'+str(problem['line']), problem['file']])
    descr = '{}:{}: {}'.format(problem['file'],problem['line'],problem['description'])
    window = make_choice_window(descr)
    choices = [False for cl in problem_classes]
    cur = db.cursor()
    cur.execute('SELECT problem_class FROM classified_problem WHERE file = ? AND line = ?', (problem['file'], problem['line']))
    existing_classifier = cur.fetchone()
    if existing_classifier:
        if(options.skip_classified):
            return
        for i in range(len(choices)):
            if(problem_classes[i] in map(lambda s: s.strip(), existing_classifier[0].split(','))):
                choices[i] = True
    while True:
        redraw_choices(window, choices)
        window.refresh()
        screen.refresh()
        c = screen.getch()
        if c == ord('c'):
            break
        elif c in range(ord('1'), ord('9')+1):
            ix = c - ord('1')
            choices[ix] = not choices[ix]
        elif c == ord('a'):
            input_box.edit()
            new_class = input_box.gather()
            problem_classes.append(new_class.strip())
            choices.append(True)
            window.erase()
            window = make_choice_window(descr)
    selected_classes = list(map(lambda x: x[0], filter(lambda x: x[1], zip(problem_classes, choices))))
    joined_class = ','.join(selected_classes)
    cur.execute('DELETE FROM classified_problem WHERE file = ? AND line = ?', (problem['file'], problem['line']))
    cur.execute('INSERT INTO classified_problem(file, line, problem_class) VALUES (?, ?, ?)', (problem['file'], problem['line'], joined_class))
    db.commit()
    cur.close()


def main(screen):
    global problem_classes
    global input_box
    folders = options.folders
    for folder in folders:
        screen.clear()
        screen.addstr(0,0, ('Classifying problems in folder ' + folder))
        screen.refresh()
        editwin = curses.newwin(1, 40, curses.LINES-1, 0)
        input_box = curses.textpad.Textbox(editwin)
        input_box.stripspaces = True
        db = sqlite3.connect('problem.db')
        db.create_function('get_folder', 1, get_folder)
        db.create_function('regex_replace', 3, re.sub)

        cur = db.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS classified_problem(file TEXT, line TEXT, problem_class TEXT)')
        cur.execute("SELECT DISTINCT problem_class FROM classified_problem WHERE NOT problem_class = ''")
        problem_classes = list(set().union(*map(lambda x: map(lambda s: s.strip(), x[0].split(',')), cur.fetchall())))
        cur.execute(r"SELECT file, line, regex_replace('^\s*','',description) as description FROM problem WHERE get_folder(file) = ?", (folder,))
        for problem in cur.fetchall():
            handle_problem(screen, db, {'file': problem[0], 'line': problem[1], 'description': problem[2]})
        cur.close()
    db.close()

argparser = argparse.ArgumentParser(description='Classify code problems')
argparser.add_argument('folders', metavar='folder',
                       type=str, nargs='+',
                       help='the filter for the problem classification')
argparser.add_argument('--skip-classified', action='store_true', help='skip code locations that are already classified')
options = argparser.parse_args()
curses.wrapper(main)
