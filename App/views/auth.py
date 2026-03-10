from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from App.controllers.auth import register_student, login

auth_views = Blueprint('auth_views', __name__, url_prefix='/api/auth')


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


@auth_views.post('/register/student')
def api_register_student():
    return register_student()


@auth_views.post('/register/company')
def api_register_company():
    from App.controllers.company import create_company
    from App.models.user import User
    from App.database import db
    from App.controllers.auth import _issue_tokens

    data = request.get_json(silent=True) or {}
    required = ['company_name', 'email', 'password']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})

    email = str(data['email']).strip().lower()

    if User.query.filter_by(email=email).first():
        return _json_error('Email already registered', 409)

    try:
        user = User(email=email, password=data['password'], role='company')
        db.session.add(user)
        db.session.flush()

        from App.models.company import Company
        company = Company(
            company_name=str(data['company_name']).strip(),
            email=email,
            website=data.get('website'),
            category=data.get('category')
        )
        db.session.add(company)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _json_error('Registration failed', 500)

    access, refresh = _issue_tokens(user)
    return jsonify({
        'message': 'Company registered successfully',
        'company': company.get_json(),
        'access_token': access,
        'refresh_token': refresh
    }), 201


@auth_views.post('/register/staff')
def api_register_staff():
    from App.models.staff import Staff
    from App.models.user import User
    from App.database import db
    from App.controllers.auth import _issue_tokens

    data = request.get_json(silent=True) or {}
    required = ['email', 'password', 'first_name', 'last_name', 'department']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})

    email = str(data['email']).strip().lower()
    if User.query.filter_by(email=email).first():
        return _json_error('Email already registered', 409)

    try:
        staff = Staff(
            email=email,
            password=data['password'],
            first_name=str(data['first_name']).strip(),
            last_name=str(data['last_name']).strip(),
            department=str(data['department']).strip(),
            role='staff'
        )
        db.session.add(staff)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to register staff', 500)

    access, refresh = _issue_tokens(staff)
    return jsonify({
        'message': 'Staff account created',
        'user': staff.get_json(),
        'access_token': access,
        'refresh_token': refresh
    }), 201



@auth_views.post('/login')
def api_login():
    return login()



@auth_views.get('/me')
@jwt_required()
def api_whoami():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    return jsonify({'user': current_user.get_json()}), 200



@auth_views.post('/refresh')
@jwt_required(refresh=True)
def api_refresh():
    from App.controllers.auth import _issue_tokens
    if current_user is None:
        return _json_error('Not authenticated', 401)
    access, _ = _issue_tokens(current_user)
    return jsonify({'access_token': access}), 200
