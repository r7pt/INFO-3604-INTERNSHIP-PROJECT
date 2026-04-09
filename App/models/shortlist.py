from App.database import db
from App.models.user import User
from sqlalchemy import Enum
import enum  
from datetime import datetime


class Shortlist(db.Model):
    __tablename__ = 'shortlist'
    
    
    id = db.Column(db.Integer, primary_key=True)
    
   
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, index=True)
    
    
    status = db.Column(db.String(50), nullable=False, default='shortlisted')
    
    interview_scheduled = db.Column(db.Boolean, default=False)
    interview_date = db.Column(db.DateTime)
    interviewed = db.Column(db.Boolean, default=False)
    interview_notes = db.Column(db.Text)
    
    
    hired = db.Column(db.Boolean, default=False)
    hiring_decision_date = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)  
    
    
    staff_notes = db.Column(db.Text)
    
    
    match_reason = db.Column(db.Text)
    match_score = db.Column(db.Float)  
    
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    shortlisted_by = db.Column(db.Integer, db.ForeignKey('staff.staff_id'))  
   
    student_notified = db.Column(db.Boolean, default=False)
    student_notification_sent_at = db.Column(db.DateTime)
    company_notified = db.Column(db.Boolean, default=False)
    company_notification_sent_at = db.Column(db.DateTime)
    

    staff = db.relationship('Staff', foreign_keys=[staff_id], back_populates='shortlists')
    student = db.relationship('Student', back_populates='shortlists')
    project = db.relationship('Project', back_populates='shortlists')
    shortlisted_by_staff = db.relationship('Staff', foreign_keys=[shortlisted_by])
    

    __table_args__ = (
        db.UniqueConstraint('student_id', 'project_id', name='unique_student_project_shortlist'),
        db.Index('idx_shortlist_status', 'status'),
    )
    
    def __init__(self, staff_id, student_id, project_id, match_reason=None, match_score=None):
        self.staff_id = staff_id
        self.student_id = student_id
        self.project_id = project_id
        self.match_reason = match_reason
        self.match_score = match_score
        self.shortlisted_by = staff_id
        self.status = 'shortlisted'  
    
    def mark_as_interviewed(self, interview_notes=None):
        self.interviewed = True
        self.interview_scheduled = True
        self.status = 'interviewed'
        if interview_notes:
            self.interview_notes = interview_notes
        self.updated_at = datetime.utcnow()
    
    def mark_as_hired(self):
        self.hired = True
        self.hiring_decision_date = datetime.utcnow()
        self.status = 'hired'
        self.updated_at = datetime.utcnow()
    
    def mark_as_rejected(self, reason=None):
        self.hired = False
        self.hiring_decision_date = datetime.utcnow()
        self.status = 'rejected'
        if reason:
            self.rejection_reason = reason
        self.updated_at = datetime.utcnow()
    
    def schedule_interview(self, interview_date):
        self.interview_scheduled = True
        self.interview_date = interview_date
        self.status = 'interview_scheduled'
        self.updated_at = datetime.utcnow()
    
    def add_staff_note(self, note, staff_id):
        timestamp = datetime.utcnow().isoformat()
        new_note = f"[{timestamp}] Staff {staff_id}: {note}\n"
        if self.staff_notes:
            self.staff_notes += new_note
        else:
            self.staff_notes = new_note
        self.updated_at = datetime.utcnow()
    
    def notify_student(self):
        self.student_notified = True
        self.student_notification_sent_at = datetime.utcnow()
    
    def notify_company(self):
        self.company_notified = True
        self.company_notification_sent_at = datetime.utcnow()
    
    def get_json(self):
        return {
            'id': self.id,
            'staff_id': self.staff_id,
            'student_id': self.student_id,
            'project_id': self.project_id,
            'status': self.status,
            'interview_scheduled': self.interview_scheduled,
            'interview_date': self.interview_date.isoformat() if self.interview_date else None,
            'interviewed': self.interviewed,
            'interview_notes': self.interview_notes,
            'hired': self.hired,
            'hiring_decision_date': self.hiring_decision_date.isoformat() if self.hiring_decision_date else None,
            'rejection_reason': self.rejection_reason,
            'staff_notes': self.staff_notes,
            'match_reason': self.match_reason,
            'match_score': self.match_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'shortlisted_by': self.shortlisted_by,
            'student_notified': self.student_notified,
            'student_notification_sent_at': self.student_notification_sent_at.isoformat() if self.student_notification_sent_at else None,
            'company_notified': self.company_notified,
            'company_notification_sent_at': self.company_notification_sent_at.isoformat() if self.company_notification_sent_at else None
        }
    
    def __repr__(self):
        return f"<Shortlist {self.id}: Student {self.student_id} → Project {self.project_id} ({self.status})>"