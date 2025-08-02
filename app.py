from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import hashlib
import jwt
import datetime
import json
import re
from collections import Counter
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
CORS(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Categories table for ML training
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Simple ML-based transaction classification
def classify_transaction(description):
    description = description.lower()
    
    # Define category keywords
    categories = {
        'groceries': ['food', 'grocery', 'supermarket', 'market', 'fresh', 'organic', 'produce'],
        'transportation': ['uber', 'lyft', 'taxi', 'gas', 'fuel', 'parking', 'metro', 'bus', 'train'],
        'entertainment': ['movie', 'theater', 'concert', 'game', 'netflix', 'spotify', 'amazon prime'],
        'utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'cable', 'wifi'],
        'shopping': ['amazon', 'walmart', 'target', 'clothing', 'shoes', 'electronics'],
        'dining': ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'sushi', 'dinner', 'lunch'],
        'healthcare': ['pharmacy', 'doctor', 'medical', 'dental', 'vision', 'insurance'],
        'education': ['book', 'course', 'tuition', 'school', 'college', 'university'],
        'travel': ['hotel', 'flight', 'airbnb', 'vacation', 'trip', 'booking']
    }
    
    # Find matching category
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in description:
                return category
    
    return 'other'

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Generate JWT token
def generate_token(user_id, username):
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

# Verify JWT token
def verify_token(token):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload
    except:
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({'error': 'All fields are required'}), 400
    
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    try:
        hashed_password = hash_password(password)
        cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                      (username, hashed_password, email))
        conn.commit()
        
        user_id = cursor.lastrowid
        token = generate_token(user_id, username)
        
        conn.close()
        return jsonify({'token': token, 'user_id': user_id, 'username': username}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    cursor.execute('SELECT id, username FROM users WHERE username = ? AND password = ?',
                  (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        token = generate_token(user[0], user[1])
        return jsonify({'token': token, 'user_id': user[0], 'username': user[1]}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401
    
    user_id = payload['user_id']
    
    if request.method == 'POST':
        data = request.get_json()
        description = data.get('description')
        amount = data.get('amount')
        type_transaction = data.get('type')  # 'income' or 'expense'
        date = data.get('date')
        
        if not all([description, amount, type_transaction, date]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Auto-classify transaction
        category = classify_transaction(description)
        
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, description, amount, type, category, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, description, amount, type_transaction, category, date))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Transaction added successfully', 'category': category}), 201
    
    else:  # GET request
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, description, amount, type, category, date
            FROM transactions WHERE user_id = ? ORDER BY date DESC
        ''', (user_id,))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'id': row[0],
                'description': row[1],
                'amount': row[2],
                'type': row[3],
                'category': row[4],
                'date': row[5]
            })
        
        conn.close()
        return jsonify(transactions), 200

@app.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401
    
    user_id = payload['user_id']
    
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?',
                  (transaction_id, user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Transaction not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Transaction deleted successfully'}), 200

@app.route('/analytics')
def analytics():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401
    
    user_id = payload['user_id']
    
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    # Get current month's data
    current_month = datetime.datetime.now().strftime('%Y-%m')
    
    # Monthly summary
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses
        FROM transactions 
        WHERE user_id = ? AND date LIKE ?
    ''', (user_id, f'{current_month}%'))
    
    summary = cursor.fetchone()
    total_income = summary[0] or 0
    total_expenses = summary[1] or 0
    net_income = total_income - total_expenses
    
    # Category breakdown
    cursor.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions 
        WHERE user_id = ? AND type = 'expense' AND date LIKE ?
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id, f'{current_month}%'))
    
    categories = []
    for row in cursor.fetchall():
        categories.append({
            'category': row[0],
            'amount': row[1]
        })
    
    # Recent transactions for insights
    cursor.execute('''
        SELECT description, amount, category, date
        FROM transactions 
        WHERE user_id = ? AND type = 'expense'
        ORDER BY date DESC LIMIT 10
    ''', (user_id,))
    
    recent_transactions = []
    for row in cursor.fetchall():
        recent_transactions.append({
            'description': row[0],
            'amount': row[1],
            'category': row[2],
            'date': row[3]
        })
    
    conn.close()
    
    # Generate insights
    insights = []
    if total_expenses > total_income * 0.8:
        insights.append("⚠️ You're spending more than 80% of your income. Consider reducing expenses.")
    
    if categories:
        top_category = categories[0]
        if top_category['amount'] > total_expenses * 0.4:
            insights.append(f"💰 {top_category['category'].title()} accounts for over 40% of your expenses. Consider budgeting for this category.")
    
    if net_income < 0:
        insights.append("📉 Your expenses exceed your income this month. Focus on increasing income or reducing expenses.")
    elif net_income > 0:
        insights.append("✅ Great job! You have positive net income this month.")
    
    return jsonify({
        'summary': {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': net_income
        },
        'categories': categories,
        'recent_transactions': recent_transactions,
        'insights': insights
    }), 200

@app.route('/upload', methods=['POST'])
def upload_csv():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401
    
    user_id = payload['user_id']
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    try:
        content = file.read().decode('utf-8')
        lines = content.strip().split('\n')
        
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        imported_count = 0
        for line in lines[1:]:  # Skip header
            parts = line.split(',')
            if len(parts) >= 3:
                description = parts[0].strip()
                amount = float(parts[1].strip())
                type_transaction = parts[2].strip().lower()
                date = parts[3].strip() if len(parts) > 3 else datetime.datetime.now().strftime('%Y-%m-%d')
                
                category = classify_transaction(description)
                
                cursor.execute('''
                    INSERT INTO transactions (user_id, description, amount, type, category, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, description, amount, type_transaction, category, date))
                
                imported_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Successfully imported {imported_count} transactions'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000) 