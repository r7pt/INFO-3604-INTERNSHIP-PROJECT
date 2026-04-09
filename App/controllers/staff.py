from App.models import Shortlist, Student, Project, Staff
from App.database import db
from datetime import datetime

def get_staff (staff_id):
    return db.session.get(staff_id)

def get_staff_by_email(email):
    return db.session.filter_by(email=email).first()

def get_all_staff():
    return db.session.scalars(db.select(Student)).all()

def get_all_staff_json():
    all_staff = get_all_staff()
    if all_staff:
        return [staff.get_json() for staff in all_staff]
    else:
        return None

def create_staff(email, password, first_name, last_name, department):
    try:
        if get_staff_by_email(email):
            print("this staff already exist")
            return None
        else:
            staff = Staff(email, password, first_name, last_name, department)
            db.session.add(staff)
            db.session.commit()
            return staff
    except Exception as e:
        db.session.rollback()
        print("the following error occurred while creating staff ", e)
        return None

def update_staff(staff_id,email=None, password=None, first_name=None, last_name=None, department=None):
    try:
        staff = get_staff(staff_id)
        if not staff:
            return None
        else:
            if email!=None:
                staff.email = email
            if password!=None:
                staff.password=password
            if first_name!=None:
                staff.first_name=first_name
            if last_name!=None:
                staff.last_name=last_name
            if department!=None:
                staff.department = department
            db.session.commit()
            return staff
    except Exception as e:
        db.session.rollback()
        print("the following error occurred while updating staff ", e)
        return None

def delete_staff(staff_id):
    try:
        staff = get_staff(staff_id)
        if not staff:
            return None
        db.session.delete(staff)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print("the following error occurred while deleting staff ", e)
        return None

def get_staff_shortlist(staff_id):
    shortlist = Shortlist.query.filter_by(staff_id=staff_id).all()    
    return shortlist

def get_all_staff_shortlist_json(staff_id):
    shortlist = get_staff_shortlist(staffod)
    if shortlist:
        return [list.get_json() for list in shortlist]
    else:
        return None

def get_staff_notes(staff_id):
    notes = Notes.query.filter_by(staff_id=staff_id).all()    
    return notes

def get_all_staff_note_json(staff_id):
    notes = get_all_staff_note(staff_id)
    if notes:
        return [note.get_json() for note in notes]
    else:
        return None