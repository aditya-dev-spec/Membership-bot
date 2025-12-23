import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="membership_bot.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                joined_date TIMESTAMP
            )
        ''')
        
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan TEXT,
                amount REAL,
                utr TEXT,
                screenshot_id TEXT,
                status TEXT DEFAULT 'pending',
                submitted_at TIMESTAMP,
                verified_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Memberships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, username):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, joined_date)
            VALUES (?, ?, ?)
        ''', (user_id, username, datetime.now()))
        self.conn.commit()
    
    def add_payment(self, user_id, plan, amount, utr, screenshot_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO payments (user_id, plan, amount, utr, screenshot_id, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, plan, amount, utr, screenshot_id, datetime.now()))
        self.conn.commit()
        return cursor.lastrowid
    
    # Add more database methods as needed
    
    def close(self):
        self.conn.close()