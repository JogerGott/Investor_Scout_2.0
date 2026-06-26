import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DBConnectionManager
import mysql.connector

SQL_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "info", "InvestorScout_FINAL_v4.sql")

def initialize_database():
    print("--- Investor Scout DB Initialization ---")
    if not os.path.exists(SQL_FILE_PATH):
        print(f"Error: SQL schema file not found at: {SQL_FILE_PATH}")
        return False
        
    try:
        conn = DBConnectionManager.get_connection()
        cursor = conn.cursor()
        
        with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
            sql_script = f.read()
            
        print("Executing DDL script from InvestorScout_FINAL_v4.sql...")
        # Custom SQL parser: split statements by semicolon, skipping comments
        statements = []
        current_statement = []
        for line in sql_script.splitlines():
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("--") or trimmed.startswith("#"):
                continue
            current_statement.append(line)
            if trimmed.endswith(";"):
                statements.append("\n".join(current_statement))
                current_statement = []
                
        if current_statement:
            leftover = "\n".join(current_statement).strip()
            if leftover:
                statements.append(leftover)

        count = 0
        for stmt in statements:
            if stmt.strip():
                cursor.execute(stmt)
                count += 1
            
        print(f"Successfully executed {count} SQL statements.")
        conn.commit()
        cursor.close()
        conn.close()
        print("Database tables initialized successfully.")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    initialize_database()
