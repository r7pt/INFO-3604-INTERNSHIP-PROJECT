from datetime import datetime

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, current_user

from App.database import db
from App.models.student import Student
from App.models.Meeting import Meeting

student_scheduling_views = Blueprint(
    'student_scheduling_views',
    __name__,
    url_prefix='/api/student-scheduling'
)


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _require_student():
    if current_user is None:
        return None, _json_error('Not authenticated', 401)

    if getattr(current_user, 'role', None) != 'student':
        return None, _json_error('Forbidden – student access only', 403)

    student = db.session.get(Student, current_user.id)
    if student is None:
        return None, _json_error('Student profile not found', 404)

    return student, None


def _meeting_json(meeting):
    payload = meeting.get_json()

    if getattr(meeting, 'project', None):
        payload['project'] = {
            'id': meeting.project.id,
            'project_name': getattr(meeting.project, 'project_name', None)
        }

    if getattr(meeting, 'staff', None):
        payload['staff'] = {
            'id': meeting.staff.id,
            'name': getattr(meeting.staff, 'name', None),
            'email': getattr(meeting.staff, 'email', None)
        }

    return payload


@student_scheduling_views.get('/')
@jwt_required()
def api_student_schedule():
    student, err = _require_student()
    if err:
        return err

    meetings = (
        Meeting.query
        .filter_by(student_id=student.id)
        .order_by(Meeting.scheduled_at.asc())
        .all()
    )

    return jsonify({
        'schedule': [_meeting_json(meeting) for meeting in meetings]
    }), 200


@student_scheduling_views.get('/upcoming')
@jwt_required()
def api_student_upcoming_schedule():
    student, err = _require_student()
    if err:
        return err

    now = datetime.utcnow()

    meetings = (
        Meeting.query
        .filter(
            Meeting.student_id == student.id,
            Meeting.scheduled_at >= now,
            Meeting.status == 'scheduled'
        )
        .order_by(Meeting.scheduled_at.asc())
        .all()
    )

    return jsonify({
        'upcoming_schedule': [_meeting_json(meeting) for meeting in meetings]
    }), 200


@student_scheduling_views.get('/<int:meeting_id>')
@jwt_required()
def api_student_schedule_detail(meeting_id):
    student, err = _require_student()
    if err:
        return err

    meeting = db.session.get(Meeting, meeting_id)
    if meeting is None or meeting.student_id != student.id:
        return _json_error('Meeting not found', 404)

    return jsonify({
        'meeting': _meeting_json(meeting)
    }), 200