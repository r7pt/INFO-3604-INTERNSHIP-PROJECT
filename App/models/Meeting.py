from App.database import db
from datetime import datetime


class Meeting(db.Model):
    __tablename__ = 'meeting'

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), index=True)

    meeting_type = db.Column(db.String(50), nullable=False, default='weekly', index=True)
    scheduled_at = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(256))
    meeting_link = db.Column(db.String(512))
    agenda = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default='scheduled', index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    program = db.relationship('Program', back_populates='meetings')
    student = db.relationship('Student', back_populates='meetings')
    staff = db.relationship('Staff', back_populates='meetings')
    project = db.relationship('Project', back_populates='meetings')

    __table_args__ = (
        db.Index('idx_meeting_status', 'status'),
        db.Index('idx_meeting_type_time', 'meeting_type', 'scheduled_at'),
    )

    def __init__(
        self,
        student_id,
        staff_id,
        scheduled_at,
        meeting_type='weekly',
        program_id=None,
        project_id=None,
        location=None,
        meeting_link=None,
        agenda=None,
        notes=None,
        status='scheduled'
    ):
        self.student_id = student_id
        self.staff_id = staff_id
        self.scheduled_at = scheduled_at
        self.meeting_type = meeting_type
        self.program_id = program_id
        self.project_id = project_id
        self.location = location
        self.meeting_link = meeting_link
        self.agenda = agenda
        self.notes = notes
        self.status = status

    def add_notes(self, notes):
        timestamp = datetime.utcnow().isoformat()
        new_note = f"[{timestamp}] {notes}\n"
        if self.notes:
            self.notes += new_note
        else:
            self.notes = new_note
        self.updated_at = datetime.utcnow()

    def mark_completed(self):
        self.status = 'completed'
        self.updated_at = datetime.utcnow()

    def cancel(self, reason=None):
        self.status = 'cancelled'
        if reason:
            self.add_notes(f"Cancelled: {reason}")
        self.updated_at = datetime.utcnow()

    def get_json(self):
        return {
            'id': self.id,
            'program_id': self.program_id,
            'student_id': self.student_id,
            'staff_id': self.staff_id,
            'project_id': self.project_id,
            'meeting_type': self.meeting_type,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'location': self.location,
            'meeting_link': self.meeting_link,
            'agenda': self.agenda,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Meeting {self.id}: {self.meeting_type} with Student {self.student_id}>"