from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import inspect

from App.database import db
from App.models.announcement import Announcement

announcement_views = Blueprint(
    'announcement_views',
    __name__,
    url_prefix='/api/announcements'
)


def _json_error(message, status=400, extra=None):
    payload = {'error': message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _column_names():
    return {column.key for column in inspect(Announcement).columns}


def _assignable_columns():
    excluded = {'id', 'created_at', 'updated_at'}
    return _column_names() - excluded


def _required_columns():
    required = []
    for column in inspect(Announcement).columns:
        if column.key in ['id', 'created_at', 'updated_at']:
            continue
        if column.nullable:
            continue
        if column.default is not None or column.server_default is not None:
            continue
        if column.autoincrement:
            continue
        required.append(column.key)
    return required


def _serialize(announcement):
    if hasattr(announcement, 'get_json'):
        return announcement.get_json()

    payload = {}
    for key in _column_names():
        payload[key] = getattr(announcement, key, None)
    return payload


def _coerce_value(column_name, value):
    if value is None:
        return None

    column = inspect(Announcement).columns[column_name]

    try:
        python_type = column.type.python_type
    except Exception:
        python_type = None

    if python_type is bool:
        if isinstance(value, bool):
            return value

        text = str(value).strip().lower()
        if text in ['true', '1', 'yes', 'y', 'on']:
            return True
        if text in ['false', '0', 'no', 'n', 'off']:
            return False
        raise ValueError(f'{column_name} must be a boolean')

    if python_type is int:
        try:
            return int(value)
        except Exception:
            raise ValueError(f'{column_name} must be an integer')

    if python_type is float:
        try:
            return float(value)
        except Exception:
            raise ValueError(f'{column_name} must be a number')

    return value


def _request_data():
    return request.get_json(silent=True) or {}


def _apply_defaults(data):
    cols = _column_names()

    if 'user_id' in cols and 'user_id' not in data and current_user is not None:
        data['user_id'] = current_user.id

    if 'author_id' in cols and 'author_id' not in data and current_user is not None:
        data['author_id'] = current_user.id

    if 'staff_id' in cols and 'staff_id' not in data and current_user is not None and getattr(current_user, 'role', None) == 'staff':
        data['staff_id'] = current_user.id

    if 'posted_by' in cols and 'posted_by' not in data and current_user is not None:
        data['posted_by'] = current_user.id

    return data


@announcement_views.get('/')
def api_list_announcements():
    announcements = Announcement.query.order_by(Announcement.id.desc()).all()
    return jsonify({
        'announcements': [_serialize(announcement) for announcement in announcements]
    }), 200


@announcement_views.get('/<int:announcement_id>')
def api_get_announcement(announcement_id):
    announcement = db.session.get(Announcement, announcement_id)
    if announcement is None:
        return _json_error('Announcement not found', 404)

    return jsonify({
        'announcement': _serialize(announcement)
    }), 200


@announcement_views.post('/')
@jwt_required()
def api_create_announcement():
    data = _apply_defaults(_request_data())
    allowed = _assignable_columns()

    missing = [key for key in _required_columns() if data.get(key) in [None, '']]
    if missing:
        return _json_error('Missing required fields', 400, {'missing': missing})

    kwargs = {}

    try:
        for key, value in data.items():
            if key in allowed:
                kwargs[key] = _coerce_value(key, value)

        announcement = Announcement(**kwargs)
        db.session.add(announcement)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return _json_error(str(e), 400)
    except TypeError as e:
        db.session.rollback()
        return _json_error(f'Invalid announcement fields: {str(e)}', 400)
    except Exception:
        db.session.rollback()
        return _json_error('Failed to create announcement', 500)

    return jsonify({
        'message': 'Announcement created successfully',
        'announcement': _serialize(announcement)
    }), 201


@announcement_views.patch('/<int:announcement_id>')
@jwt_required()
def api_update_announcement(announcement_id):
    announcement = db.session.get(Announcement, announcement_id)
    if announcement is None:
        return _json_error('Announcement not found', 404)

    data = _request_data()
    allowed = _assignable_columns()

    try:
        for key, value in data.items():
            if key in allowed:
                setattr(announcement, key, _coerce_value(key, value))

        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return _json_error(str(e), 400)
    except Exception:
        db.session.rollback()
        return _json_error('Failed to update announcement', 500)

    return jsonify({
        'message': 'Announcement updated successfully',
        'announcement': _serialize(announcement)
    }), 200


@announcement_views.delete('/<int:announcement_id>')
@jwt_required()
def api_delete_announcement(announcement_id):
    announcement = db.session.get(Announcement, announcement_id)
    if announcement is None:
        return _json_error('Announcement not found', 404)

    try:
        db.session.delete(announcement)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error('Failed to delete announcement', 500)

    return jsonify({
        'message': 'Announcement deleted successfully'
    }), 200