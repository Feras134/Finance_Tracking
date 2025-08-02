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
import secrets
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
import validators

app = Flask(__name__)

# Secure secret key generation
def generate_secret_key():
    return secrets.token_hex(32)

# Use environment variable for secret key, fallback to generated one
app.secret_key = os.environ.get('SECRET_KEY', generate_secret_key())

# Secure CORS configuration
CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'], 
     supports_credentials=True, methods=['GET', 'POST', 'DELETE'])

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src https://cdnjs.cloudflare.com"
    return response

# Input validation functions
def validate_email(email):
    return validators.email(email)

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def sanitize_input(text):
    if not text:
        return ""
    # Remove potentially dangerous characters
    return re.sub(r'[<>"\']', '', str(text))

def validate_amount(amount):
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return False, "Amount must be positive"
        return True, amount_float
    except ValueError:
        return False, "Invalid amount format"

def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True, date_str
    except ValueError:
        return False, "Invalid date format (YYYY-MM-DD)"

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

# Secure password hashing
def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password, hashed_password):
    return check_password_hash(hashed_password, password)

# Generate JWT token
def generate_token(user_id, username):
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

# Verify JWT token
def verify_token(token):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    
    # Input validation
    if not username or not password or not email:
        return jsonify({'error': 'All fields are required'}), 400
    
    # Validate email
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password
    is_valid, password_msg = validate_password(password)
    if not is_valid:
        return jsonify({'error': password_msg}), 400
    
    # Sanitize inputs
    username = sanitize_input(username)
    email = sanitize_input(email)
    
    # Validate username length
    if len(username) < 3 or len(username) > 50:
        return jsonify({'error': 'Username must be between 3 and 50 characters'}), 400
    
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
    except Exception as e:
        conn.close()
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Sanitize username
    username = sanitize_input(username)
    
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user[2]):
            token = generate_token(user[0], user[1])
            return jsonify({'token': token, 'user_id': user[0], 'username': user[1]}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        conn.close()
        return jsonify({'error': 'Login failed'}), 500

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    user_id = payload['user_id']
    
    if request.method == 'POST':
        data = request.get_json()
        description = data.get('description', '').strip()
        amount = data.get('amount')
        type_transaction = data.get('type', '').lower()
        date = data.get('date', '').strip()
        
        # Input validation
        if not description or amount is None or not type_transaction or not date:
            return jsonify({'error': 'All fields are required'}), 400
        
        # Validate amount
        is_valid, amount_result = validate_amount(amount)
        if not is_valid:
            return jsonify({'error': amount_result}), 400
        
        # Validate transaction type
        if type_transaction not in ['income', 'expense']:
            return jsonify({'error': 'Type must be income or expense'}), 400
        
        # Validate date
        is_valid, date_result = validate_date(date)
        if not is_valid:
            return jsonify({'error': date_result}), 400
        
        # Sanitize description
        description = sanitize_input(description)
        
        # Auto-classify transaction
        category = classify_transaction(description)
        
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO transactions (user_id, description, amount, type, category, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, description, amount_result, type_transaction, category, date_result))
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Transaction added successfully', 'category': category}), 201
        except Exception as e:
            conn.close()
            return jsonify({'error': 'Failed to add transaction'}), 500
    
    else:  # GET request
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        try:
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
        except Exception as e:
            conn.close()
            return jsonify({'error': 'Failed to load transactions'}), 500

@app.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    user_id = payload['user_id']
    
    # Validate transaction_id
    if transaction_id <= 0:
        return jsonify({'error': 'Invalid transaction ID'}), 400
    
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?',
                      (transaction_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Transaction not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Transaction deleted successfully'}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': 'Failed to delete transaction'}), 500

@app.route('/analytics')
def analytics():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    user_id = payload['user_id']
    
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    try:
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
    except Exception as e:
        conn.close()
        return jsonify({'error': 'Failed to load analytics'}), 500

@app.route('/upload', methods=['POST'])
def upload_csv():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    user_id = payload['user_id']
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Enhanced file validation
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file'}), 400
    
    # Check file size (limit to 5MB)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 5 * 1024 * 1024:  # 5MB limit
        return jsonify({'error': 'File size too large (max 5MB)'}), 400
    
    try:
        content = file.read().decode('utf-8')
        lines = content.strip().split('\n')
        
        if len(lines) < 2:  # Need at least header + 1 data row
            return jsonify({'error': 'CSV file must contain at least a header and one data row'}), 400
        
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        imported_count = 0
        for line_num, line in enumerate(lines[1:], 2):  # Skip header, start counting from 2
            parts = line.split(',')
            if len(parts) >= 3:
                description = sanitize_input(parts[0].strip())
                amount_str = parts[1].strip()
                type_transaction = parts[2].strip().lower()
                date = parts[3].strip() if len(parts) > 3 else datetime.datetime.now().strftime('%Y-%m-%d')
                
                # Validate amount
                is_valid, amount_result = validate_amount(amount_str)
                if not is_valid:
                    conn.close()
                    return jsonify({'error': f'Invalid amount in row {line_num}: {amount_result}'}), 400
                
                # Validate type
                if type_transaction not in ['income', 'expense']:
                    conn.close()
                    return jsonify({'error': f'Invalid type in row {line_num}: must be income or expense'}), 400
                
                # Validate date
                is_valid, date_result = validate_date(date)
                if not is_valid:
                    conn.close()
                    return jsonify({'error': f'Invalid date in row {line_num}: {date_result}'}), 400
                
                category = classify_transaction(description)
                
                cursor.execute('''
                    INSERT INTO transactions (user_id, description, amount, type, category, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, description, amount_result, type_transaction, category, date_result))
                
                imported_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Successfully imported {imported_count} transactions'}), 200
        
    except UnicodeDecodeError:
        return jsonify({'error': 'Invalid file encoding. Please use UTF-8 encoding'}), 400
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 400

if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000) 