from App.database import db
from datetime import datetime


class CompanyRegistration(db.Model):
    __tablename__ = "company_registration"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), nullable=False, unique=True, index=True)
    website = db.Column(db.String(256))
    category = db.Column(db.String(256))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    projects = db.relationship("Project", backref="registration", lazy=True)

    def __init__(self, company_name, email, website=None, category=None):
        self.company_name = company_name
        self.email = email
        self.website = website
        self.category = category

    def get_json(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "email": self.email,
            "website": self.website,
            "category": self.category,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<CompanyRegistration {self.id}: {self.company_name}>"