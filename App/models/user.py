from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'
    

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False, unique=True, index=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, index=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    __mapper_args__ = {             
        "polymorphic_identity": "user",
        "polymorphic_on": "role"     
    }
    
    def __init__(self, email, password, role):
        self.email = email
        self.set_password(password)
        self.role = role
    
    def get_json(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    
    def can_shortlist_application(self, application):
        return False
    
    def can_accept_application(self, application):
        return False
    
    def can_reject_application(self, application):
        return False
    
    def can_view_application(self, application):
        return False
    
    def can_create_project(self):
        return False
    
    def can_match_student_to_project(self):
        return False
    
    def __repr__(self):
        return f"<User {self.id}: {self.email}>"
