from App.models import Student_application,Student, WeeklyReport, Project, Shortlist
from App.database import db
from datetime import datetime, date
import os
import re, magic 


#getters,stu id,name,all,
#get_application thing 
#create application
#delete application
#sanitzantion,vaildation
 #get student if student has more than 1 application

def get_application(application_id):
    return db.session.get(application)

def get_application_by_student_id(student_id):
    application = Student_application.get_application_by_id(student_id)
    return application

def get_applicationby_email(email):
    try:
        application =  Student_application.query.filter_by(email=email).first()
        if not application:
            print("No application found with student email : ",email)
            return None
        return application
    except Exception as e:
        print( "the following error occurred : ",e)
        return None

def get_all_application():
    try:
        applications = Student_application.query.all()
        if not applications:
            print("there are no application")
            return None
        return applications
    except Exception as e :
        print("the following error occured : ",e )
        return None
    
def get_application_resume(student_id):
    try:
        application = get_application_by_student_id(student_id)
        resume = application.resume
        return resume
    except Exception as e: 
        print("the following error occured : ",e )
        return None

def get_application_transcript(student_id):
    try:
        application = get_application_by_student_id(student_id)
        transcript = application.transcript
        return transcript
    except Exception as e: 
        print("the following error occured : ",e )
        return None

def pdf_checker(file):
     return (magic.from_file(file,mime=True) != "application/pdf")
            
    
def create_application(student_id,first_name,last_name,email,contact_number,covid_19_vaccination,summer_requirment,program,cover_letter,internship_credits,citizenship,profile_picture,returning_intern,year_of_study,resume,transcript):

    try:
        valid_id = bool(re.match(r'\d{8}$',student_id))
        if not valid_id:
            print("the student ID is invalid format, must be 8 digits")
            raise e

        validname = bool(re.match(r'^[a-zA-Z\s]{1,50}$',first_name))
        if not validname:
            print("the first name is invalid format, must be only alphabetic letters and 50 charaters long",e)
            raise e

        validname = bool(re.match(r'^[a-zA-Z\s]{1,50}$',last_name))
        if not validname:
            print("the first name is invalid format, must be only alphabetic letters and 50 charaters long",e)
            raise e

        valid_email = student_application._validate_uwi_email(email)
        if not valid_email:
            print("the email is invalid, must be a UWI mail",e)
            raise e
        
        validcontact = (bool(re.match(r'^868\d{7}$',contact_number)) or bool(re.match(r'^\d{7}$',contact_number)))
        if not validcontact:
            print("the first name is invalid format, must be only alphabetic letters and 50 charaters long",e)
            raise e
            
        if (type(covid_19_vaccination)!=Boolean):
            print("the covid 19 vaccination status must be a boolean",e)
            raise e

        if (summer_requirment != "Yes") or (summer_requirment != "No") or (summer_requirment != "Not Sure"):
            print("the invalid summer_requirement",e)
            raise e

        valid_year_of_study = (bool(re.match('^[2-5]$',year_of_study)))
        if not valid_year_of_study:
            print("the invalid year of study",e)
            raise e
        
        if (type(returning_intern)!=Boolean):
            print("the returning intern must be a boolean",e)
            raise e

        validCoverLetter = bool(re.match(r'^[a-zA-Z\s]{1,400}$',cover_letter))
        if not validCoverLetter:
            print("the cover letter is invalid format, must be only alphabetic letters and at most 400 charaters long",e)
            raise e

        if (magic.from_file(profile_picture,mime=True) != "image/jpeg"):
            print("the profile picture must be a JPEG format",e)
            raise e
        
        if not (pdf_checker(resume)):
            print("the resmue must be a PDF format",e)
            raise e

        if not (pdf_checker(transcript)):
            print("the transcript must be a PDF format",e)
            raise e

        application=Student_application(student_id,first_name,last_name,email,contact_number,covid_19_vaccination,summer_requirment,program,cover_letter,internship_credits,citizenship,profile_picture,returning_intern,year_of_study,resume,transcript)
        db.session.add(application)
        db.session.commit()

    except Exception as e:
        print("the following error occurred : ",e)
        db.session.rollback()

def delete_application(student_id):
    try:
        application = get_application_by_student_id(student_id)
        if not application:
            print("there is no application with student id : ",student_id)
            return None
        return application
    except Exception as e:
        print("the following error occurred : ",e)
        return None
        



        


        

        


        








