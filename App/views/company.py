from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, current_user, create_access_token, create_refresh_token
from App.database import db
from App.models.company import Company
from App.models.project import Project
from App.models.shortlist import Shortlist
from App.models.weeklyreport import WeeklyReport
from App.controllers.project import get_company_projects, create_project, delete_project

company_views = Blueprint('company_views', __name__, url_prefix='/api/company')


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _require_company():
    if current_user is None:
        return None, _json_error('Not authenticated', 401)
    if not isinstance(current_user, Company):
        return None, _json_error('Forbidden — company access only', 403)
    return current_user, None


def _project_payload(project):
    return {
        **project.get_json(),
        'description': project.description,
        'details': project.details,
        'company_id': project.company_id,
        'company_name': project.company.company_name if getattr(project, 'company', None) else None,
        'registration_id': project.registration_id,
        'created_at': project.created_at.isoformat() if project.created_at else None,
        'updated_at': project.updated_at.isoformat() if project.updated_at else None,
    }


def _student_payload(student):
    data = student.get_json() if student else None
    if not data:
        return None
    data['resume_path'] = getattr(student, 'resume_path', None)
    data['transcript_path'] = getattr(student, 'transcript_path', None)
    data['transcript_summary'] = getattr(student, 'transcript_summary', None)
    return data


def _shortlist_payload(shortlist):
    return {
        **shortlist.get_json(),
        'student': _student_payload(shortlist.student) if shortlist.student else None,
        'project': _project_payload(shortlist.project) if shortlist.project else None,
    }


def _weekly_report_payload(report):
    return {
        **report.get_json(),
        'student': _student_payload(report.student) if report.student else None,
        'project': _project_payload(report.project) if report.project else None,
    }


@company_views.post('/register')
def api_company_register():
    data = request.get_json(silent=True) or {}
    required = ['company_name', 'email', 'password']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})

    email = str(data['email']).strip().lower()

    if Company.query.filter_by(email=email).first():
        return _json_error('Email already registered', 409)

    try:
        company = Company(
            company_name=str(data['company_name']).strip(),
            email=email,
            website=data.get('website'),
            category=data.get('category'),
            password=data['password']
        )
        company.password_hash = generate_password_hash(str(data['password']), method='pbkdf2:sha256')
        db.session.add(company)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Company registration error: {e}")
        return _json_error('Registration failed', 500)

    access = create_access_token(identity=f'company:{company.id}', additional_claims={'role': 'company'})
    refresh = create_refresh_token(identity=f'company:{company.id}')

    return jsonify({
        'message': 'Company registered successfully',
        'company': company.get_json(),
        'access_token': access,
        'refresh_token': refresh
    }), 201


@company_views.post('/login')
def api_company_login():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))

    if not email or not password:
        return _json_error('Email and password are required', 400)

    company = Company.query.filter_by(email=email).first()
    if company is None or not check_password_hash(company.password_hash, password):
        return _json_error('Invalid email or password', 401)

    access = create_access_token(identity=f'company:{company.id}', additional_claims={'role': 'company'})
    refresh = create_refresh_token(identity=f'company:{company.id}')

    return jsonify({
        'message': 'Login successful',
        'company': company.get_json(),
        'access_token': access,
        'refresh_token': refresh
    }), 200


@company_views.get('/me')
@jwt_required()
def api_company_me():
    company, err = _require_company()
    if err:
        return err
    payload = company.get_json()
    payload['project_count'] = len(company.projects or [])
    return jsonify({'company': payload}), 200


@company_views.get('/projects')
@jwt_required()
def api_company_projects():
    company, err = _require_company()
    if err:
        return err
    projects = get_company_projects(company.id)
    return jsonify({'projects': [_project_payload(p) for p in projects]}), 200


@company_views.post('/projects')
@jwt_required()
def api_company_create_project():
    company, err = _require_company()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    missing = [k for k in ['project_name', 'number_of_interns'] if not data.get(k)]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})

    try:
        stipend = float(data['stipend']) if data.get('stipend') not in [None, ''] else None
    except (TypeError, ValueError):
        return _json_error('stipend must be a number', 400)

    try:
        number_of_interns = int(data['number_of_interns'])
    except (TypeError, ValueError):
        return _json_error('number_of_interns must be an integer', 400)

    project = create_project(
        company_id=company.id,
        project_name=str(data['project_name']).strip(),
        number_of_interns=number_of_interns,
        description=data.get('description'),
        details=data.get('details'),
        stipend=stipend,
        place_of_work=bool(data.get('place_of_work', False)),
        international_students=bool(data.get('international_students', False)),
        hired_after=bool(data.get('hired_after', False)),
        covid_vaccination=bool(data.get('covid_vaccination', False))
    )

    if project is None:
        return _json_error('Failed to create project', 500)

    project = db.session.get(Project, project.id)
    return jsonify({'message': 'Project created', 'project': _project_payload(project)}), 201


@company_views.delete('/projects/<int:project_id>')
@jwt_required()
def api_company_delete_project(project_id):
    company, err = _require_company()
    if err:
        return err

    project = db.session.get(Project, project_id)
    if project is None or project.company_id != company.id:
        return _json_error('Project not found', 404)

    if not delete_project(project_id, company.id):
        return _json_error('Failed to delete project', 500)

    return jsonify({'message': 'Project deleted'}), 200


@company_views.get('/shortlist')
@jwt_required()
def api_company_shortlist():
    company, err = _require_company()
    if err:
        return err

    shortlists = (
        Shortlist.query
        .join(Project)
        .filter(Project.company_id == company.id)
        .order_by(Shortlist.created_at.desc())
        .all()
    )
    return jsonify({'shortlist': [_shortlist_payload(s) for s in shortlists]}), 200


@company_views.get('/weekly-reports')
@jwt_required()
def api_company_weekly_reports():
    company, err = _require_company()
    if err:
        return err

    reports = (
        WeeklyReport.query
        .join(Project)
        .filter(Project.company_id == company.id)
        .order_by(WeeklyReport.submission_date.desc())
        .all()
    )
    return jsonify({'weekly_reports': [_weekly_report_payload(r) for r in reports]}), 200


@company_views.post('/shortlist/<int:shortlist_id>/interview')
@jwt_required()
def api_company_select_for_interview(shortlist_id):
    company, err = _require_company()
    if err:
        return err

    shortlist = db.session.get(Shortlist, shortlist_id)
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    project = db.session.get(Project, shortlist.project_id)
    if project is None or project.company_id != company.id:
        return _json_error('Forbidden', 403)

    data = request.get_json(silent=True) or {}
    interview_date = None
    if data.get('interview_date'):
        try:
            interview_date = datetime.fromisoformat(data['interview_date'])
        except ValueError:
            return _json_error('Invalid interview_date format. Use ISO 8601', 400)

    try:
        if interview_date:
            shortlist.schedule_interview(interview_date)
        else:
            shortlist.mark_as_interviewed(data.get('notes'))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to update shortlist', 500)

    return jsonify({'message': 'Shortlist updated', 'shortlist': _shortlist_payload(shortlist)}), 200


@company_views.post('/shortlist/<int:shortlist_id>/hire')
@jwt_required()
def api_company_hire_student(shortlist_id):
    company, err = _require_company()
    if err:
        return err

    shortlist = db.session.get(Shortlist, shortlist_id)
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    project = db.session.get(Project, shortlist.project_id)
    if project is None or project.company_id != company.id:
        return _json_error('Forbidden', 403)

    try:
        shortlist.mark_as_hired()
        if shortlist.student:
            shortlist.student.current_internship_status = 'hired'
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to hire student', 500)

    return jsonify({'message': 'Student hired', 'shortlist': _shortlist_payload(shortlist)}), 200


@company_views.post('/shortlist/<int:shortlist_id>/reject')
@jwt_required()
def api_company_reject_student(shortlist_id):
    company, err = _require_company()
    if err:
        return err

    shortlist = db.session.get(Shortlist, shortlist_id)
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    project = db.session.get(Project, shortlist.project_id)
    if project is None or project.company_id != company.id:
        return _json_error('Forbidden', 403)

    data = request.get_json(silent=True) or {}
    try:
        shortlist.mark_as_rejected(reason=data.get('reason'))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to reject student', 500)

    return jsonify({'message': 'Student rejected', 'shortlist': _shortlist_payload(shortlist)}), 200
