import os
import sqlite3
from prs_project.settings import BASE_DIR

db = os.path.join(BASE_DIR, 'db.sqlite3')

def connect_to_db():
    return connect_to_sqllite()

def connect_to_sqllite():
    return sqlite3.connect(db)


def get_query_cursor(sql):
    conn = connect_to_sqllite()
    c = conn.cursor()

    return c.execute(sql)


def execute_many(sql, items):
    conn = connect_to_sqllite()
    c = conn.cursor()
    c.executemany(sql, items)


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
        ]