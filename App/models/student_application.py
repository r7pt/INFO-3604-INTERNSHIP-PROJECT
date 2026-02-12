from App.database import db
from datetime import date
from email_validator import validate_email, EmailNotValidError
from sqlalchemy_imageattach.entity import Image, image_attachment
import re
import phonenumbers

class(db.model):
    application_id = db.Column(db.Integer,primary_key=True)
    first_name = db.Column(db.String,nullable=False)
    last_name =db.Column(db.String,nullable=False)
    email = db.Column(db.String,nullable=False)
    contact_number = db.Column(db.String(7),nullable=False)
    covid_19_vaccination = db.Column(db.bool,nullable=False)
    summer_requirment =db.Column(db.bool,nullable=False)
    program =db.Column(db.String,nullable=False)
    cover_letter =db.Column(db.String,nullable=False)
    internship_credits = db.Column(db.Integer,nullable=False)
    citizenship = db.Column(db.String,nullable=False)
    profile_picture = db.Column(image_attachment("Profile_picture"))
    returning_intern = db.column(db.bool,nullable=False)
    year_of_study= db.column(db.Integer,nullable=False)
    created_on = db.column(db.date,nullable=False,default =datetime.utcnow)
    resume = db.column(db.LargeBinary,nullable=False)
    transcript = db.column(db.LargeBinary,nullable =False)
    
    def __init__ (self,first_name,last_name,email,contact_number,covid_19_vaccination,summer_requirment,program,cover_letter,internship_credits,citizenship,profile_picture,returning_intern,year_of_study,resume,transcript):
        self.first_name = first_name
        self.last_name=last_name
        self.email= _validate_uwi_email(email)
        self.contact_number= _validate_contact_number(contact_number)
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

    def _validate_contact_number(contact_number):
        contact_Number_Object = phonenumbers.parse(contact_number)
        if phonenumbers.is_valid_number(contact_Number_Object):
            return contact_number
        
    def _validate_uwi_email(email):
        email_domains = ["@my.uwi.edu","@uwi.edu","@sta.uwi.edu"]
        return  any(email.lower().endswith(domain) for domain in valid_domains)

    def get_json(self):
        student_application_json= 
        {
            'first_name'= self.first_name,
            'last_name'=self.last_name,
            'email'=self.email,
            'covid_19_vaccination'=self.covid_19_vaccination,
            'summer_required'=self.summer_required,
            'program'= self.program,
            'cover_letter'=self.cover_letter,
            'internship_credit'=self.internship_credits,
            'citizenship'=self.citizenship,
            'profit_picture'=self.profile_picture,
            'returning_intern'=self.returning_intern,
            'year_of_study'=self.year_of_study,
            'resume'=self.resume,
            'transcript'=self.transcript
        }

        return student_application_json

    def __repr(self):
        return f'<Student_application {self.application_id}: {self.student_id} {self.first_name}  {self.last_name} '    



    