import mysql.connector
from app.database.connection import DBConnectionManager

class BaseRepository:
    """
    Base Repository class providing database connection sharing.
    Supports transactions by passing a shared connection.
    """
    def __init__(self, connection=None):
        self._connection = connection

    def get_connection(self):
        if self._connection:
            return self._connection
        return DBConnectionManager.get_connection()

    def close_connection(self, conn):
        # Only close if it's not a shared connection (which should be closed by the owner)
        if not self._connection and conn:
            conn.close()
