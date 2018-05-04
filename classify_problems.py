#!/usr/bin/env python3
import argparse
import curses
import curses.textpad
import subprocess

from configure_db import open_db

input_box = None
checkmark = '[X]'
crossmark = '[ ]'
problem_classes = []


def update_header(screen, folder, i, n):
    screen.addstr(0, 0, 'Classifying problem [{}/{}] in folder {}'.format(
        i, n, folder))


def get_folder(path):
    return path.split('/')[0]


def make_choice_window(description):
    lines = len(problem_classes) + 3
    window = curses.newwin(lines, curses.COLS, curses.LINES - lines - 2, 0)
    window.addstr(0, 0, description)
    window.addstr(lines - 2, 0, 'A) Add class')
    window.addstr(lines - 1, 0, 'C) Confirm classes and display next choice')
    return window


def redraw_choices(window, choices):
    assert (len(choices) == len(problem_classes))
    for i in range(0, len(problem_classes)):
        mark = checkmark if choices[i] else crossmark
        window.addstr(i + 1, 0, str(i + 1) + ') ' + problem_classes[i] + ' ' + mark)


def handle_problem(screen, db, problem):
    descr = '{}:{}: {}'.format(problem['file'], problem['line'], problem['description'])
    window = make_choice_window(descr)
    choices = [False for cl in problem_classes]
    cur = db.cursor()
    cur.execute("""SELECT group_concat(problem_class.name) AS problem_classes
        FROM problem_belongs_to_class INNER JOIN problem_class
          ON problem_class.id = class_id
        WHERE file = ? AND line = ?""",
                (problem['file'], problem['line']))
    existing_classifier = cur.fetchone()
    if existing_classifier[0] is not None:
        if options.skip_classified:
            return
        for i in range(len(choices)):
            if problem_classes[i] in map(lambda s: s.strip(), existing_classifier[0].split(',')):
                choices[i] = True

    # TODO make this configurable?
    subprocess.run(['emacsclient', '-n', '+' + str(problem['line']), problem['file']])
    while True:
        redraw_choices(window, choices)
        window.refresh()
        screen.refresh()
        c = screen.getch()
        if c == ord('c'):
            break
        elif c in range(ord('1'), ord('9') + 1):
            ix = c - ord('1')
            choices[ix] = not choices[ix]
        elif c == ord('a'):
            input_box.edit()
            new_class = input_box.gather().strip()
            problem_classes.append(new_class)
            cur.execute("INSERT INTO problem_class(name) VALUES (?)", new_class)
            cur.commit()
            choices.append(True)
            window.erase()
            window = make_choice_window(descr)
    selected_classes = list(
        map(lambda x: (problem['file'], problem['line'], x[0]), filter(lambda x: x[1], zip(problem_classes, choices))))
    cur.execute('DELETE FROM problem_belongs_to_class WHERE file = ? AND line = ?', (problem['file'], problem['line']))
    cur.executemany("""INSERT INTO problem_belongs_to_class(file, line, class_id)
                   SELECT ?, ?, problem_class.id
                   FROM problem_class
                   WHERE problem_class.name = ?""",
                    selected_classes)
    db.commit()
    cur.close()


def main(screen):
    global problem_classes
    global input_box
    folders = options.folders
    db = open_db('problem.db')
    cur = db.cursor()
    editwin = curses.newwin(1, 40, curses.LINES - 1, 0)
    input_box = curses.textpad.Textbox(editwin)
    input_box.stripspaces = True
    cur.execute("SELECT group_concat(problem_class.name) as all_classes FROM problem_class")
    existing_classes = cur.fetchone()[0]
    problem_classes = existing_classes.split(',') if existing_classes != '' else problem_classes
    for folder in folders:
        screen.clear()
        screen.refresh()
        cur.execute(r"""
            SELECT file, line, regex_replace('^\s*','',description) as description
            FROM problem
            WHERE
                get_folder(file) = ?
                AND file LIKE ('%' || ? || '%')
                AND description LIKE ('%' || ? || '%')""",  # Inelegant, but should work for our purposes
                    (folder, options.file, options.description))
        i = 0
        problems = cur.fetchall()
        for problem in problems:
            i += 1
            update_header(screen, folder, i, len(problems))
            handle_problem(screen, db, {'file': problem[0], 'line': problem[1], 'description': problem[2]})
    cur.close()
    db.close()


argparser = argparse.ArgumentParser(description='Classify code problems')
argparser.add_argument('folders', metavar='folder',
                       type=str, nargs='+',
                       help='the filter for the problem classification')
argparser.add_argument('--skip-classified', action='store_true', help='skip code locations that are already classified')
argparser.add_argument('--file', help='only consider files whose path contains this string', default='')
argparser.add_argument('--description', help='only consider problems whose description contains this string',
                       default='')
options = argparser.parse_args()
curses.wrapper(main)
