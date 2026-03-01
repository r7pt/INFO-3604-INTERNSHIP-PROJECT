from flask import Blueprint, jsonify, render_template

index_views = Blueprint('index_views', __name__)

@index_views.get('/')
def home():
    try:
        return render_template('index.html')
    except Exception:
        return jsonify({'message': 'Internship Platform API', 'status': 'ok'}), 200

@index_views.get('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@index_views.get('/student')
def student_portal():
    return render_template('student_portal.html')