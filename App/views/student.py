from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, current_user
from App.database import db
from App.controllers.auth import register_student, login
from App.controllers.student import (
    upload_student_resume,
    upload_student_transcript,
    get_student_application_status
)
from App.controllers.document import DocumentController
from App.models.project import Project
from App.models.weeklyreport import WeeklyReport

from App.models.student_application import Student_application
from App.models.shortlist import Shortlist
from App.controllers.shortlist import *
from App.models.Meeting import Meeting
from App.models.weekly_report import WeeklyReport
from App.controllers.weekly_report import *

student_views = Blueprint('student_views', __name__, url_prefix='/api/student')


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


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

    try:
        rel_path = DocumentController.save_student_resume(
            file_storage=file_obj,
            student_id=current_user.id,
            old_relative_path=getattr(current_user, 'resume_path', None)
        )
    except ValueError as e:
        return _json_error(str(e), 400)
    except Exception:
        return _json_error('Failed to save resume file', 500)

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

    try:
        rel_path = DocumentController.save_student_transcript(
            file_storage=file_obj,
            student_id=current_user.id,
            old_relative_path=getattr(current_user, 'transcript_path', None)
        )
    except ValueError as e:
        return _json_error(str(e), 400)
    except Exception:
        return _json_error('Failed to save transcript file', 500)

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

    return jsonify({
        'message': 'Application submitted',
        'project_id': project.id,
        'status': current_user.current_internship_status
    }), 200


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
        return _json_errEor('Not authenticated', 401)
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

    try:
        rel_path = DocumentController.save_weekly_report(
            file_storage=file_obj,
            student_id=current_user.id,
            week_number=week_number
        )
    except ValueError as e:
        return _json_error(str(e), 400)
    except Exception:
        return _json_error('Failed to save weekly report file', 500)

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


@student_views.get('/dashboard')
@jwt_required()
def student_dashboard():
    if current_user is None:
        return _json_errEor('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)
    try:
        student_id= getattr(current_user, 'id', None) 
        application = get_application_by_student_id(current_user.id)
        if application.status :
            application_submitted = 1
        else:
            application_submitted = "not submitted"
        shortlists = get_shortlists_by_student(current_user.id)
        accepted_projects = [for shortlist in shortlists if shortlist.status  = 'accepted']
        num_accepted_projects = len(accepted_projects)
        upcoming_interviews= [for shortlist in shortlists if shortlist.interview_date != None and shortlist.interview_date < datetime.utcnow]
        num_upcoming_interviews = len(interviews)
        num_skills = len(application.skills)
        weekly_reports = get_report_by_student(current_user.id)
        upcoming_weekly_reports=  [for weekly_report in weekly_reports if weekly_report.due_date <= datetime.utcnow]
        upcoming_meetings = Meeting.query.filter_by(student_id = current_user.id and due_date <=datetime.utcnow).order_by(WeeklyReport.due_date.asc()).all()
        important_deadlines.append(upcoming_interviews,upcoming_meetings,upcoming_weekly_reports)
        return jsonify(application_submitted,num_upcoming_interviews,num_accepted_projects,num_skills,important_deadlines),200
    except Exception as e:
        flash("an error occurred")
        print("the foolowing error occured while getting dashboard", e)
        return return _json_error('Failed to get dashboard', 500)
    

    

