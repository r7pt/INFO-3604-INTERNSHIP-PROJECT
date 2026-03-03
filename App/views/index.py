from flask import Blueprint, jsonify, render_template

index_views = Blueprint('index_views', __name__)

@index_views.get('/')

def home():
    return render_template('index.html')

@index_views.get('/login')

def login_page():
    return render_template('login.html')

@index_views.get('/health')

def health():
    return jsonify({'status': 'ok'}), 200

@index_views.get('/student')
def student_portal():
    return render_template('student_portal.html')