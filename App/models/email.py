from App.database import db
from datetime import date
from email_validator import validate_email, EmailNotValidError
from sqlalchemy_imageattach.entity import Image, image_attachment
from App.models.user import user

class Email(db.Model):
    email_id = db.Column(db.Integer,primary_key=True)
    recipient_id= db.Column(db.Integer,ForeignKey("user.user_id"),nullable =False)
    sender_id = db.Column(db.Integer,ForeignKey("user.user_id"),nullable = False)
    subject = db.Column(db.String(50),nullable = False)
    description = db.Column(db.String(500),nullable = False)
    graphic = db.Column(image_attachment("graphic"),nullable=False)
    attachment = db.Column(db.String,nullable = True)
    created_at = db.Column(db.DateTime, default= db.DateTime.utcnow)
    status = db.Column(db.Boolean, nullable =False, default= False)
    
    sender = db.relationship("User",backref="sent_emails",foreign_keys =[sender_id],lazy=True)
    recipient= db.relationship("User",backref="received_emails",foreign_keys=[recipient_id],lazy=True)
    __tablename__ = 'email'

    def __init__(self,student_email,company_email,subject,description,graphic,attachment):
        self.student_email= student_email,
        self.company_email=company_email,
        self.subject = subject,
        self.description=description,
        self.graphic=graphic,
        self.attachment=attachment

    #get all email 
    def get_all_emails(self):
        emails= Email.query.all()
        if not emails:
            return []
        return emails

    #get all email sent by company
    def get_company_sent_emails(self,company_id):
        try:
            #email = Email.query.join(User, Email.sender_id == user.user_id).filter(user.user_id==company_id).all()
            user = User.query.get(company_id)
            if not user:
                print("no company found")
                return[]
            emails = user.sent_emails
            if not emails :
                return []
            return emails
        except Exception as e:
            print("Error retrieving  emails:",e)
            return []

    #get all emails sent by staff
    def get_staff_sent email(self,staff_id):
        try:
            staff_user = User.query.get(staff_id)
            if not staff_user:
                print("staff not found")
                return[]
            emails = staff.sent_emails
            if not emails:
                print("staff has sent zero emails")
                return []
            return emails
        except Exception as e 
            print("exception", e)
            return []

    #get all emails sent to company
    def get_company_receival_emails(self,company_id)
        try:
            company = User.query.get(company_id)
            if not company:
                print("company not found")
            emails = company.received_emails
            if not emails:
                print("company has recieved zero emails")
                return []
            return emails
        except Exception as e 
            print("exception", e)
            return []
    
    #get all email sent to student
    def get_all_student_emails(self,student_id)
        try:
            student = User.query.get(student_id)
            if not student:
                print("student not found")
            emails = student.received_emails
            if not emails:
                print("student has recieved zero emails")
                return []
            return emails
        except Exception as e 
            print("exception", e)
            return []
  
# get inbox

  #get email by header
    

    def get_json(self)
        email = {
            'student_email'= self.student_email,
            'company_email'=self.company_email,
            'subject'=self.subject,
            'description'=self.description,
            'graphic'=self.graphic,
            'attachment'= self.attachment
        }
        return email
    
    def __repr__(self):
        return f'<Email {self.email_id}: {self.student_id} {self.company_id} {self.description}>'