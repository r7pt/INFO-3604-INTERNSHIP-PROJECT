import os
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, current_user

from App.database import db
from App.models.company import Company
from App.models.project import Project
from App.models.shortlist import Shortlist
from App.models.studentevaluation import StudentEvaluation
from App.controllers.auth import login

company_views = Blueprint('company_views', __name__, url_prefix='/api/company')


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _require_company():
    if current_user is None:
        return None, _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'company':
        return None, _json_error('Forbidden – company access only', 403)
    company = Company.query.filter_by(email=current_user.email).first()
    if company is None:
        return None, _json_error('Company profile not found', 404)
    return company, None



@company_views.post('/login')
def api_company_login():
    return login()


@company_views.post('/register')
def api_company_register():
    data = request.get_json(silent=True) or {}
    required = ['company_name', 'email', 'password']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})

    from App.models.user import User
    from App.models.companyRegistration import CompanyRegistration

    email = str(data['email']).strip().lower()

    if User.query.filter_by(email=email).first():
        return _json_error('Email already registered', 409)

    try:
        from App.models.user import User as BaseUser
        from werkzeug.security import generate_password_hash
        user = BaseUser(email=email, password=data['password'], role='company')
        db.session.add(user)

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

    from App.controllers.auth import _issue_tokens
    access, refresh = _issue_tokens(user)
    return jsonify({
        'message': 'Company registered successfully',
        'company': company.get_json(),
        'access_token': access,
        'refresh_token': refresh
    }), 201



@company_views.get('/me')
@jwt_required()
def api_company_me():
    company, err = _require_company()
    if err:
        return err
    return jsonify({'company': company.get_json()}), 200




@company_views.get('/projects')
@jwt_required()
def api_company_projects():
    company, err = _require_company()
    if err:
        return err
    projects = Project.query.filter_by(company_id=company.id).order_by(Project.created_at.desc()).all()
    return jsonify({'projects': [p.get_json() for p in projects]}), 200


@company_views.post('/projects')
@jwt_required()
def api_company_create_project():
    company, err = _require_company()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    required = ['project_name', 'number_of_interns']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})

    try:
        project = Project(
            project_name=str(data['project_name']).strip(),
            number_of_interns=int(data['number_of_interns']),
            description=data.get('description'),
            details=data.get('details'),
            stipend=float(data['stipend']) if data.get('stipend') else None,
            place_of_work=bool(data.get('place_of_work', False)),
            international_students=bool(data.get('international_students', False)),
            hired_after=bool(data.get('hired_after', False)),
            covid_vaccination=bool(data.get('covid_vaccination', False)),
            company_id=company.id
        )
        db.session.add(project)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _json_error('Failed to create project', 500)

    return jsonify({'message': 'Project created', 'project': project.get_json()}), 201


@company_views.delete('/projects/<int:project_id>')
@jwt_required()
def api_company_delete_project(project_id):
    company, err = _require_company()
    if err:
        return err

    project = db.session.get(Project, project_id)
    if project is None or project.company_id != company.id:
        return _json_error('Project not found', 404)

    try:
        db.session.delete(project)
        db.session.commit()
    except Exception:
        db.session.rollback()
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
    return jsonify({'shortlist': [s.get_json() for s in shortlists]}), 200


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
    interview_date_str = data.get('interview_date')
    interview_date = None
    if interview_date_str:
        try:
            interview_date = datetime.fromisoformat(interview_date_str)
        except ValueError:
            return _json_error('Invalid interview_date format. Use ISO 8601 (e.g. 2025-06-15T10:00:00)', 400)

    try:
        if interview_date:
            shortlist.schedule_interview(interview_date)
        else:
            shortlist.mark_as_interviewed(data.get('notes'))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to update shortlist', 500)

    return jsonify({'message': 'Interview status updated', 'shortlist': shortlist.get_json()}), 200


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
        from App.models.student import Student
        student = db.session.get(Student, shortlist.student_id)
        if student:
            student.current_internship_status = 'hired'
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to hire student', 500)

    return jsonify({'message': 'Student hired successfully', 'shortlist': shortlist.get_json()}), 200


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

    return jsonify({'message': 'Student rejected', 'shortlist': shortlist.get_json()}), 200




@company_views.get('/weekly-reports')
@jwt_required()
def api_company_weekly_reports():
    company, err = _require_company()
    if err:
        return err

    from App.models.weeklyreport import WeeklyReport
    reports = (
        WeeklyReport.query
        .join(Project)
        .filter(Project.company_id == company.id)
        .order_by(WeeklyReport.submission_date.desc())
        .all()
    )
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200