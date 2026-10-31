"""Run Django's MySQL backend on PyMySQL (pure Python; no C compiler needed on Windows)."""

import pymysql

pymysql.install_as_MySQLdb()
