from App.database import db
from App.models.user import User
from datetime import date
import phonenumbers

class Student_application(db.Model):
    application_id = db.Column(db.Integer,primary_key=True)
    student_id = db.Column(db.Integer,db.ForeignKey("student.id"),unique = True,nullable=False)
    first_name = db.Column(db.String,nullable=False)
    last_name =db.Column(db.String,nullable=False)
    email = db.Column(db.String,nullable=False)
    contact_number = db.Column(db.String(7),nullable=False)
    covid_19_vaccination = db.Column(db.Boolean,nullable=False)
    summer_requirment =db.Column(db.bool,nullable=False)
    program =db.Column(db.String,nullable=False)
    cover_letter =db.Column(db.String,nullable=False)
    internship_credits = db.Column(db.Integer,nullable=False)
    citizenship = db.Column(db.String,nullable=False)
    profile_picture = db.Column(db.String,nullable=False)
    returning_intern = db.Column(db.bool,nullable=False)
    year_of_study= db.Column(db.Integer,nullable=False)
    created_on = db.Column(db.Date,nullable=False,default =date.utcnow)
    resume = db.Column(db.String,nullable=False)
    transcript = db.Column(db.String,nullable =False)
    
    def __init__ (self,student_id,first_name,last_name,email,contact_number,covid_19_vaccination,summer_requirment,program,cover_letter,internship_credits,citizenship,profile_picture,returning_intern,year_of_study,resume,transcript):
        self.first_name = first_name
        self.student_id = student_id
        self.last_name=last_name
        self.email= self._validate_uwi_email(email)
        self.contact_number=self._validate_contact_number(contact_number)
        self.covid_19_vaccination = covid_19_vaccination
        self.summer_requirment = summer_requirment
        self.program = program
        self.cover_letter=cover_letter
        self.internship_credits = internship_credits
        self.citizenship=citizenship
        self.profile_picture=profile_picture
        self.returning_intern =returning_intern
        self.year_of_study=year_of_study
        self.resume=resume
        self.transcript=transcript

    def _validate_contact_number(self,contact_number):
        contact_Number_Object = phonenumbers.parse(contact_number)
        if phonenumbers.is_valid_number(contact_Number_Object):
            return contact_number
        else :
            raise ValueError("invalid contact number")
        
    def _validate_uwi_email(self,email):
        email_domains = ["@my.uwi.edu","@uwi.edu","@sta.uwi.edu"]
        if any(email.lower().endswith(domain) for domain in email_domains):
            return email
        else :
            raise ValueError("invalid email..email must a UWI email")


    def get_json(self):
        student_application_json= {
            'first_name': self.first_name,
            'last_name':self.last_name,
            'email':self.email,
            'covid_19_vaccination':self.covid_19_vaccination,
            'summer_required':self.summer_required,
            'program': self.program,
            'cover_letter':self.cover_letter,
            'internship_credit':self.internship_credits,
            'citizenship':self.citizenship,
            'profit_picture':self.profile_picture,
            'returning_intern':self.returning_intern,
            'year_of_study':self.year_of_study,
            'resume':self.resume,
            'transcript':self.transcript
        }

        return student_application_json

    def __repr__(self):
        return f'<Student_application {self.application_id}: {self.student_id} {self.first_name}  {self.last_name} '    



    