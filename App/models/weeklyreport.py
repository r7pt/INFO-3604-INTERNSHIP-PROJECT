from App.database import db
from App.models.user import User
from sqlalchemy import Enum
import enum  
from datetime import datetime


class WeeklyReport(db.Model):
    __tablename__ = 'weekly_report'
    
    id = db.Column(db.Integer, primary_key=True)
    
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, index=True)
    
    week_number = db.Column(db.Integer, nullable=False)  
    report_file_path = db.Column(db.String(512), nullable=False)  
    
    title = db.Column(db.String(256))
    description = db.Column(db.Text)  
    
    hours_worked = db.Column(db.Float)  
    
   
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)  
    is_late = db.Column(db.Boolean, default=False)
    
    
    reviewed = db.Column(db.Boolean, default=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('staff.staff_id'))
    reviewed_at = db.Column(db.DateTime)
    staff_feedback = db.Column(db.Text)
    
    
    status = db.Column(db.String(50), default='submitted') 
    
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    student = db.relationship('Student', back_populates='weekly_reports')
    project = db.relationship('Project', back_populates='weekly_reports')
    reviewer = db.relationship('Staff', foreign_keys=[reviewed_by])
    

    __table_args__ = (
        db.UniqueConstraint('student_id', 'project_id', 'week_number', name='unique_student_project_week'),
        db.Index('idx_weekly_report_status', 'status'),
        db.Index('idx_weekly_report_submission', 'submission_date'),
    )
    
    def __init__(self, student_id, project_id, week_number, report_file_path, 
                 title=None, description=None, hours_worked=None, due_date=None):
        
        if not report_file_path.lower().endswith('.pdf'):
            raise ValueError("Weekly reports must be in PDF format only")
        
        self.student_id = student_id
        self.project_id = project_id
        self.week_number = week_number
        self.report_file_path = report_file_path
        self.title = title
        self.description = description
        self.hours_worked = hours_worked
        self.due_date = due_date
        self.status = 'submitted'
        
        if due_date and datetime.utcnow() > due_date:
            self.is_late = True
    
    def upload_report(self, file_path):
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("Weekly reports must be in PDF format only")
        self.report_file_path = file_path
        self.submission_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if self.due_date and self.submission_date > self.due_date:
            self.is_late = True
    
    def add_staff_feedback(self, staff_id, feedback):
        self.reviewed = True
        self.reviewed_by = staff_id
        self.reviewed_at = datetime.utcnow()
        self.staff_feedback = feedback
        self.status = 'reviewed'
        self.updated_at = datetime.utcnow()
    
    def approve_report(self, staff_id):
        self.reviewed = True
        self.reviewed_by = staff_id
        self.reviewed_at = datetime.utcnow()
        self.status = 'approved'
        self.updated_at = datetime.utcnow()
    
    def request_revision(self, staff_id, feedback):
        self.reviewed = True
        self.reviewed_by = staff_id
        self.reviewed_at = datetime.utcnow()
        self.staff_feedback = feedback
        self.status = 'needs_revision'
        self.updated_at = datetime.utcnow()
    
    def get_json(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'project_id': self.project_id,
            'week_number': self.week_number,
            'report_file_path': self.report_file_path,
            'title': self.title,
            'description': self.description,
            'hours_worked': self.hours_worked,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_late': self.is_late,
            'reviewed': self.reviewed,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'staff_feedback': self.staff_feedback,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<WeeklyReport {self.id}: Student {self.student_id} Week {self.week_number} ({self.status})>"