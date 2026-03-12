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
from App.controllers.document import DocumentController
from App.controllers.project import (
    get_company_projects,
    create_project,
    delete_project
)
from App.controllers.evaluation import (
    get_company_evaluations,
    get_project_evaluations,
    get_student_evaluations,
    create_evaluation
)

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


def _parse_bool(value, default=None):
    if value is None:
        return default
    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()
    if text in ['true', '1', 'yes', 'y', 'on']:
        return True
    if text in ['false', '0', 'no', 'n', 'off']:
        return False
    return default


def _parse_float(value, field_name):
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} must be a number')


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

    projects = get_company_projects(company.id)
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
        stipend = float(data['stipend']) if data.get('stipend') else None
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

    if not delete_project(project_id, company.id):
        return _json_error('Failed to delete project', 500)

    return jsonify({'message': 'Project deleted'}), 200


@company_views.get('/evaluations')
@jwt_required()
def api_company_evaluations():
    company, err = _require_company()
    if err:
        return err

    project_id = request.args.get('project_id')
    student_id = request.args.get('student_id')

    if project_id:
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            return _json_error('project_id must be an integer', 400)

        project = db.session.get(Project, project_id)
        if project is None or project.company_id != company.id:
            return _json_error('Project not found', 404)

        evaluations = get_project_evaluations(project_id, company.id)
    elif student_id:
        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return _json_error('student_id must be an integer', 400)

        evaluations = get_student_evaluations(student_id, company.id)
    else:
        evaluations = get_company_evaluations(company.id)

    return jsonify({'evaluations': [e.get_json() for e in evaluations]}), 200


@company_views.post('/evaluations')
@jwt_required()
def api_company_create_evaluation():
    company, err = _require_company()
    if err:
        return err

    file_obj = request.files.get('file')
    project_id = request.form.get('project_id')
    student_id = request.form.get('student_id')
    evaluation_period = request.form.get('evaluation_period') or 'final'

    if not project_id or not student_id:
        data = request.get_json(silent=True) or {}
        project_id = project_id or data.get('project_id')
        student_id = student_id or data.get('student_id')
        evaluation_period = request.form.get('evaluation_period') or data.get('evaluation_period') or 'final'
    else:
        data = {}

    if not project_id or not student_id:
        return _json_error('project_id and student_id are required', 400)

    try:
        project_id = int(project_id)
    except (TypeError, ValueError):
        return _json_error('project_id must be an integer', 400)

    try:
        student_id = int(student_id)
    except (TypeError, ValueError):
        return _json_error('student_id must be an integer', 400)

    project = db.session.get(Project, project_id)
    if project is None or project.company_id != company.id:
        return _json_error('Project not found', 404)

    existing = StudentEvaluation.query.filter_by(
        student_id=student_id,
        project_id=project_id,
        evaluation_period=evaluation_period
    ).first()

    if existing is not None:
        return _json_error('Evaluation already exists for this student, project, and period', 409)

    try:
        rel_path = DocumentController.save_pdf_document(
            file_storage=file_obj,
            owner_id=company.id,
            category='evaluations',
            filename_prefix=f"evaluation_{student_id}_{project_id}_{evaluation_period}"
        )
    except ValueError as e:
        return _json_error(str(e), 400)
    except Exception:
        return _json_error('Failed to save evaluation form', 500)

    source = request.form if request.form else data

    try:
        overall_rating = _parse_float(source.get('overall_rating'), 'overall_rating')
        technical_skills_rating = _parse_float(source.get('technical_skills_rating'), 'technical_skills_rating')
        communication_rating = _parse_float(source.get('communication_rating'), 'communication_rating')
        professionalism_rating = _parse_float(source.get('professionalism_rating'), 'professionalism_rating')
        teamwork_rating = _parse_float(source.get('teamwork_rating'), 'teamwork_rating')
        problem_solving_rating = _parse_float(source.get('problem_solving_rating'), 'problem_solving_rating')
    except ValueError as e:
        return _json_error(str(e), 400)

    completion_date = None
    completion_date_raw = source.get('completion_date')
    if completion_date_raw:
        try:
            completion_date = datetime.fromisoformat(completion_date_raw)
        except ValueError:
            return _json_error('Invalid completion_date format. Use ISO 8601 (e.g. 2026-03-12T14:30:00)', 400)

    evaluation = create_evaluation(
        company_id=company.id,
        student_id=student_id,
        project_id=project_id,
        evaluation_form_path=rel_path,
        evaluation_period=evaluation_period,
        evaluator_name=source.get('evaluator_name'),
        evaluator_title=source.get('evaluator_title'),
        evaluator_email=source.get('evaluator_email'),
        overall_rating=overall_rating,
        technical_skills_rating=technical_skills_rating,
        communication_rating=communication_rating,
        professionalism_rating=professionalism_rating,
        teamwork_rating=teamwork_rating,
        problem_solving_rating=problem_solving_rating,
        strengths=source.get('strengths'),
        areas_for_improvement=source.get('areas_for_improvement'),
        comments=source.get('comments'),
        recommend_for_future_employment=_parse_bool(source.get('recommend_for_future_employment')),
        would_hire_again=_parse_bool(source.get('would_hire_again')),
        internship_completed=_parse_bool(source.get('internship_completed'), True),
        completion_date=completion_date,
        status=source.get('status') or 'submitted'
    )

    if evaluation == 'duplicate':
        return _json_error('Evaluation already exists for this student, project, and period', 409)

    if evaluation is None:
        return _json_error('Failed to create evaluation', 500)

    return jsonify({'message': 'Evaluation submitted', 'evaluation': evaluation.get_json()}), 201


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
            return _json_error('Invalid interview_date format. Use ISO 8601 (e.g. 2026-03-12T14:30:00)', 400)

    try:
        if interview_date:
            shortlist.schedule_interview(interview_date)
        else:
            shortlist.mark_as_interviewed(data.get('notes'))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to update shortlist', 500)

    return jsonify({'message': 'Shortlist updated', 'shortlist': shortlist.get_json()}), 200


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
        student = shortlist.student
        if student:
            student.current_internship_status = 'hired'
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to hire student', 500)

    return jsonify({'message': 'Student hired', 'shortlist': shortlist.get_json()}), 200


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