from datetime import timedelta
from flask import jsonify, request

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
    current_user
)

from App.database import db
from App.models import User, Student


ACCESS_EXPIRES = timedelta(hours=2)
REFRESH_EXPIRES = timedelta(days=7)


def setup_jwt(app):
    jwt = JWTManager(app)

    @jwt.user_lookup_loader
    def _user_lookup(_jwt_header, jwt_data):
        identity = jwt_data.get("sub")
        if identity is None:
            return None
        return User.query.filter_by(id=identity).first()

    @jwt.additional_claims_loader
    def _add_claims(identity):
        user = User.query.filter_by(id=identity).first()
        if not user:
            return {}
        return {"role": user.role}

    return jwt


def add_auth_context(app):
    @app.context_processor
    def _inject_auth():
        authenticated = False
        user_obj = None
        try:
            verify_jwt_in_request(optional=True)
            if get_jwt_identity() is not None and current_user is not None:
                authenticated = True
                user_obj = current_user
        except Exception:
            authenticated = False
            user_obj = None

        return {
            "is_authenticated": authenticated,
            "current_user": user_obj
        }


def _json_error(message, status=400, extra=None):
    payload = {"error": message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _issue_tokens(user):
    access = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role},
        expires_delta=ACCESS_EXPIRES
    )
    refresh = create_refresh_token(
        identity=user.id,
        additional_claims={"role": user.role},
        expires_delta=REFRESH_EXPIRES
    )
    return access, refresh


def register_student(payload=None):
    data = payload if payload is not None else (request.get_json(silent=True) or {})

    required = ["email", "password", "first_name", "last_name", "student_id", "degree"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _json_error("Missing required fields", 400, {"missing": missing})

    email = str(data["email"]).strip().lower()
    password = str(data["password"])
    first_name = str(data["first_name"]).strip()
    last_name = str(data["last_name"]).strip()
    student_id = str(data["student_id"]).strip()
    degree = str(data["degree"]).strip()

    if User.query.filter_by(email=email).first():
        return _json_error("Email already registered", 409)

    if Student.query.filter_by(student_id=student_id).first():
        return _json_error("Student ID already registered", 409)

    try:
        student = Student(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            student_id=student_id,
            degree=degree,
            role="student"
        )

        if data.get("phone") is not None:
            student.phone = str(data["phone"]).strip()

        if data.get("gender") is not None:
            student.gender = str(data["gender"]).strip()

        if data.get("gpa") is not None:
            student.gpa = float(data["gpa"])

        if data.get("year_of_study") is not None:
            student.year_of_study = int(data["year_of_study"])

        db.session.add(student)
        db.session.commit()

    except ValueError as e:
        db.session.rollback()
        return _json_error(str(e), 400)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to register student", 500)

    access, refresh = _issue_tokens(student)

    return jsonify({
        "message": "Student registered",
        "user": student.get_json(),
        "access_token": access,
        "refresh_token": refresh
    }), 201


def login(payload=None):
    data = payload if payload is not None else (request.get_json(silent=True) or {})

    email = (data.get("email") or data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return _json_error("Email and password are required", 400)

    user = User.query.filter_by(email=email).first()
    if not user:
        return _json_error("Invalid credentials", 401)

    if not user.is_active:
        return _json_error("Account is disabled", 403)

    if not user.check_password(password):
        return _json_error("Invalid credentials", 401)

    try:
        user.update_last_login()
    except Exception:
        db.session.rollback()

    access, refresh = _issue_tokens(user)

    return jsonify({
        "message": "Login successful",
        "user": user.get_json(),
        "access_token": access,
        "refresh_token": refresh
    }), 200


def whoami():
    try:
        verify_jwt_in_request()
    except Exception:
        return _json_error("Not authenticated", 401)

    identity = get_jwt_identity()
    if identity is None:
        return _json_error("Not authenticated", 401)

    user = User.query.filter_by(id=identity).first()
    if not user:
        return _json_error("User not found", 404)

    return jsonify({"user": user.get_json()}), 200