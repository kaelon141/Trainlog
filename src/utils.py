import json
import re
import sqlite3
from contextlib import contextmanager
from functools import wraps
from glob import glob

from flask import abort, session

from py.sql import getCurrentTrip
from py.utils import load_config
from src.consts import DbNames

pathConn = sqlite3.connect(DbNames.PATH_DB, check_same_thread=False)
pathConn.row_factory = sqlite3.Row

mainConn = sqlite3.connect(DbNames.MAIN_DB, check_same_thread=False)
mainConn.row_factory = sqlite3.Row


owner = load_config()["owner"]["username"]


def getNameFromPath(path):
    return re.search(r"[A-Za-z0-9_\-\.]+(?=\.[A-Za-z0-9]+$)", path).group(0)


def readLang():
    languages = {}
    for lang_path in glob("lang/*.json"):
        with open(lang_path, "r", encoding="utf-8") as lang:
            languages[getNameFromPath(lang_path)] = json.loads(lang.read())
    return languages


lang = readLang()


@contextmanager
def managed_cursor(connection):
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get(owner):
            abort(401)
        return f(*args, **kwargs)

    return decorated_function


def getUser():
    return session.get("logged_in") if session.get("logged_in") else "public"


def isCurrentTrip(username):
    with managed_cursor(mainConn) as cursor:
        trip = cursor.execute(getCurrentTrip, {"username": username}).fetchone()
    if trip is not None:
        return True
    else:
        return False
