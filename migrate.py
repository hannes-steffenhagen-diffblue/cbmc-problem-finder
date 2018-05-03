import sys
import sqlite3


def migrate_0(cur):
    """
    Updates schema from version 0 to 1
    Removes table classified_problem, adds the
    problem_belongs_to_class and
    problem_class tables

    Old classified_problem can be restored with

        SELECT file, line, group_concat(problem_class.name) AS problem_class
        FROM problem_belongs_to_class INNER JOIN problem_class ON class_id = problem_class.id
        GROUP BY file, line;

    :param cur: A cursor to the database that should be migrated. It is assumed
      that the caller ensures that the database is in the right migration state
      and for starting/ commit a transaction prior to and after this function
    """
    cur.execute('CREATE TABLE problem_belongs_to_class(file TEXT, line INTEGER, class_id INTEGER)')
    cur.execute('CREATE TABLE problem_class(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)')
    cur.execute("SELECT DISTINCT problem_class FROM classified_problem WHERE NOT problem_class = ''")
    problem_classes = list(set().union(*map(lambda x: map(lambda s: s.strip(), x[0].split(',')), cur.fetchall())))
    cur.executemany("INSERT INTO problem_class(name) VALUES (?)", map(lambda x: (x,), problem_classes))
    cur.execute("SELECT file, line, problem_class FROM classified_problem WHERE NOT problem_class = ''")
    for classified_problem in cur.fetchall():
        for cl in classified_problem[2].split(','):
            cur.execute("SELECT id FROM problem_class WHERE name = ?", (cl,))
            class_id = cur.fetchone()
            assert class_id is not None
            class_id = class_id[0]
            cur.execute("INSERT INTO problem_belongs_to_class(file, line, class_id) VALUES (?, ?, ?)",
                        (classified_problem[0], classified_problem[1], class_id))
    cur.execute('DROP TABLE classified_problem')


def migrate(db):
    # Disable default transaction management
    # It's ok for normal uses, but is basically unusable for
    # doing migrations because it just commits whenever
    # it sees something that is not a SELECT or UPDATE
    old_isolation_level = db.isolation_level
    db.isolation_level = None
    try:
        cur = db.cursor()
        # Note that this is intentionally not in a try/finally block
        # We don't want to commit transactions if errors occur!
        cur.execute('BEGIN TRANSACTION')
        cur.execute('CREATE TABLE IF NOT EXISTS migration_level (level INTEGER)')
        cur.execute('SELECT level FROM migration_level')
        result = cur.fetchone()
        if result is None:
            cur.execute('INSERT INTO migration_level(level) VALUES (0)')
            migration_level = 0
        else:
            migration_level = result[0]
        cur.execute('COMMIT')
        migrations = [migrate_0]
        for apply_migration in migrations[migration_level:]:
            cur.execute('BEGIN TRANSACTION')
            apply_migration(cur)
            migration_level += 1
            cur.execute('UPDATE migration_level SET level = ?', (migration_level,))
            cur.execute('COMMIT')
    finally:
        db.isolation_level = old_isolation_level


if __name__ == '__main__':
    assert (len(sys.argv) == 2)
    migrate(sqlite3.connect(sys.argv[1]))
