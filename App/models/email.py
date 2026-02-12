from App.database import db
from datetime import date
from email_validator import validate_email, EmailNotValidError
from sqlalchemy_imageattach.entity import Image, image_attachment

class(db.model):
    email_id = db.column(db.Integer,primary_key=True)
    student_email = db.column(db.String,ForeignKey("user.student_id"),nullable = True )
    company_email = db.column(db.String,ForeignKey("user.company_id"),nullable = True)
    subject = db.column(db.String(50),nullable = False)
    description = db.column(db.String(500),nullable = False)
    graphic = db.column(image_attachment("graphic"),nullable=True)
    attachment = db.column(db.String,nullable = True)
    __tablename__ = 'email'

    student = db.relationship("Student",backrefs=("emails"),foreign_keys =[student_id],lazy=True)
    company = db.relationship("Company",backrefs="emails",foreign_keys=[company_id],lazy=True)

    def __init__(self,student_email,company_email,subject,description,graphic,attachment):
        self.student_email= student_email,
        self.company_email=company_email,
        self.subject = subject,
        self.description=description,
        self.graphic=graphic,
        self.attachment=attachment

    def get_json(self)
        email = {
            'student_email'= self.student_email,
            'company_email'=self.company_email,
            'subject'=self.subject,
            'description'=self.description,
            'graphic'=self.graphic,
            'attachment'= self.attachment
        }
        return email
    
    def __repr__(self):
        return f'<Email {self.email_id}: {self.student_id} {self.company_id} {self.description}>'