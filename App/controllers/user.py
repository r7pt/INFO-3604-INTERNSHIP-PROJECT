from App.models import User
from App.database import db

def create_user(email, password, role="user"):
    
    new_user = User(email=email, password=password, role=role)
    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except Exception:
        db.session.rollback()
        return None

def get_user(id):
    
    return User.query.get(id)

def get_all_users():
    
    return User.query.all()

def get_all_users_json():
    
    users = User.query.all()
    if not users:
        return []
    return [user.get_json() for user in users]

def get_user_by_email(email):
    
    return User.query.filter_by(email=email).first()

def update_user(id, email=None, is_active=None):
    
    user = get_user(id)
    if user:
        if email:
            user.email = email
        if is_active is not None:
            user.is_active = is_active
        db.session.commit()
        return user
    return None

def delete_user(id):
    
    user = get_user(id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False
