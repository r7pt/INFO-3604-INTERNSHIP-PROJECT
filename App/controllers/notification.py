from sqlalchemy import false
from App.models import Email, Student_application,Company,Student
from App.database import db
#from App.controllers import Email, Student_application,Student

def application_received_notification(Student_application):
    application_subject_template="Internship Application Received"
    application_body_template=("Dear ", Student_application.get_full_name(),"\nThis email is acknowledgement of your internship application. thank you for applying")
    try:
        Email.send_templated_email(student_email,internship_subject_template,application_body_template,context=None,body_html_template=None,attachments=None,cc=None,bcc=None,reply_to=None)
    except Exception as e:
        print("the following error has occurred ".e)
'''
def projectList_received_notification(Company):
    projectList_subject_template="Internship Project List Received"
    projectList_body_template = ("Dear" ,CompanyRegistration.company_name ,"\n this email is acknowledgement of your list of internship projects.")
    try:
        Email.send_templated_email(Company.email,projectList_subject_template,projectList_body_template,context=None,body_html_template=None,attachments=None,cc=None,bcc=None,reply_to=None)
    except Exception as e:
        print("the following error has occurred ".e)
'''
def projectList_received_notification(Company):
    projectList_subject_template = "Internship Project List Received"
    
    projectList_body_template = f"Dear {Company.company_name},\nThis email is acknowledgement of your list of internship projects."
    
    try:
        Email.send_templated_email(
            Company.email,
            projectList_subject_template,
            projectList_body_template,
            context=None,
            body_html_template=None,
            attachments=None,
            cc=None,
            bcc=None,
            reply_to=None
        )
    except Exception as e:
        print("the following error has occurred: ", e)

def weeklyReport_received_notification(Student):
    weeklyReport_subject_template = "Weekly Report Received"
    weeklyReport_body_template = f"Dear {Student.full_name},\nThis email is acknowledgement of your weekly report submission."
    
    try:
        Email.send_templated_email(Student.email, weeklyReport_subject_template, weeklyReport_body_template)
    except Exception as e:
        print("the following error has occurred: ", e)

def accepted_student_received_notification(Company):
    accepted_student_subject_template = "List of internship student Received"
    accepted_student_body_template = f"Dear {Company.company_name},\nThis email is acknowledgement of your list of interested internship student."
    
    try:
        Email.send_templated_email(Company.email, accepted_student_subject_template, accepted_student_body_template)
    except Exception as e:
        print("the following error has occurred: ", e)

def get_announcement_statistics():
    return {"total_notifications": 0, "delivered": 0}