from App.database import db
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash


class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(256), nullable=False)
    website = db.Column(db.String(256))
    category = db.Column(db.String(256))
    email = db.Column(db.String(256), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False, default='')

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = db.relationship('Project', backref='company', lazy=True)
    student_evaluations = db.relationship('StudentEvaluation', back_populates='company', lazy=True)

    def __init__(self, company_name, website=None, category=None, email=None, password=None):
        self.company_name = company_name
        self.website = website
        self.category = category
        self.email = email
        if password:
            self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_json(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'website': self.website,
            'category': self.category,
            'email': self.email
        }

    def __repr__(self):
        return f"<Company {self.id}: {self.company_name}>"