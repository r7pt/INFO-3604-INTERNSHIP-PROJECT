from App.database import db
from App.models.user import User
from App.models.shortlist import Shortlist

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
