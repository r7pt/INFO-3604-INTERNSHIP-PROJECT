from App.database import db
from datetime import date
from sqlalchemy_imageattach.entity import Image, image_attachment


class(db.model):
    application.id = db.Column(db.Integer,primary_key=True)
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
    

    