from App.database import db
from datetime import datetime

class CompanyRegistration(db.Model):
    tablename = 'company_registration'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(256), nullable=False)
    website = db.Column(db.String(256))
    category = db.Column(db.String(256))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    projects = db.relationship('Project', backref='registration', lazy=True)

    def init(self, company_name, website, category):
        self.company_name = company_name
        self.website = website
        self.category = category

    def get_json(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'website': self.website,
            'category': self.category,
            'created_at': self.created_at.isoformat()
        }

    def repr(self):
        return f"<CompanyRegistration {self.id}: {self.company_name}>"