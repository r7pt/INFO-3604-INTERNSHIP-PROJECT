from App.database import db
from App.models.user import User
from App.models.student_application import Application
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import date

class transcript_summary(db.Model):
    transcript_id = db.Column(db.Integer,primary_key=True)
    student_id= db.Column(db.Integer,db.ForeignKey=("student.id"),nullable=False)
    application_id=db.Column(db.Integer,db.ForeignKey=("application.application_id"),nullable=True)
    report = db.Column(db.String,db.nullable=False)

    def __init__(self,student_id,application_id,report):
        self.student_id=student_id
        self.application_id=application_id
        self.report

    def get_json(self,student_id,application_id,report):

        report ={
            "student_id":self.student_id,
            "application_id":application_id,
            "report":self.report
        }

        return report

    def __repr__(self):
        return f'<Transcript report: {self.transcript_id} - {self.student_id} - {self.application_id} - {self.report}'