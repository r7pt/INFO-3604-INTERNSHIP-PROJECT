from App.database import db
from App.models.user import User
from App.models.student_application import Student_application
from App.models.student import Student
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import date

class Transcript_summary(db.Model):
    transcript_id = db.Column(db.Integer,primary_key=True)
    student_id= db.Column(db.Integer,db.ForeignKey=("student.id"),nullable=False)
    application_id=db.Column(db.Integer,db.ForeignKey=("student_application.application_id"),nullable=True)
    report = db.Column(db.String,db.nullable=False)

    __tablename__ = "transcript_summary"

    application = db.relationship("Student_application",back_populates='transcript_summary')
    student = db.relationship("Student", backref="student", foreign_keys=['student.id'],lazy =True)

    def __init__(self,student_id,application_id,report):
        self.student_id=student_id
        self.application_id=application_id
        self.report = report

    @staticmethod
    def _get_transcript_by_id(transcript_id):
        transcript_summary= Transcript_summary.query.get(transcript_id)
        if not transcript_summary:
            print("transcript summary not found")
            return None
        return transcript_summary

    def _get_application(transcript_id):
        try:
            transcript_summary= Transcript_summary.query.get(transcript_id)
            if not transcript_summary:
                print("transcript summary not found")
                return None
            application = transcript.application
            if not application:
                print("application not found")
                return None
            return application
        except Exception as e:
            print("an error occurred ", e)
            return None

        def _get_student(transcript_id):
            try:
                transcript_summary= Transcript_summary.query.get(transcript_id)
                if not transcript_summary:
                    print("transcript summary not found")
                    return None
                student = transcript.student
                if not application:
                    print("student not found")
                    return None
                return student
            except Exception as e:
                print("an error occurred ", e)
                return None

    def get_json(self):

        report ={
            "student_id":self.student_id,
            "application_id":application_id,
            "report":self.report
        }

        return report

    def __repr__(self):
        return f'<Transcript report: {self.transcript_id} - {self.student_id} - {self.application_id} - {self.report}'