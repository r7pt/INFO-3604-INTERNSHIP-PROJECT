import os
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, current_user
from datetime import datetime

from App.database import db
from App.controllers.weeklyreport import (
    get_weekly_report, get_all_weekly_reports, get_reports_by_student,
    get_reports_by_project, get_pending_reviews, get_late_reports,
    get_reports_needing_revision, add_staff_feedback, approve_weekly_report,
    request_revision, get_weekly_report_with_details, get_student_report_summary,
    search_weekly_reports, filter_weekly_reports, create_weekly_report
)

weekly_report_views = Blueprint('weekly_report_views', __name__, url_prefix='/api/reports')


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


def _save_pdf(file_storage, student_id, week_number):
    if file_storage is None:
        return None, _json_error('Missing file', 400)
    safe_name = secure_filename(file_storage.filename or '')
    if not safe_name.lower().endswith('.pdf'):
        return None, _json_error('Only PDF files are allowed', 400)
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    final_name = f"week{week_number}_{ts}_{safe_name}"
    target_dir = os.path.join(current_app.instance_path, 'uploads', str(student_id), 'weekly_reports')
    os.makedirs(target_dir, exist_ok=True)
    abs_path = os.path.join(target_dir, final_name)
    file_storage.save(abs_path)
    rel_path = os.path.relpath(abs_path, current_app.root_path).replace('\\', '/')
    return rel_path, None


@weekly_report_views.get('/')
@jwt_required()
def api_list_all_reports():
    err = _require_staff()
    if err: return err
    reports = get_all_weekly_reports()
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@weekly_report_views.get('/<int:report_id>')
@jwt_required()
def api_get_report(report_id):
    err = _require_staff()
    if err: return err
    report = get_weekly_report_with_details(report_id)
    if report is None:
        return _json_error('Report not found', 404)
    return jsonify({'weekly_report': report}), 200


@weekly_report_views.get('/pending')
@jwt_required()
def api_pending_reviews():
    err = _require_staff()
    if err: return err
    reports = get_pending_reviews()
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@weekly_report_views.get('/late')
@jwt_required()
def api_late_reports():
    err = _require_staff()
    if err: return err
    reports = get_late_reports()
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@weekly_report_views.get('/needs-revision')
@jwt_required()
def api_needs_revision():
    err = _require_staff()
    if err: return err
    reports = get_reports_needing_revision()
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@weekly_report_views.get('/student/<int:student_id>')
@jwt_required()
def api_reports_by_student(student_id):
    err = _require_staff()
    if err: return err
    reports = get_reports_by_student(student_id)
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@weekly_report_views.get('/student/<int:student_id>/summary')
@jwt_required()
def api_student_report_summary(student_id):
    err = _require_staff()
    if err: return err
    project_id = request.args.get('project_id')
    if not project_id:
        return _json_error('project_id query parameter is required', 400)
    summary = get_student_report_summary(student_id, int(project_id))
    if summary is None:
        return _json_error('No reports found', 404)
    return jsonify({'summary': summary}), 200


@weekly_report_views.get('/project/<int:project_id>')
@jwt_required()
def api_reports_by_project(project_id):
    err = _require_staff()
    if err: return err
    reports = get_reports_by_project(project_id)
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@weekly_report_views.get('/search')
@jwt_required()
def api_search_reports():
    err = _require_staff()
    if err: return err
    reports = search_weekly_reports(
        student_name=request.args.get('student_name'),
        project_name=request.args.get('project_name')
    )
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@weekly_report_views.get('/filter')
@jwt_required()
def api_filter_reports():
    err = _require_staff()
    if err: return err
    args = request.args
    reports = filter_weekly_reports(
        status=args.get('status'),
        reviewed=args.get('reviewed') == 'true' if args.get('reviewed') else None,
        is_late=args.get('is_late') == 'true' if args.get('is_late') else None,
        min_hours=float(args['min_hours']) if args.get('min_hours') else None,
        max_hours=float(args['max_hours']) if args.get('max_hours') else None,
        start_date=args.get('start_date'),
        end_date=args.get('end_date')
    )
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200



@weekly_report_views.post('/<int:report_id>/feedback')
@jwt_required()
def api_add_feedback(report_id):
    err = _require_staff()
    if err: return err
    data = request.get_json(silent=True) or {}
    feedback = data.get('feedback', '').strip()
    if not feedback:
        return _json_error('Feedback cannot be empty', 400)
    report = add_staff_feedback(report_id, current_user.id, feedback)
    if report is None:
        return _json_error('Report not found', 404)
    return jsonify({'message': 'Feedback added', 'weekly_report': report.get_json()}), 200


@weekly_report_views.post('/<int:report_id>/approve')
@jwt_required()
def api_approve_report(report_id):
    err = _require_staff()
    if err: return err
    report = approve_weekly_report(report_id, current_user.id)
    if report is None:
        return _json_error('Report not found', 404)
    return jsonify({'message': 'Report approved', 'weekly_report': report.get_json()}), 200


@weekly_report_views.post('/<int:report_id>/revision')
@jwt_required()
def api_request_revision(report_id):
    err = _require_staff()
    if err: return err
    data = request.get_json(silent=True) or {}
    feedback = data.get('feedback', '').strip()
    if not feedback:
        return _json_error('Feedback is required when requesting a revision', 400)
    report = request_revision(report_id, current_user.id, feedback)
    if report is None:
        return _json_error('Report not found', 404)
    return jsonify({'message': 'Revision requested', 'weekly_report': report.get_json()}), 200


@weekly_report_views.post('/submit')
@jwt_required()
def api_student_submit_report():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden — student access only', 403)

    file_obj    = request.files.get('file')
    project_id  = request.form.get('project_id')
    week_number = request.form.get('week_number')

    if not project_id or not week_number:
        return _json_error('project_id and week_number are required', 400)

    rel_path, err = _save_pdf(file_obj, current_user.id, week_number)
    if err:
        return err

    report = create_weekly_report(
        student_id=current_user.id,
        project_id=int(project_id),
        week_number=int(week_number),
        report_file_path=rel_path,
        title=request.form.get('title'),
        description=request.form.get('description'),
        hours_worked=float(request.form['hours_worked']) if request.form.get('hours_worked') else None
    )

    if report is None:
        return _json_error(
            'Could not submit report. Ensure you are hired and have not already submitted this week.',
            400
        )
    return jsonify({'message': 'Weekly report submitted', 'weekly_report': report.get_json()}), 201



@weekly_report_views.get('/my')
@jwt_required()
def api_my_reports():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)
    reports = get_reports_by_student(current_user.id)
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200