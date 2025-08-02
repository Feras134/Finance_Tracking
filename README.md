# Personal Finance Tracker

A full-stack web application that enables users to track, categorize, and analyze their personal financial transactions. The system leverages machine learning to automatically classify expenses and provide personalized financial insights.

## Features

###  User Authentication
- Secure user registration and login
- JWT token-based authentication
- Password hashing for security

### Transaction Management
- Add, edit, and delete income/expense entries
- Manual transaction entry with auto-categorization
- CSV file import functionality
- Real-time transaction filtering

###  Machine Learning Categorization
- Automatic transaction classification using NLP
- Categories include: groceries, transportation, entertainment, utilities, shopping, dining, healthcare, education, travel
- Smart keyword-based classification system

###  Data Visualization
- Interactive dashboard with summary cards
- Spending breakdown by category (doughnut chart)
- Monthly overview with income vs expenses (line chart)
- Responsive charts using Chart.js

###  Smart Insights and Alerts
- Personalized financial insights based on spending patterns
- Alerts for overspending or abnormal transactions
- Tips for saving based on behavioral trends

### 📱 Mobile-Responsive Design
- Modern, beautiful UI with gradient backgrounds
- Fully responsive design that works on all screen sizes
- Intuitive navigation and user experience

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python with Flask
- **Database**: SQLite
- **Authentication**: JWT tokens
- **Charts**: Chart.js
- **Icons**: Font Awesome
- **Machine Learning**: Simple NLP-based classification

## Installation and Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Step 1: Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd personal-finance-tracker

# Or simply download and extract the files
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

### Getting Started
1. **Register/Login**: Create a new account or login with existing credentials
2. **Add Transactions**: Use the "Add Transaction" page to manually enter transactions
3. **Import Data**: Upload CSV files with transaction data
4. **View Dashboard**: Check your financial overview and insights
5. **Manage Transactions**: View, filter, and delete transactions as needed

### CSV Import Format
When importing CSV files, ensure they have the following columns:
- **Description**: Transaction description
- **Amount**: Transaction amount (positive numbers)
- **Type**: "income" or "expense"
- **Date**: Transaction date in YYYY-MM-DD format

Example CSV:
```csv
Description,Amount,Type,Date
Salary,5000,income,2024-01-15
Grocery Shopping,150,expense,2024-01-16
Netflix Subscription,15,expense,2024-01-17
```

### Transaction Categories
The system automatically categorizes transactions based on keywords:
- **Groceries**: food, grocery, supermarket, market, fresh, organic, produce
- **Transportation**: uber, lyft, taxi, gas, fuel, parking, metro, bus, train
- **Entertainment**: movie, theater, concert, game, netflix, spotify, amazon prime
- **Utilities**: electric, water, gas, internet, phone, cable, wifi
- **Shopping**: amazon, walmart, target, clothing, shoes, electronics
- **Dining**: restaurant, cafe, coffee, pizza, burger, sushi, dinner, lunch
- **Healthcare**: pharmacy, doctor, medical, dental, vision, insurance
- **Education**: book, course, tuition, school, college, university
- **Travel**: hotel, flight, airbnb, vacation, trip, booking



## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login

### Transactions
- `GET /transactions` - Get user transactions
- `POST /transactions` - Add new transaction
- `DELETE /transactions/<id>` - Delete transaction

### Analytics
- `GET /analytics` - Get financial analytics and insights

### File Upload
- `POST /upload` - Upload CSV file with transactions

## Security Features

- **Password Hashing**: All passwords are hashed using SHA-256
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Server-side validation for all inputs
- **SQL Injection Protection**: Parameterized queries
- **CORS Support**: Cross-origin resource sharing enabled

## Machine Learning Features

The application uses a simple but effective NLP-based classification system:

1. **Keyword Matching**: Predefined keywords for each category
2. **Text Processing**: Lowercase conversion and exact matching
3. **Fallback Category**: "other" for unmatched transactions
4. **Extensible**: Easy to add new categories and keywords

## Future Enhancements

- Integration with financial APIs (Plaid, Stripe)
- Advanced machine learning models
- Budget setting and tracking
- Export functionality (PDF reports)
- Multi-currency support
- Recurring transaction detection
- Advanced analytics and forecasting

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change the port in app.py
   app.run(debug=True, host='0.0.0.0', port=5001)
   ```

2. **Database errors**
   ```bash
   # Delete finance.db and restart the application
   rm finance.db
   python app.py
   ```

3. **Import errors**
   - Ensure CSV format matches the required structure
   - Check that all required columns are present
   - Verify date format is YYYY-MM-DD

### Browser Compatibility
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

