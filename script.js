// Global variables
let currentUser = null;
let categoryChart = null;
let monthlyChart = null;

// DOM elements
const authSection = document.getElementById('auth-section');
const appSection = document.getElementById('app-section');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');
const loadingOverlay = document.getElementById('loading-overlay');
const notification = document.getElementById('notification');
const notificationMessage = document.getElementById('notification-message');
const notificationClose = document.getElementById('notification-close');

// Navigation elements
const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

function initializeApp() {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
        currentUser = {
            token: token,
            user_id: localStorage.getItem('user_id'),
            username: localStorage.getItem('username')
        };
        showApp();
        loadDashboard();
    } else {
        showAuth();
    }
}

function setupEventListeners() {
    // Authentication tabs
    loginTab.addEventListener('click', () => switchAuthTab('login'));
    registerTab.addEventListener('click', () => switchAuthTab('register'));
    
    // Authentication forms
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    
    // Navigation
    navItems.forEach(item => {
        item.addEventListener('click', handleNavigation);
    });
    
    // Transaction form
    const transactionForm = document.getElementById('transaction-form');
    if (transactionForm) {
        transactionForm.addEventListener('submit', handleAddTransaction);
    }
    
    // Upload form
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUploadCSV);
    }
    
    // Category auto-detection
    const descriptionInput = document.getElementById('description');
    if (descriptionInput) {
        descriptionInput.addEventListener('input', autoDetectCategory);
    }
    
    // Filters
    const typeFilter = document.getElementById('type-filter');
    const categoryFilter = document.getElementById('category-filter');
    if (typeFilter) typeFilter.addEventListener('change', filterTransactions);
    if (categoryFilter) categoryFilter.addEventListener('change', filterTransactions);
    
    // Notification close
    notificationClose.addEventListener('click', hideNotification);
}

// Authentication functions
function switchAuthTab(tab) {
    if (tab === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
    } else {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    showLoading();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data;
            localStorage.setItem('token', data.token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('username', data.username);
            
            showNotification('Login successful!', 'success');
            showApp();
            loadDashboard();
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        showNotification('Login failed. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

async function handleRegister(e) {
    e.preventDefault();
    showLoading();
    
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data;
            localStorage.setItem('token', data.token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('username', data.username);
            
            showNotification('Registration successful!', 'success');
            showApp();
            loadDashboard();
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        showNotification('Registration failed. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Navigation functions
function handleNavigation(e) {
    const target = e.currentTarget.id;
    
    // Update active navigation
    navItems.forEach(item => item.classList.remove('active'));
    e.currentTarget.classList.add('active');
    
    // Show corresponding page
    pages.forEach(page => page.classList.remove('active'));
    
    switch (target) {
        case 'nav-dashboard':
            document.getElementById('dashboard').classList.add('active');
            loadDashboard();
            break;
        case 'nav-transactions':
            document.getElementById('transactions').classList.add('active');
            loadTransactions();
            break;
        case 'nav-add':
            document.getElementById('add-transaction').classList.add('active');
            break;
        case 'nav-upload':
            document.getElementById('upload-csv').classList.add('active');
            break;
        case 'nav-logout':
            handleLogout();
            break;
    }
}

function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    currentUser = null;
    showAuth();
    showNotification('Logged out successfully', 'success');
}

// API functions
async function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${currentUser.token}`
        }
    };
    
    const response = await fetch(endpoint, { ...defaultOptions, ...options });
    return response;
}

async function loadDashboard() {
    try {
        const response = await apiCall('/analytics');
        const data = await response.json();
        
        if (response.ok) {
            updateDashboard(data);
        } else {
            showNotification('Failed to load dashboard data', 'error');
        }
    } catch (error) {
        showNotification('Error loading dashboard', 'error');
    }
}

function updateDashboard(data) {
    // Update summary cards
    document.getElementById('total-income').textContent = formatCurrency(data.summary.total_income);
    document.getElementById('total-expenses').textContent = formatCurrency(data.summary.total_expenses);
    document.getElementById('net-income').textContent = formatCurrency(data.summary.net_income);
    
    // Update charts
    updateCategoryChart(data.categories);
    updateMonthlyChart(data.recent_transactions);
    
    // Update insights
    updateInsights(data.insights);
}

function updateCategoryChart(categories) {
    const ctx = document.getElementById('category-chart');
    if (!ctx) return;
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    const labels = categories.map(cat => cat.category);
    const data = categories.map(cat => cat.amount);
    const colors = generateColors(labels.length);
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function updateMonthlyChart(transactions) {
    const ctx = document.getElementById('monthly-chart');
    if (!ctx) return;
    
    if (monthlyChart) {
        monthlyChart.destroy();
    }
    
    // Group transactions by date
    const groupedData = {};
    transactions.forEach(transaction => {
        const date = transaction.date;
        if (!groupedData[date]) {
            groupedData[date] = { income: 0, expense: 0 };
        }
        if (transaction.type === 'income') {
            groupedData[date].income += transaction.amount;
        } else {
            groupedData[date].expense += transaction.amount;
        }
    });
    
    const dates = Object.keys(groupedData).sort();
    const incomeData = dates.map(date => groupedData[date].income);
    const expenseData = dates.map(date => groupedData[date].expense);
    
    monthlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    borderColor: '#f44336',
                    backgroundColor: 'rgba(244, 67, 54, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function updateInsights(insights) {
    const container = document.getElementById('insights-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (insights.length === 0) {
        container.innerHTML = '<div class="insight-item">No insights available yet. Add some transactions to get started!</div>';
        return;
    }
    
    insights.forEach(insight => {
        const insightElement = document.createElement('div');
        insightElement.className = 'insight-item';
        insightElement.textContent = insight;
        container.appendChild(insightElement);
    });
}

async function loadTransactions() {
    try {
        const response = await apiCall('/transactions');
        const transactions = await response.json();
        
        if (response.ok) {
            displayTransactions(transactions);
            updateCategoryFilter(transactions);
        } else {
            showNotification('Failed to load transactions', 'error');
        }
    } catch (error) {
        showNotification('Error loading transactions', 'error');
    }
}

function displayTransactions(transactions) {
    const container = document.getElementById('transactions-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (transactions.length === 0) {
        container.innerHTML = '<div class="transaction-item">No transactions found. Add your first transaction!</div>';
        return;
    }
    
    transactions.forEach(transaction => {
        const transactionElement = createTransactionElement(transaction);
        container.appendChild(transactionElement);
    });
}

function createTransactionElement(transaction) {
    const element = document.createElement('div');
    element.className = 'transaction-item';
    element.dataset.id = transaction.id;
    element.dataset.type = transaction.type;
    element.dataset.category = transaction.category;
    
    element.innerHTML = `
        <div class="transaction-info">
            <div class="transaction-description">${transaction.description}</div>
            <div class="transaction-meta">
                <span>${transaction.category}</span>
                <span>${transaction.date}</span>
            </div>
        </div>
        <div class="transaction-amount ${transaction.type}">
            ${transaction.type === 'income' ? '+' : '-'}${formatCurrency(transaction.amount)}
        </div>
        <div class="transaction-actions">
            <button class="btn btn-danger btn-small" onclick="deleteTransaction(${transaction.id})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    
    return element;
}

function updateCategoryFilter(transactions) {
    const categoryFilter = document.getElementById('category-filter');
    if (!categoryFilter) return;
    
    const categories = [...new Set(transactions.map(t => t.category))];
    
    // Clear existing options except "All Categories"
    categoryFilter.innerHTML = '<option value="">All Categories</option>';
    
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categoryFilter.appendChild(option);
    });
}

function filterTransactions() {
    const typeFilter = document.getElementById('type-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;
    const transactions = document.querySelectorAll('.transaction-item');
    
    transactions.forEach(transaction => {
        const type = transaction.dataset.type;
        const category = transaction.dataset.category;
        
        const typeMatch = !typeFilter || type === typeFilter;
        const categoryMatch = !categoryFilter || category === categoryFilter;
        
        transaction.style.display = typeMatch && categoryMatch ? 'flex' : 'none';
    });
}

async function handleAddTransaction(e) {
    e.preventDefault();
    showLoading();
    
    const description = document.getElementById('description').value;
    const amount = parseFloat(document.getElementById('amount').value);
    const type = document.getElementById('type').value;
    const date = document.getElementById('date').value;
    
    try {
        const response = await apiCall('/transactions', {
            method: 'POST',
            body: JSON.stringify({
                description,
                amount,
                type,
                date
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Transaction added successfully!', 'success');
            document.getElementById('transaction-form').reset();
            document.getElementById('category').value = '';
            
            // Reload dashboard and transactions
            loadDashboard();
            loadTransactions();
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to add transaction', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }
    
    try {
        const response = await apiCall(`/transactions/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Transaction deleted successfully!', 'success');
            loadDashboard();
            loadTransactions();
        } else {
            showNotification('Failed to delete transaction', 'error');
        }
    } catch (error) {
        showNotification('Error deleting transaction', 'error');
    }
}

async function handleUploadCSV(e) {
    e.preventDefault();
    showLoading();
    
    const fileInput = document.getElementById('csv-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showNotification('Please select a file', 'error');
        hideLoading();
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(data.message, 'success');
            fileInput.value = '';
            loadDashboard();
            loadTransactions();
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to upload file', 'error');
    } finally {
        hideLoading();
    }
}

function autoDetectCategory() {
    const description = document.getElementById('description').value;
    const categoryInput = document.getElementById('category');
    
    if (description) {
        // Simple category detection based on keywords
        const descriptionLower = description.toLowerCase();
        let detectedCategory = 'other';
        
        const categoryKeywords = {
            'groceries': ['food', 'grocery', 'supermarket', 'market', 'fresh', 'organic', 'produce'],
            'transportation': ['uber', 'lyft', 'taxi', 'gas', 'fuel', 'parking', 'metro', 'bus', 'train'],
            'entertainment': ['movie', 'theater', 'concert', 'game', 'netflix', 'spotify', 'amazon prime'],
            'utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'cable', 'wifi'],
            'shopping': ['amazon', 'walmart', 'target', 'clothing', 'shoes', 'electronics'],
            'dining': ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'sushi', 'dinner', 'lunch'],
            'healthcare': ['pharmacy', 'doctor', 'medical', 'dental', 'vision', 'insurance'],
            'education': ['book', 'course', 'tuition', 'school', 'college', 'university'],
            'travel': ['hotel', 'flight', 'airbnb', 'vacation', 'trip', 'booking']
        };
        
        for (const [category, keywords] of Object.entries(categoryKeywords)) {
            if (keywords.some(keyword => descriptionLower.includes(keyword))) {
                detectedCategory = category;
                break;
            }
        }
        
        categoryInput.value = detectedCategory;
    } else {
        categoryInput.value = '';
    }
}

// Utility functions
function showAuth() {
    authSection.classList.remove('hidden');
    appSection.classList.add('hidden');
}

function showApp() {
    authSection.classList.add('hidden');
    appSection.classList.remove('hidden');
}

function showLoading() {
    loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    loadingOverlay.classList.add('hidden');
}

function showNotification(message, type = 'success') {
    notificationMessage.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideNotification();
    }, 5000);
}

function hideNotification() {
    notification.classList.add('hidden');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function generateColors(count) {
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
        '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56'
    ];
    
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

// Set default date to today
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
});