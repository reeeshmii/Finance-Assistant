from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import socket
from contextlib import closing
from database import ExpenseDatabase
from nlp_processor import FinanceNLP

app = FastAPI(title="Personal Finance Chatbot")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = ExpenseDatabase()
nlp = FinanceNLP()

class ChatMessage(BaseModel):
    message: str
    user_id: str = "default"

class ExpenseResponse(BaseModel):
    success: bool
    message: str
    expense_id: int = None
    insights: str = None

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Finance chatbot is running!"}

@app.post("/api/chat", response_model=ExpenseResponse)
async def chat_endpoint(chat_message: ChatMessage):
    try:
        user_input = chat_message.message.lower().strip()
        print(f"Received message: {user_input}")
        
        if any(word in user_input for word in ['spent', 'paid', 'bought', 'expense', 'cost', 'purchased']):
            expense_data = nlp.parse_expense(chat_message.message)
            print(f"Parsed expense data: {expense_data}")
            
            expense_id = db.add_expense(
                amount=expense_data['amount'],
                description=expense_data['description'],
                category=expense_data['category'],
                date=expense_data['date']
            )
            
            recent_expenses = db.get_expenses(days=7)
            insights = nlp.generate_insights(recent_expenses)
            
            return ExpenseResponse(
                success=True,
                message=f"✅ Added ₹{expense_data['amount']:.2f} for {expense_data['description']} ({expense_data['category']}) on {expense_data['date']}",
                expense_id=expense_id,
                insights=insights
            )
        
        elif any(word in user_input for word in ['summary', 'report', 'spending', 'how much', 'show']):
            days = 30
            if 'week' in user_input or '7' in user_input:
                days = 7
            elif 'month' in user_input or '30' in user_input:
                days = 30
            
            expenses = db.get_expenses(days=days)
            total_spent = sum(exp['amount'] for exp in expenses)
            category_totals = db.get_spending_by_category(days=days)
            
            if not category_totals:
                return ExpenseResponse(
                    success=True,
                    message="No expenses found for this period. Start by adding some expenses!",
                    insights="Try saying: 'I spent ₹15 on lunch' or 'I paid ₹50 for groceries'"
                )
            
            summary = f"📊 Spending Summary (last {days} days)\n\nTotal: ₹{total_spent:.2f} \n\n\nBy category:\n"
            for category, amount in category_totals.items():
                percentage = (amount / total_spent) * 100 if total_spent > 0 else 0
                summary += f"• {category.title()}: ₹{amount:.2f} ({percentage:.1f}%)\n"
            
            return ExpenseResponse(
                success=True,
                message=summary,
                insights="💡 Tip: Track daily to see your spending patterns!"
            )
        
        elif any(word in user_input for word in ['hello', 'hi', 'hey', 'help']):
            return ExpenseResponse(
                success=True,
                message="👋 Hello! I'm your personal finance assistant. I can help you:\n\n• Track expenses: 'I spent ₹25 on lunch'\n• View summaries: 'Show my spending this week'\n• Analyze patterns: 'How much did I spend on food?'\n\nTry adding an expense to get started!",
                insights="💡 Example: 'I paid ₹15 for Uber today' or 'Bought groceries for ₹85'"
            )
        
        else:
            return ExpenseResponse(
                success=True,
                message="I can help you track expenses and analyze spending. Try:\n• 'I spent ₹25 on dinner'\n• 'Show my weekly spending'\n• 'Add ₹15 for coffee'",
                insights="💡 The more you track, the better insights I can provide!"
            )
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expenses")
async def get_expenses(days: int = 30, category: str = None):
    try:
        expenses = db.get_expenses(days=days, category=category)
        return {"expenses": expenses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/spending-by-category")
async def get_spending_by_category(days: int = 30):
    try:
        category_totals = db.get_spending_by_category(days=days)
        return category_totals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def find_free_port():
    """Find a free port to use"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

if __name__ == "__main__":
    import uvicorn
    port = find_free_port()
    
    print("🚀 Starting Personal Finance Chatbot...")
    print("📊 Database initialized: finance.db")
    print(f"🌐 Backend API: http://localhost:{port}")
    print(f"💬 Open this URL in your browser: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=port)