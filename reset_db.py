# reset_db.py
from database import ExpenseDatabase
import sqlite3
import os

def reset_database():
    # Close any existing connections
    if os.path.exists('finance.db'):
        os.remove('finance.db')
        print("🗑️  Old database deleted")
    
    # Create new database
    db = ExpenseDatabase()
    print("✅ New database created")
    
    # Verify it's empty
    expenses = db.get_expenses(days=365)
    print(f"📊 Expenses in new database: {len(expenses)}")

if __name__ == "__main__":
    reset_database()