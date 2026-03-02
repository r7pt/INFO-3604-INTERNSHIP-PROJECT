from App.database import db
from App.models.user import User
from datetime import date

class Student(User):
    __tablename__ = 'student'

    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    phone = db.Column(db.String(20))

    degree = db.Column(db.String(256), nullable=False)
    gpa = db.Column(db.Float)
    year_of_study = db.Column(db.Integer)
    expected_graduation = db.Column(db.Date)

    resume_path = db.Column(db.String(512))
    transcript_path = db.Column(db.String(512))
    profile_pic_path = db.Column(db.String(512))

    transcript_summary = db.Column(db.Text)

    current_internship_status = db.Column(db.String(50), default='not_applied')

    shortlists = db.relationship('Shortlist', back_populates='student', lazy=True)
    weekly_reports = db.relationship('WeeklyReport', back_populates='student', lazy=True)
    meetings = db.relationship('Meeting', back_populates='student', lazy=True)
    evaluations = db.relationship('StudentEvaluation', back_populates='student', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }

    def __init__(self, email, password, first_name, last_name, student_id, degree, role='student'):
        if not self._is_valid_uwi_email(email):
            raise ValueError('Only UWI student emails are allowed to apply for internship')

        super().__init__(email, password, role)
        self.first_name = first_name
        self.last_name = last_name
        self.student_id = student_id
        self.degree = degree

    @staticmethod
    def _is_valid_uwi_email(email):
        valid_domains = ['@my.uwi.edu', '@sta.uwi.edu']
        return any(email.lower().endswith(domain) for domain in valid_domains)

    def calculate_age(self):
        if not self.dob:
            return None
        today = date.today()
        return today.year - self.dob.year - (
            (today.month, today.day) < (self.dob.month, self.dob.day)
        )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def upload_resume(self, file_path):
        if not file_path.lower().endswith('.pdf'):
            raise ValueError('Only PDF files are allowed for resumes')
        self.resume_path = file_path

    def upload_transcript(self, file_path):
        if not file_path.lower().endswith('.pdf'):
            raise ValueError('Only PDF files are allowed for transcripts')
        self.transcript_path = file_path

    def upload_weekly_report(self, file_path, week_number):
        if self.current_internship_status not in ['active']:
            raise ValueError('Can only upload weekly reports after being hired')
        if not file_path.lower().endswith('.pdf'):
            raise ValueError('Only PDF files are allowed for weekly reports')

    def can_apply_to_project(self, project):
        if not self.resume_path or not self.transcript_path:
            return False
        if self.current_internship_status == 'hired':
            return False
        return True

    def can_shortlist_application(self, application):
        return False

    def can_accept_application(self, application):
        return False

    def can_reject_application(self, application):
        return False

    def can_view_application(self, application):
        return getattr(application, 'student_id', None) == self.id

    def can_create_project(self):
        return False

    def can_match_student_to_project(self):
        return False

    def get_json(self):
        base_json = super().get_json()
        student_json = {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'student_id': self.student_id,
            'degree': self.degree,
            'phone': self.phone,
            'gender': self.gender,
            'gpa': self.gpa,
            'year_of_study': self.year_of_study,
            'expected_graduation': self.expected_graduation.isoformat() if self.expected_graduation else None,
            'age': self.calculate_age(),
            'current_internship_status': self.current_internship_status,
            'has_resume': bool(self.resume_path),
            'has_transcript': bool(self.transcript_path),
            'has_transcript_summary': bool(self.transcript_summary),
            'profile_pic_path': self.profile_pic_path,
            'can_apply': bool(self.resume_path and self.transcript_path)
        }
        return {**base_json, **student_json}

    def __repr__(self):
        return f"<Student {self.id}: {self.full_name} ({self.student_id})>"