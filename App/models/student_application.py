from App.database import db
from App.models.user import User
from datetime import datetime
import phonenumbers

class Student_application(db.Model):
    application_id = db.Column(db.Integer,primary_key=True)
    first_name = db.Column(db.String,nullable=False)
    last_name =db.Column(db.String,nullable=False)
    email = db.Column(db.String,unique=True,nullable=False)
    contact_number = db.Column(db.String(7),nullable=False)
    covid_19_vaccination = db.Column(db.Boolean,nullable=False)
    summer_requirment =db.Column(db.String,nullable=False)
    program =db.Column(db.String,nullable=False)
    cover_letter =db.Column(db.String,nullable=False)
    internship_credits = db.Column(db.Integer,nullable=False)
    citizenship = db.Column(db.String,nullable=False)
    profile_picture = db.Column(db.String,nullable=False)
    returning_intern = db.Column(db.Boolean,nullable=False)
    year_of_study= db.Column(db.Integer,nullable=False)
    created_on = db.Column(db.Date,nullable=False,default=datetime.utcnow)
    resume = db.Column(db.String,nullable=False)
    skills =db.Column(db.String,nullable=True)
    transcript = db.Column(db.String,nullable =False)
    status = db.Column(db.String,nullable=False,default="pending")
    created_at= db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    
    transcript_summary = db.relationship("Transcript_summary",uselist=False,back_populates="application",lazy=True)
    __tablename__ ="student_application"


    def __init__ (self,student_id,first_name,last_name,email,contact_number,covid_19_vaccination,summer_requirment,program,cover_letter,internship_credits,citizenship,profile_picture,returning_intern,year_of_study,resume,transcript,skills=None):
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
        self.skills=skills
        self.transcript=transcript
        self.status = 'pending'  

    def set_status(self,status):
        self.status=status

    def get_created_date(self):
        return self.created_at

    def get_application_by_id(student_id):
        try:
            application = Student_application.query.get(student_id=student_id).first()
            if not application:
                print("there is no student application with ",student_id)
                return None
            return application
        except Exception as e:
            print("An error has occurred ", e)
            return None

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_email(self):
        return f'{self.email}'

    def get_student_id(self):
        return f'{self.student_id}'

    def get_contact(self):
        return f'{self.contact_number}'

    def get_program(self):
        return f'{self.program}'

    @staticmethod
    def get_transcript_summary(application_id):
        try:
            application =Application.query.get(application_id)
            if not application:
                print("there is no application with ",application_id)
                return None
            transcript_summary = application.transcript_summary
            if not transcript_summary:
                print("an error occurred with transcript")
                return None
            return transcript_summary
        except Exception as e:
            print("an error occurred ", e)
            return None
            
    def _validate_contact_number(self,contact_number):
        
        contact_Number_Object = phonenumbers.parse(contact_number, None)
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
            'summer_required': self.summer_requirment,
            'program': self.program,
            'cover_letter':self.cover_letter,
            'internship_credit':self.internship_credits,
            'citizenship':self.citizenship,
            'profit_picture':self.profile_picture,
            'returning_intern':self.returning_intern,
            'year_of_study':self.year_of_study,
            'resume':self.resume,
            'transcript':self.transcript,
            'status':self.status
        }

        return student_application_json
    
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        from sqlalchemy.orm.instrumentation import manager_of_class
        manager = manager_of_class(cls)
        if manager:
            manager.setup_instance(instance)
        return instance

    def __repr__(self):
        return f'<Student_application {self.application_id}: {self.student_id}-{self.first_name} -{self.last_name} -{self.status}'    



    