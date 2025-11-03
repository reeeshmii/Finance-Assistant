# database.py
import sqlite3
from datetime import datetime, timedelta
import json

class ExpenseDatabase:
    def __init__(self, db_path='finance.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                month TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_expense(self, amount, description, category, date=None):
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (amount, description, category, date)
            VALUES (?, ?, ?, ?)
        ''', (amount, description, category, date))
        conn.commit()
        expense_id = cursor.lastrowid
        conn.close()
        return expense_id
    
    def get_expenses(self, days=30, category=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT * FROM expenses 
            WHERE date >= ?
        '''
        params = [start_date]
        
        if category:
            query += ' AND category = ?'
            params.append(category)
            
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'amount': row[1],
            'description': row[2],
            'category': row[3],
            'date': row[4]
        } for row in expenses]
    
    def get_spending_by_category(self, days=30):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE date >= ?
            GROUP BY category
            ORDER BY total DESC
        ''', (start_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in results}