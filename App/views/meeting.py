from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from App.database import db
from App.models.Meeting import Meeting

meeting_views = Blueprint('meeting_views', __name__, url_prefix='/api/meetings')


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _require_staff():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'staff':
        return _json_error('Forbidden – staff access only', 403)
    return None



@meeting_views.post('/')
@jwt_required()
def api_create_meeting():
    err = _require_staff()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    required = ['student_id', 'scheduled_at']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})

    try:
        scheduled_at = datetime.fromisoformat(data['scheduled_at'])
    except ValueError:
        return _json_error('Invalid scheduled_at format. Use ISO 8601 (e.g. 2025-06-15T10:00:00)', 400)

    try:
        meeting = Meeting(
            student_id=int(data['student_id']),
            staff_id=current_user.id,
            scheduled_at=scheduled_at,
            meeting_type=data.get('meeting_type', 'weekly'),
            project_id=data.get('project_id'),
            location=data.get('location'),
            meeting_link=data.get('meeting_link'),
            agenda=data.get('agenda'),
        )
        db.session.add(meeting)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to create meeting', 500)

    return jsonify({'message': 'Meeting scheduled', 'meeting': meeting.get_json()}), 201



@meeting_views.get('/')
@jwt_required()
def api_list_meetings():
    err = _require_staff()
    if err:
        return err

    meetings = (
        Meeting.query
        .filter_by(staff_id=current_user.id)
        .order_by(Meeting.scheduled_at.desc())
        .all()
    )
    return jsonify({'meetings': [m.get_json() for m in meetings]}), 200


@meeting_views.get('/<int:meeting_id>')
@jwt_required()
def api_get_meeting(meeting_id):
    if current_user is None:
        return _json_error('Not authenticated', 401)

    meeting = db.session.get(Meeting, meeting_id)
    if meeting is None:
        return _json_error('Meeting not found', 404)

    
    role = getattr(current_user, 'role', None)
    if role == 'student' and meeting.student_id != current_user.id:
        return _json_error('Forbidden', 403)
    if role == 'staff' and meeting.staff_id != current_user.id:
        return _json_error('Forbidden', 403)

    return jsonify({'meeting': meeting.get_json()}), 200



@meeting_views.post('/<int:meeting_id>/notes')
@jwt_required()
def api_add_meeting_notes(meeting_id):
    err = _require_staff()
    if err:
        return err

    meeting = db.session.get(Meeting, meeting_id)
    if meeting is None or meeting.staff_id != current_user.id:
        return _json_error('Meeting not found', 404)

    data = request.get_json(silent=True) or {}
    notes = data.get('notes', '').strip()
    if not notes:
        return _json_error('Notes cannot be empty', 400)

    try:
        meeting.add_notes(notes)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to save notes', 500)

    return jsonify({'message': 'Notes added', 'meeting': meeting.get_json()}), 200


@meeting_views.post('/<int:meeting_id>/complete')
@jwt_required()
def api_complete_meeting(meeting_id):
    err = _require_staff()
    if err:
        return err

    meeting = db.session.get(Meeting, meeting_id)
    if meeting is None or meeting.staff_id != current_user.id:
        return _json_error('Meeting not found', 404)

    try:
        meeting.mark_completed()
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to complete meeting', 500)

    return jsonify({'message': 'Meeting marked as completed', 'meeting': meeting.get_json()}), 200


@meeting_views.post('/<int:meeting_id>/cancel')
@jwt_required()
def api_cancel_meeting(meeting_id):
    err = _require_staff()
    if err:
        return err

    meeting = db.session.get(Meeting, meeting_id)
    if meeting is None or meeting.staff_id != current_user.id:
        return _json_error('Meeting not found', 404)

    data = request.get_json(silent=True) or {}
    try:
        meeting.cancel(reason=data.get('reason'))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to cancel meeting', 500)

    return jsonify({'message': 'Meeting cancelled', 'meeting': meeting.get_json()}), 200



@meeting_views.get('/my')
@jwt_required()
def api_student_meetings():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)

    meetings = (
        Meeting.query
        .filter_by(student_id=current_user.id)
        .order_by(Meeting.scheduled_at.desc())
        .all()
    )
    return jsonify({'meetings': [m.get_json() for m in meetings]}), 200




























