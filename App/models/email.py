from App.database import db
from datetime import datetime
#from sqlalchemy_imageattach.entity import Image, image_attachment
from App.models.user import User
import re

class Email(db.Model):
    email_id = db.Column(db.Integer,primary_key=True)
    recipient_id= db.Column(db.Integer,db.ForeignKey("user.id"),nullable =False)
    sender_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable = False)
    subject = db.Column(db.String(50),nullable = False)
    description = db.Column(db.String(500),nullable = False)
    #graphic = db.Column(image_attachment("graphic"),nullable=False)
    attachment = db.Column(db.String,nullable = True)
    created_at = db.Column(db.DateTime, default= datetime.utcnow)
    status = db.Column(db.Boolean, nullable =False, default= False)
    
    sender = db.relationship("User",backref="sent_emails",foreign_keys =[sender_id],lazy=True)
    recipient= db.relationship("User",backref="received_emails",foreign_keys=[recipient_id],lazy=True)
    __tablename__ = 'email'

    def __init__(self,sender_id,recipient_id,subject,description,graphic,attachment):
        self.sender_id= sender_id
        self.recipient_id=recipient_id
        self.subject = subject
        self.description=description
        self.graphic=graphic
        self.attachment=attachment

    #get all email 
    def get_all_emails(self):
        emails= Email.query.all()
        if not emails:
            return []
        return emails

    #get all emails by user
    def get_all_emails_by_user(self,user_id):
        user = User.query.get(user_id)
        if not user:
            print("user not found with id", user_id)
            return []
        emails =[]
        if user.role != "student":
            emails.extend(user.sent_emails)
        emails.extend(user.received_emails)
        return emails
        
    #get all email sent by 
    def get_all_emails_sent_by_user(self,user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                print("no user found with ",user_id)
                return[]
            if user.role == "student":
                print(user.full_name," is not authorized to send emails")
                return []
            emails = user.sent_emails
            if not emails :
                print(user.full_name," has zero emails")
                return []
            return emails
        except Exception as e:
            print("Error retrieving  emails:",e)
            return []

    #get all email recieved by
    def get_all_emails_recieved_by_user(self,user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                print("no user found with ",user_id)
                return[]
            emails = user.received_emails
            if not emails :
                print(user.full_name," has zero emails")
                return []
            return emails
        except Exception as e:
            print("Error retrieving  emails:",e)
            return []

    #find keyword in header
    def search_email_header(self,keyword):
        try:
            search_results= []
            count = 0
            emails= self.get_all_emails()
            pattern = re.compile(keyword,re.IGNORECASE)

            for email in emails:
                if pattern.search(pattern,email.subject) or pattern.search(pattern,email.description)  :
                    search_results.append(email)
                    count+=1
            if not search_results:
                print("zero matches found")
            return search_results,count
        except Exception as e:
            print("an error occurred",e)
            return []
            
    #reply email
    @staticmethod 
    def reply_email(email_id,description,attachment,graphic):
        try:
            old_mail = Email.query.get(email_id)
            if not old_mail:
                print('email not found with ', email_id)
                return None
            new_email = Email(old_mail.sender_id,old_mail.recipient_id,old_mail.subject,description,graphic,attachment)
            if not new_email:
                print("an error occurred with new email")
                return None
            db.session.add(new_email)
            db.session.commit()
            return new_email
        except Exception as e:
            print("the following error occured : ",e)
            return None

    def get_json(self):
        email = {
            'sender_id': self.sender_id,
            'recipient_id':self.recipient_id,
            'subject':self.subject,
            'description':self.description,
            'graphic':self.graphic,
            'attachment': self.attachment
        }
        return email
    
    def __repr__(self):
        return f'<Email {self.email_id}: {self.sender_id}-{self.recipient_id}-{self.description}>'