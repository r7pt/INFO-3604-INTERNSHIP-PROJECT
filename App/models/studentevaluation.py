from App.database import db
from datetime import datetime


class StudentEvaluation(db.Model):
    __tablename__ = 'student_evaluation'
    
    id = db.Column(db.Integer, primary_key=True)
    
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, index=True)
    
    evaluation_form_path = db.Column(db.String(512), nullable=False)  
    
    evaluation_period = db.Column(db.String(50))  
    evaluation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    overall_rating = db.Column(db.Float)  
    technical_skills_rating = db.Column(db.Float)
    communication_rating = db.Column(db.Float)
    professionalism_rating = db.Column(db.Float)
    teamwork_rating = db.Column(db.Float)
    problem_solving_rating = db.Column(db.Float)
    
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    comments = db.Column(db.Text)
    
    recommend_for_future_employment = db.Column(db.Boolean)
    would_hire_again = db.Column(db.Boolean)
    
    internship_completed = db.Column(db.Boolean, default=True)
    completion_date = db.Column(db.DateTime)
    
    evaluator_name = db.Column(db.String(256))  
    evaluator_title = db.Column(db.String(256))  
    evaluator_email = db.Column(db.String(256))
    
    status = db.Column(db.String(50), default='submitted') 
    
    reviewed_by_staff = db.Column(db.Boolean, default=False)
    staff_reviewer_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    staff_notes = db.Column(db.Text)
    staff_review_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    
    company = db.relationship('Company', back_populates='student_evaluations')
    student = db.relationship('Student', back_populates='evaluations')
    project = db.relationship('Project', back_populates='student_evaluations')
    staff_reviewer = db.relationship('Staff', foreign_keys=[staff_reviewer_id])
    
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'project_id', 'evaluation_period', name='unique_student_project_evaluation'),
        db.Index('idx_evaluation_status', 'status'),
        db.Index('idx_evaluation_date', 'evaluation_date'),
    )
    
    def __init__(self, company_id, student_id, project_id, evaluation_form_path,
                 evaluation_period='final', evaluator_name=None, evaluator_title=None, evaluator_email=None):
        if not evaluation_form_path.lower().endswith('.pdf'):
            raise ValueError("Evaluation forms must be in PDF format only")
        
        self.company_id = company_id
        self.student_id = student_id
        self.project_id = project_id
        self.evaluation_form_path = evaluation_form_path
        self.evaluation_period = evaluation_period
        self.evaluator_name = evaluator_name
        self.evaluator_title = evaluator_title
        self.evaluator_email = evaluator_email
        self.submitted_at = datetime.utcnow()
    
    def upload_evaluation_form(self, file_path):
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("Evaluation forms must be in PDF format only")
        self.evaluation_form_path = file_path
        self.submitted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def set_ratings(self, overall=None, technical=None, communication=None,
                   professionalism=None, teamwork=None, problem_solving=None):
        if overall is not None:
            self.overall_rating = overall
        if technical is not None:
            self.technical_skills_rating = technical
        if communication is not None:
            self.communication_rating = communication
        if professionalism is not None:
            self.professionalism_rating = professionalism
        if teamwork is not None:
            self.teamwork_rating = teamwork
        if problem_solving is not None:
            self.problem_solving_rating = problem_solving
        self.updated_at = datetime.utcnow()
    
    def add_staff_review(self, staff_id, notes):
        self.reviewed_by_staff = True
        self.staff_reviewer_id = staff_id
        self.staff_notes = notes
        self.staff_review_date = datetime.utcnow()
        self.status = 'reviewed_by_staff'
        self.updated_at = datetime.utcnow()
    
    def finalize_evaluation(self):
        self.status = 'finalized'
        self.updated_at = datetime.utcnow()
    
    def mark_internship_completed(self, completion_date=None):
        self.internship_completed = True
        self.completion_date = completion_date or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def calculate_average_rating(self):
        ratings = [
            self.overall_rating,
            self.technical_skills_rating,
            self.communication_rating,
            self.professionalism_rating,
            self.teamwork_rating,
            self.problem_solving_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            return sum(valid_ratings) / len(valid_ratings)
        return None
    
    def get_json(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'student_id': self.student_id,
            'project_id': self.project_id,
            'evaluation_form_path': self.evaluation_form_path,
            'evaluation_period': self.evaluation_period,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'ratings': {
                'overall': self.overall_rating,
                'technical_skills': self.technical_skills_rating,
                'communication': self.communication_rating,
                'professionalism': self.professionalism_rating,
                'teamwork': self.teamwork_rating,
                'problem_solving': self.problem_solving_rating,
                'average': self.calculate_average_rating()
            },
            'strengths': self.strengths,
            'areas_for_improvement': self.areas_for_improvement,
            'comments': self.comments,
            'recommend_for_future_employment': self.recommend_for_future_employment,
            'would_hire_again': self.would_hire_again,
            'internship_completed': self.internship_completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'evaluator': {
                'name': self.evaluator_name,
                'title': self.evaluator_title,
                'email': self.evaluator_email
            },
            'status': self.status,
            'reviewed_by_staff': self.reviewed_by_staff,
            'staff_reviewer_id': self.staff_reviewer_id,
            'staff_notes': self.staff_notes,
            'staff_review_date': self.staff_review_date.isoformat() if self.staff_review_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }
    
    def __repr__(self):
        return f"<StudentEvaluation {self.id}: Student {self.student_id} @ Project {self.project_id} ({self.evaluation_period})>"