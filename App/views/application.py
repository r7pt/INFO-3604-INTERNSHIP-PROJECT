from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
 
from App.database import db
from App.models.shortlist import Shortlist
from App.models.project import Project
from App.controllers.student import (
    get_student, get_student_application_status,
    get_student_shortlists, get_student_shortlists_json,
    get_all_students, search_students, filter_students,
    get_students_by_status, update_student_internship_status
)
 
application_views = Blueprint('application_views', __name__, url_prefix='/api/applications')
 
 
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
 
 
 
@application_views.get('/my-status')
@jwt_required()
def api_my_application_status():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)
    status = get_student_application_status(current_user.id)
    if status is None:
        return _json_error('Student not found', 404)
    return jsonify({'status': status}), 200
 
 
 
@application_views.get('/my-shortlists')
@jwt_required()
def api_my_shortlists():
    if current_user is None:
        return _json_error('Not authenticated', 401)
    if getattr(current_user, 'role', None) != 'student':
        return _json_error('Forbidden', 403)
    shortlists = get_student_shortlists(current_user.id)
    return jsonify({'shortlists': [s.get_json() for s in shortlists]}), 200
 
 
 
@application_views.get('/students')
@jwt_required()
def api_list_students():
    err = _require_staff()
    if err: return err
    students = get_all_students()
    return jsonify({'students': [s.get_json() for s in students]}), 200
 

 
@application_views.get('/students/<int:student_id>')
@jwt_required()
def api_get_student_application(student_id):
    err = _require_staff()
    if err: return err
    student = get_student(student_id)
    if student is None:
        return _json_error('Student not found', 404)
    return jsonify({
        'student': student.get_json(),
        'application_status': get_student_application_status(student_id),
        'shortlists': get_student_shortlists_json(student_id)
    }), 200
 
 
 
@application_views.get('/students/search')
@jwt_required()
def api_search_students():
    err = _require_staff()
    if err: return err
    query = request.args.get('q', '').strip()
    if not query:
        return _json_error('Search query q is required', 400)
    students = search_students(query)
    return jsonify({'students': [s.get_json() for s in students]}), 200
 
 
 
@application_views.get('/students/filter')
@jwt_required()
def api_filter_students():
    err = _require_staff()
    if err: return err
    args = request.args
    students = filter_students(
        degree=args.get('degree'),
        year_of_study=int(args['year_of_study']) if args.get('year_of_study') else None,
        status=args.get('status'),
        min_gpa=float(args['min_gpa']) if args.get('min_gpa') else None,
        max_gpa=float(args['max_gpa']) if args.get('max_gpa') else None
    )
    return jsonify({'students': [s.get_json() for s in students]}), 200
 
 
 
@application_views.get('/students/by-status/<string:status>')
@jwt_required()
def api_students_by_status(status):
    err = _require_staff()
    if err: return err
    valid = ['not_applied','applied','shortlisted','interviewed','hired','active','completed']
    if status not in valid:
        return _json_error(f'Invalid status. Must be one of: {valid}', 400)
    students = get_students_by_status(status)
    return jsonify({'students': [s.get_json() for s in students], 'status': status}), 200
 
 
 
@application_views.post('/shortlist')
@jwt_required()
def api_shortlist_student():
    err = _require_staff()
    if err: return err
 
    data = request.get_json(silent=True) or {}
    missing = [k for k in ['student_id','project_id'] if not data.get(k)]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})
 
    student_id = int(data['student_id'])
    project_id = int(data['project_id'])
 
    student = get_student(student_id)
    if student is None:
        return _json_error('Student not found', 404)
 
    project = db.session.get(Project, project_id)
    if project is None:
        return _json_error('Project not found', 404)
 
    if Shortlist.query.filter_by(student_id=student_id, project_id=project_id).first():
        return _json_error('Student already shortlisted for this project', 409)
 
    try:
        shortlist = Shortlist(
            staff_id=current_user.id,
            student_id=student_id,
            project_id=project_id,
            match_reason=data.get('match_reason'),
            match_score=float(data['match_score']) if data.get('match_score') else None
        )
        db.session.add(shortlist)
        student.current_internship_status = 'shortlisted'
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to shortlist student', 500)
 
    return jsonify({'message': 'Student shortlisted', 'shortlist': shortlist.get_json()}), 201
 
 
 
@application_views.put('/students/<int:student_id>/status')
@jwt_required()
def api_update_student_status(student_id):
    err = _require_staff()
    if err: return err
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if not new_status:
        return _json_error('status is required', 400)
    student = update_student_internship_status(student_id, new_status)
    if student is None:
        return _json_error('Student not found or invalid status', 400)
    return jsonify({'message': 'Status updated', 'student': student.get_json()}), 200
 
 
 
@application_views.get('/shortlists')
@jwt_required()
def api_all_shortlists():
    err = _require_staff()
    if err: return err
    shortlists = Shortlist.query.order_by(Shortlist.created_at.desc()).all()
    return jsonify({'shortlists': [s.get_json() for s in shortlists]}), 200
 
 
 
@application_views.get('/shortlists/project/<int:project_id>')
@jwt_required()
def api_shortlists_by_project(project_id):
    err = _require_staff()
    if err: return err
    shortlists = Shortlist.query.filter_by(project_id=project_id).all()
    return jsonify({'shortlists': [s.get_json() for s in shortlists]}), 200
 

 
@application_views.post('/shortlists/<int:shortlist_id>/note')
@jwt_required()
def api_add_shortlist_note(shortlist_id):
    err = _require_staff()
    if err: return err
    shortlist = db.session.get(Shortlist, shortlist_id)
    if shortlist is None:
        return _json_error('Shortlist entry not found', 404)
    data = request.get_json(silent=True) or {}
    note = data.get('note', '').strip()
    if not note:
        return _json_error('Note cannot be empty', 400)
    try:
        shortlist.add_staff_note(note, current_user.id)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to add note', 500)
    return jsonify({'message': 'Note added', 'shortlist': shortlist.get_json()}), 200