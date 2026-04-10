from App.database import db
import json

class Transcript_summary(db.Model):
    __tablename__ = "transcript_summary"
    
    transcript_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey("student_application.application_id"), nullable=True)
    report = db.Column(db.String, nullable=False) 

   
    application = db.relationship("Student_application", back_populates='transcript_summary')
    
    student = db.relationship("Student", backref="transcript_summaries", lazy=True)

    def __init__(self, student_id, application_id, report):
        self.student_id = student_id
        self.application_id = application_id
        self.report = report

    def get_json(self):
        return {
            "transcript_id": self.transcript_id,
            "student_id": self.student_id,
            "application_id": self.application_id,
            "report": json.loads(self.report) if self.report and self.report.startswith('{') else self.report
        }

    @staticmethod
    def get_transcript_by_id(transcript_id):
        return Transcript_summary.query.get(transcript_id)