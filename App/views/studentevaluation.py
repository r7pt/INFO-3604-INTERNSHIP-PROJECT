import os
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, current_user
from werkzeug.utils import secure_filename

from App.database import db
from App.models.company import Company
from App.models.project import Project
from App.models.shortlist import Shortlist
from App.models.student import Student
from App.models.studentevaluation import StudentEvaluation

student_evaluation_views = Blueprint(
    'student_evaluation_views',
    __name__,
    url_prefix='/api/student-evaluations'
)


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


def _require_student():
    if current_user is None:
        return None, _json_error('Not authenticated', 401)

    if getattr(current_user, 'role', None) != 'student':
        return None, _json_error('Forbidden – student access only', 403)

    student = db.session.get(Student, current_user.id)
    if student is None:
        return None, _json_error('Student profile not found', 404)

    return student, None


def _ensure_upload_path(company_id):
    base_dir = os.path.join(
        current_app.instance_path,
        'uploads',
        'companies',
        str(company_id),
        'student_evaluations'
    )
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _save_pdf(file_storage, company_id, student_id, project_id, evaluation_period):
    if file_storage is None:
        return None, _json_error('Missing file', 400)

    original = file_storage.filename or ''
    safe_name = secure_filename(original)

    if not safe_name.lower().endswith('.pdf'):
        return None, _json_error('Only PDF files are allowed', 400)

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    final_name = f"evaluation_{student_id}_{project_id}_{evaluation_period}_{ts}_{safe_name}"

    target_dir = _ensure_upload_path(company_id)
    abs_path = os.path.join(target_dir, final_name)
    file_storage.save(abs_path)

    rel_path = os.path.relpath(abs_path, current_app.root_path)
    rel_path = rel_path.replace('\\', '/')

    return rel_path, None


def _parse_float(value, field_name):
    if value is None or value == '':
        return None, None
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, _json_error(f'{field_name} must be a number', 400)


def _parse_bool(value):
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        return value

    value = str(value).strip().lower()
    if value in ['true', '1', 'yes', 'y', 'on']:
        return True
    if value in ['false', '0', 'no', 'n', 'off']:
        return False
    return None


def _get_request_value(key, default=None):
    if request.form and key in request.form:
        return request.form.get(key, default)

    data = request.get_json(silent=True) or {}
    return data.get(key, default)


@student_evaluation_views.get('/company')
@jwt_required()
def api_company_list_student_evaluations():
    company, err = _require_company()
    if err:
        return err

    evaluations = (
        StudentEvaluation.query
        .filter_by(company_id=company.id)
        .order_by(StudentEvaluation.created_at.desc())
        .all()
    )

    return jsonify({
        'student_evaluations': [evaluation.get_json() for evaluation in evaluations]
    }), 200


@student_evaluation_views.get('/company/<int:evaluation_id>')
@jwt_required()
def api_company_get_student_evaluation(evaluation_id):
    company, err = _require_company()
    if err:
        return err

    evaluation = db.session.get(StudentEvaluation, evaluation_id)
    if evaluation is None or evaluation.company_id != company.id:
        return _json_error('Student evaluation not found', 404)

    return jsonify({'student_evaluation': evaluation.get_json()}), 200


@student_evaluation_views.post('/company')
@jwt_required()
def api_company_create_student_evaluation():
    company, err = _require_company()
    if err:
        return err

    file_obj = request.files.get('file')

    student_id = _get_request_value('student_id')
    project_id = _get_request_value('project_id')
    evaluation_period = _get_request_value('evaluation_period', 'final')

    if not student_id or not project_id:
        return _json_error('student_id and project_id are required', 400)

    try:
        student_id = int(student_id)
        project_id = int(project_id)
    except ValueError:
        return _json_error('student_id and project_id must be integers', 400)

    student = db.session.get(Student, student_id)
    if student is None:
        return _json_error('Student not found', 404)

    project = db.session.get(Project, project_id)
    if project is None:
        return _json_error('Project not found', 404)

    if project.company_id != company.id:
        return _json_error('Forbidden', 403)

    shortlist = Shortlist.query.filter_by(student_id=student.id, project_id=project.id).first()
    if shortlist is None:
        return _json_error('Student is not associated with this project shortlist', 400)

    existing = StudentEvaluation.query.filter_by(
        student_id=student.id,
        project_id=project.id,
        evaluation_period=evaluation_period
    ).first()

    if existing is not None:
        return _json_error(
            'An evaluation already exists for this student, project, and evaluation period',
            409
        )

    rel_path, save_err = _save_pdf(
        file_obj,
        company.id,
        student.id,
        project.id,
        evaluation_period
    )
    if save_err:
        return save_err

    overall_rating, err = _parse_float(_get_request_value('overall_rating'), 'overall_rating')
    if err:
        return err

    technical_skills_rating, err = _parse_float(
        _get_request_value('technical_skills_rating'),
        'technical_skills_rating'
    )
    if err:
        return err

    communication_rating, err = _parse_float(
        _get_request_value('communication_rating'),
        'communication_rating'
    )
    if err:
        return err

    professionalism_rating, err = _parse_float(
        _get_request_value('professionalism_rating'),
        'professionalism_rating'
    )
    if err:
        return err

    teamwork_rating, err = _parse_float(
        _get_request_value('teamwork_rating'),
        'teamwork_rating'
    )
    if err:
        return err

    problem_solving_rating, err = _parse_float(
        _get_request_value('problem_solving_rating'),
        'problem_solving_rating'
    )
    if err:
        return err

    try:
        evaluation = StudentEvaluation(
            company_id=company.id,
            student_id=student.id,
            project_id=project.id,
            evaluation_form_path=rel_path,
            evaluation_period=evaluation_period,
            evaluator_name=_get_request_value('evaluator_name'),
            evaluator_title=_get_request_value('evaluator_title'),
            evaluator_email=_get_request_value('evaluator_email')
        )

        evaluation.overall_rating = overall_rating
        evaluation.technical_skills_rating = technical_skills_rating
        evaluation.communication_rating = communication_rating
        evaluation.professionalism_rating = professionalism_rating
        evaluation.teamwork_rating = teamwork_rating
        evaluation.problem_solving_rating = problem_solving_rating

        evaluation.strengths = _get_request_value('strengths')
        evaluation.areas_for_improvement = _get_request_value('areas_for_improvement')
        evaluation.comments = _get_request_value('comments')

        evaluation.recommend_for_future_employment = _parse_bool(
            _get_request_value('recommend_for_future_employment')
        )
        evaluation.would_hire_again = _parse_bool(
            _get_request_value('would_hire_again')
        )
        evaluation.internship_completed = _parse_bool(
            _get_request_value('internship_completed')
        )
        evaluation.status = _get_request_value('status', 'submitted')

        db.session.add(evaluation)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return _json_error(str(e), 400)
    except Exception:
        db.session.rollback()
        return _json_error('Failed to create student evaluation', 500)

    return jsonify({
        'message': 'Student evaluation created successfully',
        'student_evaluation': evaluation.get_json()
    }), 201


@student_evaluation_views.get('/student')
@jwt_required()
def api_student_list_own_evaluations():
    student, err = _require_student()
    if err:
        return err

    evaluations = (
        StudentEvaluation.query
        .filter_by(student_id=student.id)
        .order_by(StudentEvaluation.created_at.desc())
        .all()
    )

    return jsonify({
        'student_evaluations': [evaluation.get_json() for evaluation in evaluations]
    }), 200


@student_evaluation_views.get('/student/<int:evaluation_id>')
@jwt_required()
def api_student_get_own_evaluation(evaluation_id):
    student, err = _require_student()
    if err:
        return err

    evaluation = db.session.get(StudentEvaluation, evaluation_id)
    if evaluation is None or evaluation.student_id != student.id:
        return _json_error('Student evaluation not found', 404)

    return jsonify({'student_evaluation': evaluation.get_json()}), 200