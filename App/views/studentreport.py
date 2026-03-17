import os
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, current_user
from datetime import datetime

from App.database import db
from App.controllers.studentevaluation import (
    get_evaluation,
    get_company_evaluations,
    get_project_evaluations,
    get_student_evaluations,
    create_evaluation,
    update_evaluation,
    delete_evaluation,
)

student_report_views = Blueprint('student_report_views', __name__, url_prefix='/api/evaluations')


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _require_staff():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'staff':
        return _json_error('Forbidden — staff access only', 403)
    return None


def _require_company():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'company':
        return _json_error('Forbidden — company access only', 403)
    return None


def _save_pdf(file_storage, subfolder):
    
    if file_storage is None:
        return None, _json_error('No file provided', 400)
    safe_name = secure_filename(file_storage.filename or '')
    if not safe_name.lower().endswith('.pdf'):
        return None, _json_error('Only PDF files are allowed', 400)
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    final_name = f"{ts}_{safe_name}"
    target_dir = os.path.join(
        current_app.instance_path, 'uploads', 'evaluations', str(subfolder)
    )
    os.makedirs(target_dir, exist_ok=True)
    abs_path = os.path.join(target_dir, final_name)
    file_storage.save(abs_path)
    rel_path = os.path.relpath(abs_path, current_app.root_path).replace('\\', '/')
    return rel_path, None



@student_report_views.get('/my')
@jwt_required()
def api_student_my_evaluations():

    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden — student access only', 403)

    evaluations = get_student_evaluations(current_user.id)
    return jsonify({'evaluations': [e.get_json() for e in evaluations]}), 200


@student_report_views.get('/my/<int:evaluation_id>')
@jwt_required()
def api_student_single_evaluation(evaluation_id):
    """Student views one of their own evaluations."""
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden — student access only', 403)

    evaluation = get_evaluation(evaluation_id)
    if evaluation is None:
        return _json_error('Evaluation not found', 404)
    if evaluation.student_id != current_user.id:
        return _json_error('Forbidden — this is not your evaluation', 403)

    return jsonify({'evaluation': evaluation.get_json()}), 200


@student_report_views.post('/submit')
@jwt_required()
def api_company_submit_evaluation():
    
    err = _require_company()
    if err:
        return err

    student_id = request.form.get('student_id')
    project_id = request.form.get('project_id')
    if not student_id or not project_id:
        return _json_error('student_id and project_id are required', 400)

    file_obj = request.files.get('file')
    rel_path, file_err = _save_pdf(file_obj, current_user.id)
    if file_err:
        return file_err

    def _bool(val):
        if val is None:
            return None
        return str(val).lower() == 'true'

    def _float(val):
        try:
            return float(val) if val not in (None, '') else None
        except (ValueError, TypeError):
            return None

    completion_date = None
    raw_date = request.form.get('completion_date')
    if raw_date:
        try:
            completion_date = datetime.strptime(raw_date, '%Y-%m-%d')
        except ValueError:
            return _json_error('completion_date must be YYYY-MM-DD', 400)

    result = create_evaluation(
        company_id=current_user.id,
        student_id=int(student_id),
        project_id=int(project_id),
        evaluation_form_path=rel_path,
        evaluation_period=request.form.get('evaluation_period', 'final'),
        evaluator_name=request.form.get('evaluator_name'),
        evaluator_title=request.form.get('evaluator_title'),
        evaluator_email=request.form.get('evaluator_email'),
        overall_rating=_float(request.form.get('overall_rating')),
        technical_skills_rating=_float(request.form.get('technical_skills_rating')),
        communication_rating=_float(request.form.get('communication_rating')),
        professionalism_rating=_float(request.form.get('professionalism_rating')),
        teamwork_rating=_float(request.form.get('teamwork_rating')),
        problem_solving_rating=_float(request.form.get('problem_solving_rating')),
        strengths=request.form.get('strengths'),
        areas_for_improvement=request.form.get('areas_for_improvement'),
        comments=request.form.get('comments'),
        recommend_for_future_employment=_bool(request.form.get('recommend_for_future_employment')),
        would_hire_again=_bool(request.form.get('would_hire_again')),
        internship_completed=_bool(request.form.get('internship_completed')) if request.form.get('internship_completed') else True,
        completion_date=completion_date,
        status='submitted'
    )

    if result == 'duplicate':
        return _json_error(
            'An evaluation for this student, project, and period already exists.', 409
        )
    if result is None:
        return _json_error(
            'Could not submit evaluation. Ensure this student is on your project.', 400
        )

    return jsonify({
        'message': 'Evaluation submitted successfully',
        'evaluation': result.get_json()
    }), 201


@student_report_views.put('/<int:evaluation_id>')
@jwt_required()
def api_company_update_evaluation(evaluation_id):

    err = _require_company()
    if err:
        return err

    evaluation = get_evaluation(evaluation_id)
    if evaluation is None:
        return _json_error('Evaluation not found', 404)
    if evaluation.company_id != current_user.id:
        return _json_error('Forbidden — this is not your evaluation', 403)

    
    new_path = None
    if request.files.get('file'):
        new_path, file_err = _save_pdf(request.files['file'], current_user.id)
        if file_err:
            return file_err

    
    form = request.form if request.form else (request.get_json(silent=True) or {})

    def _bool(val):
        if val is None:
            return None
        return str(val).lower() == 'true'

    def _float(val):
        try:
            return float(val) if val not in (None, '') else None
        except (ValueError, TypeError):
            return None

    completion_date = None
    raw_date = form.get('completion_date')
    if raw_date:
        try:
            completion_date = datetime.strptime(raw_date, '%Y-%m-%d')
        except ValueError:
            return _json_error('completion_date must be YYYY-MM-DD', 400)

    updated = update_evaluation(
        evaluation_id=evaluation_id,
        company_id=current_user.id,
        evaluation_form_path=new_path,
        evaluation_period=form.get('evaluation_period'),
        evaluator_name=form.get('evaluator_name'),
        evaluator_title=form.get('evaluator_title'),
        evaluator_email=form.get('evaluator_email'),
        overall_rating=_float(form.get('overall_rating')),
        technical_skills_rating=_float(form.get('technical_skills_rating')),
        communication_rating=_float(form.get('communication_rating')),
        professionalism_rating=_float(form.get('professionalism_rating')),
        teamwork_rating=_float(form.get('teamwork_rating')),
        problem_solving_rating=_float(form.get('problem_solving_rating')),
        strengths=form.get('strengths'),
        areas_for_improvement=form.get('areas_for_improvement'),
        comments=form.get('comments'),
        recommend_for_future_employment=_bool(form.get('recommend_for_future_employment')),
        would_hire_again=_bool(form.get('would_hire_again')),
        internship_completed=_bool(form.get('internship_completed')),
        completion_date=completion_date,
        status=form.get('status')
    )

    if updated is None:
        return _json_error('Update failed', 500)

    return jsonify({'message': 'Evaluation updated', 'evaluation': updated.get_json()}), 200


@student_report_views.delete('/<int:evaluation_id>')
@jwt_required()
def api_company_delete_evaluation(evaluation_id):
    err = _require_company()
    if err:
        return err

    deleted = delete_evaluation(evaluation_id, company_id=current_user.id)
    if not deleted:
        return _json_error('Evaluation not found or forbidden', 404)

    return jsonify({'message': 'Evaluation deleted'}), 200


@student_report_views.get('/company/my-submissions')
@jwt_required()
def api_company_my_submissions():
    err = _require_company()
    if err:
        return err

    evaluations = get_company_evaluations(current_user.id)
    return jsonify({'evaluations': [e.get_json() for e in evaluations]}), 200


@student_report_views.get('/company/project/<int:project_id>')
@jwt_required()
def api_company_project_evaluations(project_id):
    err = _require_company()
    if err:
        return err

    evaluations = get_project_evaluations(project_id, company_id=current_user.id)
    return jsonify({'evaluations': [e.get_json() for e in evaluations]}), 200



@student_report_views.get('/')
@jwt_required()
def api_staff_list_all():
    err = _require_staff()
    if err:
        return err

    from App.models.studentevaluation import StudentEvaluation
    evaluations = db.session.scalars(db.select(StudentEvaluation)).all()
    return jsonify({'evaluations': [e.get_json() for e in evaluations]}), 200


@student_report_views.get('/<int:evaluation_id>')
@jwt_required()
def api_staff_get_evaluation(evaluation_id):
    err = _require_staff()
    if err:
        return err

    evaluation = get_evaluation(evaluation_id)
    if evaluation is None:
        return _json_error('Evaluation not found', 404)

    data = evaluation.get_json()
    data['student'] = evaluation.student.get_json() if evaluation.student else None
    data['company'] = evaluation.company.get_json() if evaluation.company else None
    data['project'] = evaluation.project.get_json() if evaluation.project else None

    return jsonify({'evaluation': data}), 200


@student_report_views.get('/student/<int:student_id>')
@jwt_required()
def api_staff_student_evaluations(student_id):
    err = _require_staff()
    if err:
        return err

    evaluations = get_student_evaluations(student_id)
    return jsonify({'evaluations': [e.get_json() for e in evaluations]}), 200


@student_report_views.get('/project/<int:project_id>')
@jwt_required()
def api_staff_project_evaluations(project_id):
    err = _require_staff()
    if err:
        return err

    evaluations = get_project_evaluations(project_id)
    return jsonify({'evaluations': [e.get_json() for e in evaluations]}), 200


@student_report_views.put('/staff/<int:evaluation_id>')
@jwt_required()
def api_staff_update_evaluation(evaluation_id):
    err = _require_staff()
    if err:
        return err

    evaluation = get_evaluation(evaluation_id)
    if evaluation is None:
        return _json_error('Evaluation not found', 404)

    data = request.get_json(silent=True) or {}

    def _bool(val):
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        return str(val).lower() == 'true'

    def _float(val):
        try:
            return float(val) if val not in (None, '') else None
        except (ValueError, TypeError):
            return None

    completion_date = None
    raw_date = data.get('completion_date')
    if raw_date:
        try:
            completion_date = datetime.strptime(raw_date, '%Y-%m-%d')
        except ValueError:
            return _json_error('completion_date must be YYYY-MM-DD', 400)

    updated = update_evaluation(
        evaluation_id=evaluation_id,
        evaluation_period=data.get('evaluation_period'),
        evaluator_name=data.get('evaluator_name'),
        evaluator_title=data.get('evaluator_title'),
        evaluator_email=data.get('evaluator_email'),
        overall_rating=_float(data.get('overall_rating')),
        technical_skills_rating=_float(data.get('technical_skills_rating')),
        communication_rating=_float(data.get('communication_rating')),
        professionalism_rating=_float(data.get('professionalism_rating')),
        teamwork_rating=_float(data.get('teamwork_rating')),
        problem_solving_rating=_float(data.get('problem_solving_rating')),
        strengths=data.get('strengths'),
        areas_for_improvement=data.get('areas_for_improvement'),
        comments=data.get('comments'),
        recommend_for_future_employment=_bool(data.get('recommend_for_future_employment')),
        would_hire_again=_bool(data.get('would_hire_again')),
        internship_completed=_bool(data.get('internship_completed')),
        completion_date=completion_date,
        status=data.get('status')
    )

    if updated is None:
        return _json_error('Update failed', 500)

    return jsonify({'message': 'Evaluation updated', 'evaluation': updated.get_json()}), 200