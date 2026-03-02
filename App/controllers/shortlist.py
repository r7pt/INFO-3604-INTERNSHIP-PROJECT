from App.models import Shortlist, Student, Project, Staff
from App.database import db
from datetime import datetime

def get_shortlist(shortlist_id):
    return db.session.get(Shortlist, shortlist_id)

def get_all_shortlists():
    return db.session.scalars(db.select(Shortlist)).all()

def get_all_shortlists_json():
    shortlists = get_all_shortlists()
    return [s.get_json() for s in shortlists] if shortlists else []

def create_shortlist(staff_id, student_id, project_id, match_reason=None, match_score=None):
    staff = db.session.get(Staff, staff_id)
    student = db.session.get(Student, student_id)
    project = db.session.get(Project, project_id)
    
    if not staff:
        print("Staff not found")
        return None
    if not student:
        print("Student not found")
        return None
    if not project:
        print("Project not found")
        return None
    
    existing = Shortlist.query.filter_by(
        student_id=student_id,
        project_id=project_id
    ).first()
    
    if existing:
        print("Student already shortlisted for this project")
        return None
    
    try:
        shortlist = Shortlist(
            staff_id=staff_id,
            student_id=student_id,
            project_id=project_id,
            match_reason=match_reason,
            match_score=match_score
        )
        db.session.add(shortlist)
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error creating shortlist: {e}")
        return None

def delete_shortlist(shortlist_id):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return False
    try:
        db.session.delete(shortlist)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting shortlist: {e}")
        return False


def schedule_interview(shortlist_id, interview_date):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    
    try:
        if isinstance(interview_date, str):
            interview_date = datetime.strptime(interview_date, "%Y-%m-%d %H:%M:%S")
        
        shortlist.schedule_interview(interview_date)
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error scheduling interview: {e}")
        return None

def mark_as_interviewed(shortlist_id, interview_notes=None):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    
    try:
        shortlist.mark_as_interviewed(interview_notes)
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error marking as interviewed: {e}")
        return None

def mark_as_hired(shortlist_id):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    
    try:
        shortlist.mark_as_hired()
        
        student = db.session.get(Student, shortlist.student_id)
        if student:
            student.current_internship_status = 'hired'
        
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error marking as hired: {e}")
        return None

def mark_as_rejected(shortlist_id, reason=None):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    
    try:
        shortlist.mark_as_rejected(reason)
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error marking as rejected: {e}")
        return None


def add_staff_note(shortlist_id, staff_id, note):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    
    try:
        shortlist.add_staff_note(note, staff_id)
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error adding staff note: {e}")
        return None

def get_staff_notes(shortlist_id):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    return shortlist.staff_notes

def notify_student_of_shortlist(shortlist_id):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    
    try:
        shortlist.notify_student()
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error notifying student: {e}")
        return None

def notify_company_of_shortlist(shortlist_id):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    
    try:
        shortlist.notify_company()
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error notifying company: {e}")
        return None

def get_shortlists_by_student(student_id):
    return Shortlist.query.filter_by(student_id=student_id).all()

def get_shortlists_by_project(project_id):
    return Shortlist.query.filter_by(project_id=project_id).all()

def get_shortlists_by_staff(staff_id):
    return Shortlist.query.filter_by(shortlisted_by=staff_id).all()

def get_shortlists_by_status(status):
    return Shortlist.query.filter_by(status=status).all()

def get_hired_students():
    return Shortlist.query.filter_by(hired=True).all()

def get_interviewed_students():
    return Shortlist.query.filter_by(interviewed=True).all()

def get_pending_interviews():
    return Shortlist.query.filter_by(
        interview_scheduled=True,
        interviewed=False
    ).all()


def search_shortlists(student_name=None, project_name=None):
    query = Shortlist.query
    
    if student_name:
        query = query.join(Student).filter(
            db.or_(
                Student.first_name.ilike(f"%{student_name}%"),
                Student.last_name.ilike(f"%{student_name}%")
            )
        )
    
    if project_name:
        query = query.join(Project).filter(
            Project.project_name.ilike(f"%{project_name}%")
        )
    
    return query.all()

def filter_shortlists(status=None, interviewed=None, hired=None, staff_id=None):
    query = Shortlist.query
    
    if status:
        query = query.filter_by(status=status)
    if interviewed is not None:
        query = query.filter_by(interviewed=interviewed)
    if hired is not None:
        query = query.filter_by(hired=hired)
    if staff_id:
        query = query.filter_by(shortlisted_by=staff_id)
    
    return query.all()

def get_shortlist_with_details(shortlist_id):
    shortlist = get_shortlist(shortlist_id)
    if not shortlist:
        return None
    
    return {
        **shortlist.get_json(),
        'student': shortlist.student.get_json() if shortlist.student else None,
        'project': shortlist.project.get_json() if shortlist.project else None,
        'staff': shortlist.staff.get_json() if shortlist.staff else None
    }

