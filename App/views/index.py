from flask import Blueprint, jsonify, render_template

index_views = Blueprint('index_views', __name__)

@index_views.get('/')
def home():
    return render_template('index.html')

@index_views.get('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@index_views.get('/login')
def login_page():
    return render_template('login.html')

@index_views.get('/register')
@index_views.get('/register/student')
@index_views.get('/register/company')
def register_page():
    return render_template('register.html')

@index_views.get('/student')
@index_views.get('/student/dashboard')
def student_portal():
    return render_template('student_portal.html')

@index_views.get('/company')
@index_views.get('/company/dashboard')
def company_dashboard():
    return render_template('company_dashboard.html')