# src/database_setup.py
import sqlite3

def create_tables(db_path='data/project.db'):
    """
    Creates tables at startup if they do not exist.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # tables as you see fit

    conn.commit()
    conn.close()
