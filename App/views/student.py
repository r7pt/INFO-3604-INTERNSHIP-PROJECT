from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, current_user
from datetime import datetime

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
from App.models.shortlist import Shortlist
from App.models.Meeting import Meeting
from App.models.student_application import Student_application
from App.controllers.weeklyreport import create_weekly_report

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
    try:
        from App.controllers.transcript_parser import parse_and_save_transcript
        parse_and_save_transcript(student.id, rel_path)
    except Exception as e:
        print(f"Summary parsing failed: {e}")

    return jsonify({'message': 'Transcript uploaded and summary generated'}), 200

'''
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

    
    existing = Student_application.query.filter_by(
        student_id=current_user.id, 
        project_id=project.id
    ).first()
    
    if existing:
        return _json_error('You have already applied for this project', 400)

    new_app = Student_application(
        student_id=current_user.id,
        project_id=project.id,
        status='pending'
    )
    db.session.add(new_app)

    current_user.current_internship_status = 'applied'
    
    db.session.commit()

    return jsonify({
        'message': 'Application submitted',
        'project_id': project.id,
        'status': current_user.current_internship_status
    }), 200
'''
@student_views.post('/apply')
@jwt_required()
def api_apply():
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    if not current_user.resume_path or not current_user.transcript_path:
        return _json_error('Please upload your Resume and Transcript before applying.', 400)

    current_user.current_internship_status = 'applied'
    db.session.commit()

    return jsonify({
        'message': 'Application submitted successfully! Staff will review your profile.',
        'status': 'applied'
    }), 200

@student_views.get('/weekly-reports')
@jwt_required()
def api_weekly_reports_list():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    reports = WeeklyReport.query.filter_by(
        student_id=current_user.id
    ).order_by(WeeklyReport.week_number.asc()).all()
    return jsonify({'weekly_reports': [r.get_json() for r in reports]}), 200


@student_views.post('/weekly-reports')
@jwt_required()
def api_weekly_reports_create():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    file_obj    = request.files.get('file')
    project_id  = request.form.get('project_id')
    week_number = request.form.get('week_number')

    if not project_id or not week_number:
        data = request.get_json(silent=True) or {}
        project_id  = project_id  or data.get('project_id')
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
            week_number=int(week_number)
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
    else:
        hours_worked = None

    report = create_weekly_report(
        student_id=current_user.id,
        project_id=project.id,
        week_number=int(week_number),
        report_file_path=rel_path,
        title=title,
        description=description,
        hours_worked=hours_worked
    )

    if report is None:
        return _json_error(
            'Could not submit report. Ensure you are hired for this project and have not already submitted this week.',
            400
        )

    return jsonify({'message': 'Weekly report uploaded', 'weekly_report': report.get_json()}), 201


@student_views.get('/dashboard')
@jwt_required()
def student_dashboard():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    try:
        now = datetime.utcnow()

        # Application status
        status = get_student_application_status(current_user.id)
        application_submitted = status is not None and status.get('current_internship_status') != 'not_applied'

        # Shortlists
        shortlists = Shortlist.query.filter_by(student_id=current_user.id).all()
        accepted_projects   = [s for s in shortlists if s.status == 'accepted']
        upcoming_interviews = [
            s for s in shortlists
            if s.interview_date is not None and s.interview_date >= now
        ]

        # Weekly reports
        weekly_reports = WeeklyReport.query.filter_by(
            student_id=current_user.id
        ).order_by(WeeklyReport.due_date.asc()).all()
        upcoming_weekly_reports = [
            r for r in weekly_reports
            if r.due_date is not None and r.due_date >= now
        ]

        # Upcoming meetings
        upcoming_meetings = Meeting.query.filter(
            Meeting.student_id == current_user.id,
            Meeting.scheduled_at >= now
        ).order_by(Meeting.meeting_date.asc()).all()

        # Build combined deadlines list
        important_deadlines = []
        important_deadlines.extend([s.get_json() for s in upcoming_interviews])
        important_deadlines.extend([m.get_json() for m in upcoming_meetings])
        important_deadlines.extend([r.get_json() for r in upcoming_weekly_reports])

        return jsonify({
            'application_submitted':    application_submitted,
            'num_upcoming_interviews':  len(upcoming_interviews),
            'num_accepted_projects':    len(accepted_projects),
            'important_deadlines':      important_deadlines,
        }), 200

    except Exception as e:
        print(f"Error getting dashboard: {e}")
        return _json_error('Failed to get dashboard', 500)