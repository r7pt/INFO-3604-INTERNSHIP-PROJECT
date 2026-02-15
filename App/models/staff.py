from App.database import db
from App.models.user import User
from App.models.shortlist import Shortlist
from App.models.email import Email
from App.models.meeting import Meeting
from App.models.notes import Notes


Class(User) Staff:
    __tablename__ = 'staff'
    staffID = db.Column(db.Integer,db.ForeignKey(user.id),primary_key= true)
    first_name= db.Column(db.String,nullable= False)
    last_name= db.Column(db.String,nullable= False)
    department = db.Column(db.String,nullable= False)
    password = db.Column (db.String, nullable= False)

    def __init__(self,password,first_name,last_name,department,role = "staff"):
        super().__init__(email,password,role)
        self.first_name =first_name
        self.last_name = last_name
        self.department =department
        self.set_password(password)

    def __repr__(self):
        return f'<Staff {self.staffID}: {self.first_name}: {self.last_name}: {self.department}>'

    def send_email(self,recipient_id,subject,description,graphic,attachment):
        try:
            email = Email(self.staffID,recipient_id,subject,description,graphic,attachment)
            db.session.add(email)
            db.session.commit()
            return email
        except Exception as e:
            print("an error occurred ", e)
            return None

    def shortlist_student(self, student_id, project_id, match_reason, match_score):
        try :
            shortlist = Shortlist(self.staff_id, student_id, project_id, match_reason, match_score)
            db.session.add(shortlist)
            db.session.commit()
            return shortlist
        except Exception as e:
            print("an error occurred ", e)
            return None

    def create_meeting(self, student_id, project_id, match_reason, match_score):
        try :
            meeting = Meeting(self.staff_id, student_id, project_id, match_reason, match_score)
            db.session.add(meeting)
            db.session.commit()
            return Meeting
        except Exception as e:
            print("an error occurred ", e)
            return None

    def create_note(self,student_id,description,parent_id):
        try :
            note = Notes(self.staff_id, student_id, project_id, match_reason, match_score)
            db.session.add(note)
            db.session.commit()
            return note
        except Exception as e:
            print("an error occurred ", e)
            return None

    def get_staff_by_id(staff_id):
        staff = Staff.query.get(staff_id)
        if not staff :
            return None
        return staff
        

    def get_json(self):
        base_json = super().get_json()
        staff_json = {
            'first_name': self.first_name,
            'last_name':self.last_name,
            'department':self.department
        }
        return (**base_jason,**student_json)

    def set_password(self,password):
        self.password = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password,password)
