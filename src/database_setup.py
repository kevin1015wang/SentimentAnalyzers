# src/database_setup.py
import sqlite3
import os

def create_tables(db_path='data/project.db'):
    """
    Creates tables at startup if they do not exist.
    """
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        print("Connected to database successfully")
        
        # Create Reddit users table first
        cur.execute('''
            CREATE TABLE IF NOT EXISTS reddit_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                karma INTEGER,
                account_created TIMESTAMP,
                is_moderator BOOLEAN,
                is_verified BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Created reddit_users table")

        # Create Reddit posts table with foreign key reference
        cur.execute('''
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_id TEXT NOT NULL,
                account_name TEXT NOT NULL,
                post_date TIMESTAMP NOT NULL,
                text_content TEXT NOT NULL,
                is_reply BOOLEAN NOT NULL,
                subreddit TEXT,
                upvotes INTEGER,
                trump_sentiment INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES reddit_users(id)
            )
        ''')
        print("Created reddit_posts table")

        # Create Instagram posts table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS instagram_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT NOT NULL,
                username TEXT NOT NULL,
                caption TEXT,
                post_date TIMESTAMP NOT NULL,
                likes_count INTEGER,
                comments_count INTEGER,
                url TEXT,
                trump_sentiment INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Created instagram_posts table")

        conn.commit()
        print("Changes committed successfully")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    create_tables()
