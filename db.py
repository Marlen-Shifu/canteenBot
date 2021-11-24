import sqlite3

from config import DB_NAME


def db_request(req, *params):
    conn = sqlite3.connect(DB_NAME)

    cur = conn.cursor()

    return [conn, cur.execute(req, *params)]


def setup_db():
    try:
        db_request('''
            CREATE TABLE registered_users(
                id INTEGER PRIMARY KEY,
                username text
            )
        ''')
    except Exception as e:
        print(e)

    try:
        db_request('''
            CREATE TABLE products(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name text,
                price int,
                photo text
            )
        ''')
    except Exception as e:
        print(e)

    try:
        db_request('''
            CREATE TABLE admins(
                id INTEGER PRIMARY KEY,
                username text
            )
        ''')
    except Exception as e:
        print(e)
