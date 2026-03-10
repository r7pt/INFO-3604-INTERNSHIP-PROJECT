from App.database import db
from App.models.company import Company
from App.models.project import Project
from App.models.shortlist import Shortlist
from App.models.student import Student
from datetime import datetime


def get_company(company_id):
    return db.session.get(Company, company_id)

def get_company_by_email(email):
    return Company.query.filter_by(email=email).first()

def get_all_companies():
    return db.session.scalars(db.select(Company)).all()

def get_all_companies_json():
    companies = get_all_companies()
    return [c.get_json() for c in companies] if companies else []

def create_company(company_name, email, website=None, category=None):
    if Company.query.filter_by(email=email).first():
        print("Company email already registered")
        return None
    try:
        company = Company(
            company_name=company_name,
            email=email,
            website=website,
            category=category
        )
        db.session.add(company)
        db.session.commit()
        return company
    except Exception as e:
        db.session.rollback()
        print(f"Error creating company: {e}")
        return None

def update_company(company_id, company_name=None, email=None, website=None, category=None):
    company = get_company(company_id)
    if not company:
        return None
    try:
        if company_name is not None:
            company.company_name = company_name
        if email is not None:
            company.email = email
        if website is not None:
            company.website = website
        if category is not None:
            company.category = category
        company.updated_at = datetime.utcnow()
        db.session.commit()
        return company
    except Exception as e:
        db.session.rollback()
        print(f"Error updating company: {e}")
        return None

def delete_company(company_id):
    company = get_company(company_id)
    if not company:
        return False
    try:
        db.session.delete(company)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting company: {e}")
        return False

def get_company_projects(company_id):
    return Project.query.filter_by(company_id=company_id).order_by(Project.created_at.desc()).all()

def get_company_projects_json(company_id):
    projects = get_company_projects(company_id)
    return [p.get_json() for p in projects] if projects else []

def create_company_project(company_id, project_name, number_of_interns,
                           description=None, details=None, stipend=None,
                           place_of_work=False, international_students=False,
                           hired_after=False, covid_vaccination=False):
    company = get_company(company_id)
    if not company:
        print("Company not found")
        return None
    try:
        project = Project(
            project_name=project_name,
            number_of_interns=number_of_interns,
            description=description,
            details=details,
            stipend=stipend,
            place_of_work=place_of_work,
            international_students=international_students,
            hired_after=hired_after,
            covid_vaccination=covid_vaccination,
            company_id=company_id
        )
        db.session.add(project)
        db.session.commit()
        return project
    except Exception as e:
        db.session.rollback()
        print(f"Error creating project: {e}")
        return None

def delete_company_project(project_id, company_id):
    project = db.session.get(Project, project_id)
    if not project or project.company_id != company_id:
        return False
    try:
        db.session.delete(project)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting project: {e}")
        return False


def get_company_shortlists(company_id):
    return (
        Shortlist.query
        .join(Project)
        .filter(Project.company_id == company_id)
        .order_by(Shortlist.created_at.desc())
        .all()
    )

def get_company_shortlists_json(company_id):
    shortlists = get_company_shortlists(company_id)
    return [s.get_json() for s in shortlists] if shortlists else []

def company_select_for_interview(shortlist_id, company_id, interview_date=None, notes=None):
    shortlist = db.session.get(Shortlist, shortlist_id)
    if not shortlist:
        return None
    project = db.session.get(Project, shortlist.project_id)
    if not project or project.company_id != company_id:
        return None
    try:
        if interview_date:
            if isinstance(interview_date, str):
                interview_date = datetime.fromisoformat(interview_date)
            shortlist.schedule_interview(interview_date)
        else:
            shortlist.mark_as_interviewed(notes)
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error updating interview status: {e}")
        return None

def company_hire_student(shortlist_id, company_id):
    shortlist = db.session.get(Shortlist, shortlist_id)
    if not shortlist:
        return None
    project = db.session.get(Project, shortlist.project_id)
    if not project or project.company_id != company_id:
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
        print(f"Error hiring student: {e}")
        return None

def company_reject_student(shortlist_id, company_id, reason=None):
    shortlist = db.session.get(Shortlist, shortlist_id)
    if not shortlist:
        return None
    project = db.session.get(Project, shortlist.project_id)
    if not project or project.company_id != company_id:
        return None
    try:
        shortlist.mark_as_rejected(reason=reason)
        db.session.commit()
        return shortlist
    except Exception as e:
        db.session.rollback()
        print(f"Error rejecting student: {e}")
        return None


def search_companies(query):
    search = f"%{query}%"
    return Company.query.filter(
        db.or_(
            Company.company_name.ilike(search),
            Company.email.ilike(search),
            Company.category.ilike(search)
        )
    ).all()

def filter_companies(category=None):
    query = Company.query
    if category:
        query = query.filter(Company.category.ilike(f"%{category}%"))
    return query.all()