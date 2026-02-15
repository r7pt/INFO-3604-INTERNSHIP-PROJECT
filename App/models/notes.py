from App.database import db
from App.models.user import User
from App.models.student import Student
from App.models.staff import Staff
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import date

class Notes(db.Model):
    note_id = db.Column(db.Integer,primary_key=True)
    student_id = db.Column(db.Integer,db.ForeignKey=("student.id"),nullable=False)
    staff_id =db.Column(db.Integer,db.ForeignKey=("staff.staff_id"),nullable=False)
    description = db.Column(db.String,nullable=False)
    parent_id = db.Column(db.Integer,db.ForeignKey=("notes.note_id"),nullable=True)
    created_at= db.Column(db.DateTime,default=db.DateTime.utcnow,nullable=False)

    staff= db.relationship('Staff',foreign_keys=['staff_id'],backref="created_by")
    student = db.relationship('Student',foreign_keys=['student_id'],backref="notes")
    parent =db.relationship("Notes",remote_side=[note_id],backref="children")



    def __init__(self,student_id,staff_id,description,parent_id=None):
        self.student_id=student_id
        self.staff_id=staff_id
        self.description=description
        self.parent_id=parent_id

    @staticmethod
    def get_note_by_id(note_id):
        note= Notes.query.get(note_id)
        return note

    def get_all_student_notes(student_id):
        try:
            student= Student.query.get(student_id)
            if not student:
                print("no student found with id",student_id)
                return[]
            notes= student.notes
            if not notes:
                print("the student has zero notes")
            return notes
        except Exception as e:
            print("an error occurred ",e)

    def append_note(self,note_id,staff_id,description):
        try:
            pervious_note = Notes.query.get(note_id)
            if not pervious_note:
                print("no note found with ",note_id)
                return None

            note=Notes(pervious_note.student_id,staff_id,description,pervious_note.note_id)
            db.session.add(note)
            db.session.commit()

            return note
        except Exception as e:
            print("an error occured ",e)
