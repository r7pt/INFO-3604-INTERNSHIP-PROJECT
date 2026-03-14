from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from App.database import db
from App.models.shortlist import Shortlist
from App.models.staff import Staff
from App.models.student import Student
from App.models.project import Project

shortlist_views = Blueprint('shortlist_views', __name__, url_prefix='/api/shortlist')


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _require_staff():
    if current_user is None:
        return None, _json_error('Not authenticated', 401)

    if getattr(current_user, 'role', None) != 'staff':
        return None, _json_error('Forbidden - staff access only', 403)

    staff = db.session.get(Staff, current_user.id)
    if staff is None:
        staff = Staff.query.filter_by(email=getattr(current_user, 'email', None)).first()

    if staff is None:
        return None, _json_error('Staff profile not found', 404)

    return staff, None


def _parse_datetime(value, field_name='datetime'):
    if value in [None, '']:
        return None, None

    try:
        return datetime.fromisoformat(value), None
    except ValueError:
        return None, _json_error(
            f'Invalid {field_name} format. Use ISO 8601, e.g. 2026-03-14T10:00:00',
            400
        )


def _shortlist_json(shortlist):
    payload = shortlist.get_json() if hasattr(shortlist, 'get_json') else {
        'id': shortlist.id,
        'staff_id': getattr(shortlist, 'staff_id', None),
        'student_id': getattr(shortlist, 'student_id', None),
        'project_id': getattr(shortlist, 'project_id', None),
        'status': getattr(shortlist, 'status', None),
    }

    if getattr(shortlist, 'student', None):
        payload['student'] = shortlist.student.get_json() if hasattr(shortlist.student, 'get_json') else {
            'id': shortlist.student.id,
            'email': getattr(shortlist.student, 'email', None),
            'name': getattr(shortlist.student, 'name', None)
        }

    if getattr(shortlist, 'project', None):
        payload['project'] = shortlist.project.get_json() if hasattr(shortlist.project, 'get_json') else {
            'id': shortlist.project.id,
            'project_name': getattr(shortlist.project, 'project_name', None)
        }

    if getattr(shortlist, 'staff', None):
        payload['staff'] = shortlist.staff.get_json() if hasattr(shortlist.staff, 'get_json') else {
            'id': shortlist.staff.id,
            'email': getattr(shortlist.staff, 'email', None),
            'name': getattr(shortlist.staff, 'name', None)
        }

    return payload


@shortlist_views.get('/')
@jwt_required()
def api_get_shortlists():
    staff, err = _require_staff()
    if err:
        return err

    student_id = request.args.get('student_id')
    project_id = request.args.get('project_id')
    status = request.args.get('status')

    query = Shortlist.query.filter_by(staff_id=staff.id)

    if student_id:
        try:
            query = query.filter_by(student_id=int(student_id))
        except ValueError:
            return _json_error('student_id must be an integer', 400)

    if project_id:
        try:
            query = query.filter_by(project_id=int(project_id))
        except ValueError:
            return _json_error('project_id must be an integer', 400)

    if status:
        query = query.filter_by(status=status)

    shortlists = query.order_by(Shortlist.id.desc()).all()

    return jsonify({
        'shortlists': [_shortlist_json(shortlist) for shortlist in shortlists]
    }), 200


@shortlist_views.get('/<int:shortlist_id>')
@jwt_required()
def api_get_shortlist(shortlist_id):
    staff, err = _require_staff()
    if err:
        return err

    shortlist = Shortlist.query.filter_by(id=shortlist_id, staff_id=staff.id).first()
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    return jsonify({
        'shortlist': _shortlist_json(shortlist)
    }), 200


@shortlist_views.post('/')
@jwt_required()
def api_create_shortlist():
    staff, err = _require_staff()
    if err:
        return err

    data = request.get_json(silent=True) or {}

    student_id = data.get('student_id')
    project_id = data.get('project_id')

    if student_id is None or project_id is None:
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

    existing = Shortlist.query.filter_by(student_id=student_id, project_id=project_id).first()
    if existing is not None:
        return _json_error('This student is already matched to this project shortlist', 409)

    try:
        shortlist = Shortlist(
            staff_id=staff.id,
            student_id=student_id,
            project_id=project_id,
            status=data.get('status', 'shortlisted')
        )

        if hasattr(shortlist, 'match_reason'):
            shortlist.match_reason = data.get('match_reason')

        if hasattr(shortlist, 'match_score') and data.get('match_score') not in [None, '']:
            shortlist.match_score = float(data.get('match_score'))

        if hasattr(shortlist, 'staff_notes'):
            shortlist.staff_notes = data.get('staff_notes')

        db.session.add(shortlist)

        if hasattr(student, 'current_internship_status'):
            student.current_internship_status = 'shortlisted'

        db.session.commit()
    except ValueError:
        db.session.rollback()
        return _json_error('match_score must be a number', 400)
    except Exception:
        db.session.rollback()
        return _json_error('Failed to create shortlist entry', 500)

    return jsonify({
        'message': 'Shortlist entry created successfully',
        'shortlist': _shortlist_json(shortlist)
    }), 201


@shortlist_views.patch('/<int:shortlist_id>')
@jwt_required()
def api_update_shortlist(shortlist_id):
    staff, err = _require_staff()
    if err:
        return err

    shortlist = Shortlist.query.filter_by(id=shortlist_id, staff_id=staff.id).first()
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    data = request.get_json(silent=True) or {}

    if 'status' in data and data.get('status'):
        shortlist.status = data.get('status')

    if hasattr(shortlist, 'match_reason') and 'match_reason' in data:
        shortlist.match_reason = data.get('match_reason')

    if hasattr(shortlist, 'match_score') and 'match_score' in data:
        try:
            shortlist.match_score = None if data.get('match_score') in [None, ''] else float(data.get('match_score'))
        except ValueError:
            return _json_error('match_score must be a number', 400)

    if hasattr(shortlist, 'staff_notes') and 'staff_notes' in data:
        shortlist.staff_notes = data.get('staff_notes')

    if hasattr(shortlist, 'rejection_reason') and 'rejection_reason' in data:
        shortlist.rejection_reason = data.get('rejection_reason')

    if hasattr(shortlist, 'interview_notes') and 'interview_notes' in data:
        shortlist.interview_notes = data.get('interview_notes')

    if hasattr(shortlist, 'interview_date') and 'interview_date' in data:
        interview_date, date_err = _parse_datetime(data.get('interview_date'), 'interview_date')
        if date_err:
            return date_err
        shortlist.interview_date = interview_date

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to update shortlist entry', 500)

    return jsonify({
        'message': 'Shortlist entry updated successfully',
        'shortlist': _shortlist_json(shortlist)
    }), 200


@shortlist_views.post('/<int:shortlist_id>/interview')
@jwt_required()
def api_schedule_interview(shortlist_id):
    staff, err = _require_staff()
    if err:
        return err

    shortlist = Shortlist.query.filter_by(id=shortlist_id, staff_id=staff.id).first()
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    data = request.get_json(silent=True) or {}
    interview_date, date_err = _parse_datetime(data.get('interview_date'), 'interview_date')
    if date_err:
        return date_err

    if interview_date is None:
        return _json_error('interview_date is required', 400)

    try:
        if hasattr(shortlist, 'schedule_interview'):
            shortlist.schedule_interview(interview_date)
        else:
            if hasattr(shortlist, 'interview_scheduled'):
                shortlist.interview_scheduled = True
            if hasattr(shortlist, 'interview_date'):
                shortlist.interview_date = interview_date
            shortlist.status = 'interview_scheduled'

        if hasattr(shortlist, 'staff_notes') and data.get('staff_notes') is not None:
            shortlist.staff_notes = data.get('staff_notes')

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to schedule interview', 500)

    return jsonify({
        'message': 'Interview scheduled successfully',
        'shortlist': _shortlist_json(shortlist)
    }), 200


@shortlist_views.post('/<int:shortlist_id>/interviewed')
@jwt_required()
def api_mark_interviewed(shortlist_id):
    staff, err = _require_staff()
    if err:
        return err

    shortlist = Shortlist.query.filter_by(id=shortlist_id, staff_id=staff.id).first()
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    data = request.get_json(silent=True) or {}

    try:
        if hasattr(shortlist, 'mark_as_interviewed'):
            shortlist.mark_as_interviewed(data.get('interview_notes'))
        else:
            if hasattr(shortlist, 'interviewed'):
                shortlist.interviewed = True
            if hasattr(shortlist, 'interview_notes'):
                shortlist.interview_notes = data.get('interview_notes')
            shortlist.status = 'interviewed'

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to mark interview as completed', 500)

    return jsonify({
        'message': 'Student marked as interviewed',
        'shortlist': _shortlist_json(shortlist)
    }), 200


@shortlist_views.post('/<int:shortlist_id>/hire')
@jwt_required()
def api_mark_hired(shortlist_id):
    staff, err = _require_staff()
    if err:
        return err

    shortlist = Shortlist.query.filter_by(id=shortlist_id, staff_id=staff.id).first()
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    try:
        if hasattr(shortlist, 'mark_as_hired'):
            shortlist.mark_as_hired()
        else:
            if hasattr(shortlist, 'hired'):
                shortlist.hired = True
            shortlist.status = 'hired'

        student = db.session.get(Student, shortlist.student_id)
        if student is not None and hasattr(student, 'current_internship_status'):
            student.current_internship_status = 'hired'

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to mark student as hired', 500)

    return jsonify({
        'message': 'Student marked as hired',
        'shortlist': _shortlist_json(shortlist)
    }), 200


@shortlist_views.post('/<int:shortlist_id>/reject')
@jwt_required()
def api_mark_rejected(shortlist_id):
    staff, err = _require_staff()
    if err:
        return err

    shortlist = Shortlist.query.filter_by(id=shortlist_id, staff_id=staff.id).first()
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    data = request.get_json(silent=True) or {}
    reason = data.get('rejection_reason')

    try:
        if hasattr(shortlist, 'mark_as_rejected'):
            shortlist.mark_as_rejected(reason)
        else:
            if hasattr(shortlist, 'rejection_reason'):
                shortlist.rejection_reason = reason
            shortlist.status = 'rejected'

        student = db.session.get(Student, shortlist.student_id)
        if student is not None and hasattr(student, 'current_internship_status'):
            student.current_internship_status = 'rejected'

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to reject student', 500)

    return jsonify({
        'message': 'Student rejected',
        'shortlist': _shortlist_json(shortlist)
    }), 200


@shortlist_views.delete('/<int:shortlist_id>')
@jwt_required()
def api_delete_shortlist(shortlist_id):
    staff, err = _require_staff()
    if err:
        return err

    shortlist = Shortlist.query.filter_by(id=shortlist_id, staff_id=staff.id).first()
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)

    try:
        db.session.delete(shortlist)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to delete shortlist entry', 500)

    return jsonify({
        'message': 'Shortlist entry deleted successfully'
    }), 200