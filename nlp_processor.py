# nlp_processor.py 
import openai
import re
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class FinanceNLP:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            try:
                # Clean initialization without any extra parameters
                self.client = openai.OpenAI(api_key=self.openai_api_key)
                self.use_new_api = True
                print("✅ OpenAI API v1.0+ initialized successfully")
            except Exception as e:
                print(f"❌ OpenAI init error: {e}")
                self.openai_api_key = None
        else:
            print("🔧 No OpenAI API key, using local parsing")
        
        self.categories = [
            'food', 'transportation', 'entertainment', 'shopping',
            'bills', 'healthcare', 'education', 'travel',
            'groceries', 'dining', 'utilities', 'rent',
            'subscriptions', 'other'
        ]
    
    def parse_expense(self, user_input):
        # Try OpenAI first if available
        if self.openai_api_key and hasattr(self, 'use_new_api'):
            try:
                print(f"🤖 Attempting OpenAI parsing for: {user_input}")
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": f"""Extract expense information from user input. Return ONLY JSON with: amount, description, category, date.
Categories: {', '.join(self.categories)}"""
                        },
                        {
                            "role": "user", 
                            "content": user_input
                        }
                    ],
                    temperature=0.1,
                    max_tokens=150
                )
                
                result_text = response.choices[0].message.content.strip()
                print(f"🤖 OpenAI response: {result_text}")
                
                # Parse JSON response
                import json
                import re
                json_match = re.search(r'\{[^}]+\}', result_text)
                if json_match:
                    expense_data = json.loads(json_match.group())
                    expense_data['amount'] = float(expense_data['amount'])
                    expense_data['category'] = expense_data['category'].lower()
                    print(f"✅ OpenAI parsing successful")
                    return expense_data
                
            except Exception as e:
                print(f"❌ OpenAI parsing failed: {e}")
        
        # Fallback to local parsing
        return self.improved_fallback_parse(user_input)
    
    def improved_fallback_parse(self, user_input):
        """Local parsing as fallback"""
        print(f"🔧 Using local parsing for: '{user_input}'")
        
        # Amount parsing
        amount = 0.0
        patterns = [
            r'\₹(\d+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)\s*\₹', 
            r'paid\s*(\d+(?:\.\d{2})?)',
            r'spent\s*(\d+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, user_input.lower())
            if matches:
                try:
                    amount = float(matches[0])
                    break
                except ValueError:
                    continue
        
        # Category detection
        category = 'other'
        user_input_lower = user_input.lower()
        
        category_keywords = {
            'food': ['lunch', 'dinner', 'breakfast', 'snack', 'meal'],
            'groceries': ['grocery', 'supermarket', 'vegetable', 'fruit', 'milk', 'bread'],
            'transportation': ['bus', 'train', 'taxi', 'uber', 'ola', 'fuel', 'transport'],
            'entertainment': ['movie', 'game', 'concert', 'netflix', 'theater'],
            'shopping': ['buy', 'purchase', 'shopping', 'clothes', 'amazon'],
            'bills': ['bill', 'electricity', 'water', 'internet', 'phone'],
            'healthcare': ['doctor', 'hospital', 'medicine', 'pharmacy'],
            'education': ['book', 'course', 'tuition', 'school'],
            'travel': ['flight', 'hotel', 'vacation', 'trip'],
            'dining': ['restaurant', 'cafe', 'coffee', 'eat out']
        }
        
        for cat, keywords in category_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                category = cat
                break
        
        # Clean description
        description = re.sub(r'\₹\d+(?:\.\d{2})?', '', user_input)
        description = re.sub(r'\d+(?:\.\d{2})?\s*\₹', '', description)
        description = re.sub(r'\b(?:i spent|i paid|paid for|bought)\b', '', description, flags=re.IGNORECASE)
        description = ' '.join(description.split()).strip()
        
        result = {
            'amount': amount,
            'description': description or "Expense",
            'category': category,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
        print(f"📊 Local parsing result: {result}")
        return result
    
    def generate_insights(self, expenses_data):
        if not expenses_data:
            return "Start adding expenses to get insights!"
            
        try:
            total = sum(exp['amount'] for exp in expenses_data)
            categories = {}
            for exp in expenses_data:
                categories[exp['category']] = categories.get(exp['category'], 0) + exp['amount']
            
            if not categories:
                return "Add more expenses to see insights!"
            
            top_category = max(categories.items(), key=lambda x: x[1])
            
            # Try OpenAI insights if available
            if self.openai_api_key and hasattr(self, 'use_new_api'):
                try:
                    spending_summary = "Recent expenses:\n"
                    for expense in expenses_data[:5]:
                        spending_summary += f"- ₹{expense['amount']} on {expense['description']} ({expense['category']})\n"
                    
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Give brief spending insights."},
                            {"role": "user", "content": f"My expenses:\n{spending_summary}\nAny insights?"}
                        ],
                        temperature=0.7,
                        max_tokens=150
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"❌ OpenAI insights failed: {e}")
            
            # Fallback insights
            return f"Total: ₹{total:.2f} | Top category: {top_category[0]} (₹{top_category[1]:.2f})"
            
        except Exception as e:
            print(f"Insights error: {e}")
            return "Keep tracking to see spending patterns!"