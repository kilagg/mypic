from application import CONNECTION_STRING
import pyodbc
import pandas as pd


class SqlManager:
    def __init__(self):
        self._conn = pyodbc.connect(CONNECTION_STRING)
        self._crs = self._conn.cursor()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._crs

    def commit(self):
        self.connection.commit()

    def close(self, commit=False):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, query, params=None):
        self.cursor.execute(query, params or ())

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()

    def query_df(self, query, commit=False, index_col=None):
        result = pd.read_sql(query, self.connection, index_col=index_col)
        self.close(commit)
        return result

    def execute_query(self, query, commit=False):
        self.execute(query)
        self.close(commit)
