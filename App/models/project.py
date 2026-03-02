from App.database import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(256), nullable=False)

    international_students = db.Column(db.Boolean, default=False)
    place_of_work = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    stipend = db.Column(db.Float)
    hired_after = db.Column(db.Boolean, default=False)
    number_of_interns = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text)
    covid_vaccination = db.Column(db.Boolean, default=False)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    registration_id = db.Column(db.Integer, db.ForeignKey('company_registration.id'))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    shortlists = db.relationship('Shortlist', back_populates='project', lazy=True)
    weekly_reports = db.relationship('WeeklyReport', back_populates='project', lazy=True)
    meetings = db.relationship('Meeting', back_populates='project', lazy=True)
    student_evaluations = db.relationship('StudentEvaluation', back_populates='project', lazy=True)

    def __init__(
        self,
        project_name,
        international_students,
        place_of_work,
        description,
        stipend,
        hired_after,
        number_of_interns,
        details,
        covid_vaccination,
        company_id,
        registration_id=None
    ):
        self.project_name = project_name
        self.international_students = international_students
        self.place_of_work = place_of_work
        self.description = description
        self.stipend = stipend
        self.hired_after = hired_after
        self.number_of_interns = number_of_interns
        self.details = details
        self.covid_vaccination = covid_vaccination
        self.company_id = company_id
        self.registration_id = registration_id

    def get_json(self):
        return {
            'id': self.id,
            'project_name': self.project_name,
            'international_students': self.international_students,
            'place_of_work': self.place_of_work,
            'stipend': self.stipend,
            'hired_after': self.hired_after,
            'number_of_interns': self.number_of_interns,
            'covid_vaccination': self.covid_vaccination
        }

    def __repr__(self):
        return f"<Project {self.id}: {self.project_name}>"