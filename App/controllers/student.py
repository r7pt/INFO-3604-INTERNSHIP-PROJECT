from App.models import Student, WeeklyReport, Project, Shortlist
from App.database import db
from datetime import datetime, date
import os

def get_student(student_id):
    return db.session.get(Student, student_id)

def get_student_by_email(email):
    return Student.query.filter_by(email=email).first()

def get_student_by_student_id(student_id):
    return Student.query.filter_by(student_id=student_id).first()

def get_all_students():
    return db.session.scalars(db.select(Student)).all()

def get_all_students_json():
    students = get_all_students()
    return [s.get_json() for s in students] if students else []

def create_student(email, password, first_name, last_name, student_id, degree, 
                  phone=None, gender=None, gpa=None, year_of_study=None, 
                  expected_graduation=None, dob=None):
   
    try:
        student = Student(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            student_id=student_id,
            degree=degree
        )
        
        if phone:
            student.phone = phone
        if gender:
            student.gender = gender
        if gpa:
            student.gpa = gpa
        if year_of_study:
            student.year_of_study = year_of_study
        if expected_graduation:
            if isinstance(expected_graduation, str):
                student.expected_graduation = datetime.strptime(expected_graduation, "%Y-%m-%d").date()
            else:
                student.expected_graduation = expected_graduation
        if dob:
            if isinstance(dob, str):
                student.dob = datetime.strptime(dob, "%Y-%m-%d").date()
            else:
                student.dob = dob
        
        db.session.add(student)
        db.session.commit()
        return student
    
    except ValueError as e:
        db.session.rollback()
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error creating student: {e}")
        return None

def update_student(student_id, first_name=None, last_name=None, email=None, 
                  dob=None, gender=None, degree=None, phone=None, gpa=None, 
                  year_of_study=None, expected_graduation=None, profile_pic_path=None,
                  current_internship_status=None):
   
    student = get_student(student_id)
    if not student:
        return None
    
    try:
        if first_name is not None:
            student.first_name = first_name
        if last_name is not None:
            student.last_name = last_name
        if email is not None:
            student.email = email
        if dob is not None:
            if isinstance(dob, str):
                student.dob = datetime.strptime(dob, "%Y-%m-%d").date()
            elif isinstance(dob, date):
                student.dob = dob
        if gender is not None:
            student.gender = gender
        if degree is not None:
            student.degree = degree
        if phone is not None:
            student.phone = phone
        if gpa is not None:
            student.gpa = gpa
        if year_of_study is not None:
            student.year_of_study = year_of_study
        if expected_graduation is not None:
            if isinstance(expected_graduation, str):
                student.expected_graduation = datetime.strptime(expected_graduation, "%Y-%m-%d").date()
            else:
                student.expected_graduation = expected_graduation
        if profile_pic_path is not None:
            student.profile_pic_path = profile_pic_path
        if current_internship_status is not None:
            student.current_internship_status = current_internship_status
        
        db.session.commit()
        return student
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating student: {e}")
        return None

def delete_student(student_id):
    student = get_student(student_id)
    if not student:
        return False
    try:
        db.session.delete(student)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting student: {e}")
        return False

def upload_student_resume(student_id, file_path):
    student = get_student(student_id)
    if not student:
        return None
    
    try:
        student.upload_resume(file_path)
        db.session.commit()
        return student
    except ValueError as e:
        db.session.rollback()
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error uploading resume: {e}")
        return None

def upload_student_transcript(student_id, file_path):
    student = get_student(student_id)
    if not student:
        return None
    
    try:
        student.upload_transcript(file_path)
        db.session.commit()
        return student
    except ValueError as e:
        db.session.rollback()
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error uploading transcript: {e}")
        return None

def upload_student_profile_pic(student_id, file_path):
    student = get_student(student_id)
    if not student:
        return None
    
    try:
        student.profile_pic_path = file_path
        db.session.commit()
        return student
    except Exception as e:
        db.session.rollback()
        print(f"Error uploading profile picture: {e}")
        return None

def set_transcript_summary(student_id, summary):
    student = get_student(student_id)
    if not student:
        return None
    
    try:
        student.transcript_summary = summary
        db.session.commit()
        return student
    except Exception as e:
        db.session.rollback()
        print(f"Error setting transcript summary: {e}")
        return None


def get_student_application_status(student_id):
    student = get_student(student_id)
    if not student:
        return None
    return {
        'student_id': student.student_id,
        'full_name': student.full_name,
        'status': student.current_internship_status,
        'has_resume': bool(student.resume_path),
        'has_transcript': bool(student.transcript_path),
        'can_apply': student.can_apply_to_project(None)  
    }

def update_student_internship_status(student_id, status):
    valid_statuses = ['not_applied', 'applied', 'shortlisted', 'interviewed', 'hired', 'orientation_pending', 'active', 'completed']
    if status not in valid_statuses:
        print(f"Invalid status. Must be one of: {valid_statuses}")
        return None
    
    student = get_student(student_id)
    if not student:
        return None
    
    try:
        student.current_internship_status = status
        db.session.commit()
        return student
    except Exception as e:
        db.session.rollback()
        print(f"Error updating internship status: {e}")
        return None

def check_can_apply_to_project(student_id, project_id):
    student = get_student(student_id)
    project = db.session.get(Project, project_id)
    
    if not student or not project:
        return False
    
    return student.can_apply_to_project(project)

def get_student_shortlists(student_id):
    return Shortlist.query.filter_by(student_id=student_id).all()

def get_student_shortlists_json(student_id):
    shortlists = get_student_shortlists(student_id)
    return [s.get_json() for s in shortlists] if shortlists else []

def get_student_weekly_reports(student_id):
    return WeeklyReport.query.filter_by(student_id=student_id).order_by(WeeklyReport.week_number).all()

def get_student_weekly_reports_json(student_id):
    reports = get_student_weekly_reports(student_id)
    return [r.get_json() for r in reports] if reports else []


def search_students(query):
    search = f"%{query}%"
    return Student.query.filter(
        db.or_(
            Student.first_name.ilike(search),
            Student.last_name.ilike(search),
            Student.student_id.ilike(search),
            Student.email.ilike(search)
        )
    ).all()

def filter_students(degree=None, year_of_study=None, status=None, min_gpa=None, max_gpa=None):
    query = Student.query
    
    if degree:
        query = query.filter(Student.degree.ilike(f"%{degree}%"))
    if year_of_study:
        query = query.filter_by(year_of_study=year_of_study)
    if status:
        query = query.filter_by(current_internship_status=status)
    if min_gpa:
        query = query.filter(Student.gpa >= min_gpa)
    if max_gpa:
        query = query.filter(Student.gpa <= max_gpa)
    
    return query.all()

def get_students_by_status(status):
    return Student.query.filter_by(current_internship_status=status).all()