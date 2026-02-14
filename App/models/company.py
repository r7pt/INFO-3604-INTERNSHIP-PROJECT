from App.database import db
from datetime import datetime

class Company(db.Model):
    tablename = 'company'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(256), nullable=False)
    website = db.Column(db.String(256))
    category = db.Column(db.String(256))
    email = db.Column(db.String(256), nullable=False, unique=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = db.relationship('Project', backref='company', lazy=True)

    def init(self, company_name, website, category, email):
        self.company_name = company_name
        self.website = website
        self.category = category
        self.email = email

    def get_json(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'website': self.website,
            'category': self.category,
            'email': self.email
        }

    def repr(self):
        return f"<Company {self.id}: {self.company_name}>"