import json
import os
import mysql.connector
from mysql.connector import pooling
from typing import Any, Dict

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "db_config.json")

class DBConnectionManager:
    """
    Manages MySQL connections using a MySQLConnectionPool.
    Loads configuration dynamically from db_config.json and ensures the database is created.
    """
    _pool = None
    _db_name = None

    @classmethod
    def _initialize_pool(cls):
        if cls._pool is None:
            if not os.path.exists(CONFIG_PATH):
                raise FileNotFoundError(f"Configuration file not found at: {CONFIG_PATH}")
            
            with open(CONFIG_PATH, "r") as f:
                config: Dict[str, Any] = json.load(f)
            
            cls._db_name = config.get("database", "investor_scout")
            
            # Setup pool connection parameters
            pool_config = {
                "host": config.get("host", "127.0.0.1"),
                "port": int(config.get("port", 3306)),
                "user": config.get("user", "root"),
                "password": config.get("password", ""),
                "pool_name": "investor_scout_pool",
                "pool_size": 5
            }
            
            # Create database if it does not exist
            cls._create_database_if_not_exists(pool_config, cls._db_name)
            
            # Update configuration with database name and create pool
            pool_config["database"] = cls._db_name
            cls._pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)

    @classmethod
    def _create_database_if_not_exists(cls, config: Dict[str, Any], db_name: str):
        try:
            conn = mysql.connector.connect(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"]
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            print(f"Error checking/creating database '{db_name}': {err}")
            raise err

    @classmethod
    def get_connection(cls):
        """
        Retrieves a connection from the connection pool.
        """
        cls._initialize_pool()
        return cls._pool.get_connection()

    @classmethod
    def get_db_name(cls) -> str:
        cls._initialize_pool()
        return cls._db_name
