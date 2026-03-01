import os
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename

from flask_jwt_extended import jwt_required, current_user

from App.database import db
from App.controllers.auth import register_student, login
from App.controllers.student import (
    upload_student_resume,
    upload_student_transcript,
    get_student_application_status
)
from App.models.project import Project
from App.models.weeklyreport import WeeklyReport


student_views = Blueprint('student_views', __name__, url_prefix='/api/student')


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _ensure_upload_path(student_id, category):
    base_dir = os.path.join(current_app.instance_path, 'uploads', str(student_id), category)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _save_pdf(file_storage, student_id, category, filename_prefix=None):
    if file_storage is None:
        return None, _json_error('Missing file', 400)

    original = file_storage.filename or ''
    safe_name = secure_filename(original)

    if not safe_name.lower().endswith('.pdf'):
        return None, _json_error('Only PDF files are allowed', 400)

    prefix = filename_prefix or category
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    final_name = f"{prefix}_{ts}_{safe_name}"

    target_dir = _ensure_upload_path(student_id, category)
    abs_path = os.path.join(target_dir, final_name)
    file_storage.save(abs_path)

    rel_path = os.path.relpath(abs_path, current_app.root_path)
    rel_path = rel_path.replace('\\', '/')
    return rel_path, None


@student_views.post('/register')
def api_register_student():
    return register_student()


@student_views.post('/login')
def api_login_student():
    return login()


@student_views.get('/me')
@jwt_required()
def api_me():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)
    return jsonify({'user': current_user.get_json()}), 200


@student_views.get('/projects')
def api_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify({'projects': [p.get_json() for p in projects]}), 200


@student_views.get('/status')
@jwt_required()
def api_status():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    status = get_student_application_status(current_user.id)
    if status is None:
        return _json_error('Student not found', 404)
    return jsonify({'status': status}), 200


@student_views.post('/upload/resume')
@jwt_required()
def api_upload_resume():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    file_obj = request.files.get('file')
    rel_path, err = _save_pdf(file_obj, current_user.id, 'resume')
    if err:
        return err

    student = upload_student_resume(current_user.id, rel_path)
    if student is None:
        return _json_error('Failed to save resume', 500)

    return jsonify({'message': 'Resume uploaded', 'user': student.get_json()}), 200


@student_views.post('/upload/transcript')
@jwt_required()
def api_upload_transcript():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    file_obj = request.files.get('file')
    rel_path, err = _save_pdf(file_obj, current_user.id, 'transcript')
    if err:
        return err

    student = upload_student_transcript(current_user.id, rel_path)
    if student is None:
        return _json_error('Failed to save transcript', 500)

    return jsonify({'message': 'Transcript uploaded', 'user': student.get_json()}), 200


@student_views.post('/apply')
@jwt_required()
def api_apply():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    data = request.get_json(silent=True) or {}
    project_id = data.get('project_id')
    if project_id is None:
        return _json_error('project_id is required', 400)

    project = db.session.get(Project, int(project_id))
    if project is None:
        return _json_error('Project not found', 404)

    if not current_user.can_apply_to_project(project):
        return _json_error('Upload resume and transcript before applying', 400)

    current_user.current_internship_status = 'applied'
    db.session.commit()

    return jsonify({'message': 'Application submitted', 'project_id': project.id, 'status': current_user.current_internship_status}), 200


@student_views.get('/weekly-reports')
@jwt_required()
def api_weekly_reports_list():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    reports = WeeklyReport.query.filter_by(student_id=current_user.id).order_by(WeeklyReport.week_number.asc()).all()
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@student_views.post('/weekly-reports')
@jwt_required()
def api_weekly_reports_create():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    file_obj = request.files.get('file')
    project_id = request.form.get('project_id')
    week_number = request.form.get('week_number')

    if not project_id or not week_number:
        data = request.get_json(silent=True) or {}
        project_id = project_id or data.get('project_id')
        week_number = week_number or data.get('week_number')

    if not project_id or not week_number:
        return _json_error('project_id and week_number are required', 400)

    project = db.session.get(Project, int(project_id))
    if project is None:
        return _json_error('Project not found', 404)

    rel_path, err = _save_pdf(file_obj, current_user.id, 'weekly_reports', filename_prefix=f"week{week_number}")
    if err:
        return err

    title = request.form.get('title')
    description = request.form.get('description')
    hours_worked = request.form.get('hours_worked')

    if hours_worked is not None and hours_worked != '':
        try:
            hours_worked = float(hours_worked)
        except ValueError:
            return _json_error('hours_worked must be a number', 400)

    try:
        report = WeeklyReport(
            student_id=current_user.id,
            project_id=project.id,
            week_number=int(week_number),
            report_file_path=rel_path,
            title=title,
            description=description,
            hours_worked=hours_worked
        )
        db.session.add(report)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to create weekly report', 500)

    return jsonify({'message': 'Weekly report uploaded', 'weekly_report': report.get_json()}), 201