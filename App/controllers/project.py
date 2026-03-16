from datetime import datetime
from App.database import db
from App.models.project import Project


def get_project(project_id):
    return db.session.get(Project, project_id)


def get_all_projects():
    return db.session.scalars(db.select(Project)).all()


def get_all_projects_json():
    projects = get_all_projects()
    return [p.get_json() for p in projects] if projects else []


def get_company_projects(company_id):
    return Project.query.filter_by(company_id=company_id).order_by(Project.created_at.desc()).all()


def get_company_projects_json(company_id):
    projects = get_company_projects(company_id)
    return [p.get_json() for p in projects] if projects else []


def create_project(
    company_id,
    project_name,
    number_of_interns,
    description=None,
    details=None,
    stipend=None,
    place_of_work=False,
    international_students=False,
    hired_after=False,
    covid_vaccination=False,
    registration_id=None
):
    try:
        project = Project(
            project_name=project_name,
            international_students=international_students,
            place_of_work=place_of_work,
            description=description,
            stipend=stipend,
            hired_after=hired_after,
            number_of_interns=number_of_interns,
            details=details,
            covid_vaccination=covid_vaccination,
            company_id=company_id,
            registration_id=registration_id
        )
        db.session.add(project)
        db.session.commit()
        return project
    except Exception as e:
        db.session.rollback()
        print(f"Error creating project: {e}")
        return None


def update_project(
    project_id,
    company_id=None,
    project_name=None,
    number_of_interns=None,
    description=None,
    details=None,
    stipend=None,
    place_of_work=None,
    international_students=None,
    hired_after=None,
    covid_vaccination=None,
    registration_id=None
):
    project = get_project(project_id)
    if not project:
        return None

    if company_id is not None and project.company_id != company_id:
        return None

    try:
        if project_name is not None:
            project.project_name = project_name
        if number_of_interns is not None:
            project.number_of_interns = number_of_interns
        if description is not None:
            project.description = description
        if details is not None:
            project.details = details
        if stipend is not None:
            project.stipend = stipend
        if place_of_work is not None:
            project.place_of_work = place_of_work
        if international_students is not None:
            project.international_students = international_students
        if hired_after is not None:
            project.hired_after = hired_after
        if covid_vaccination is not None:
            project.covid_vaccination = covid_vaccination
        if registration_id is not None:
            project.registration_id = registration_id

        project.updated_at = datetime.utcnow()
        db.session.commit()
        return project
    except Exception as e:
        db.session.rollback()
        print(f"Error updating project: {e}")
        return None


def delete_project(project_id, company_id=None):
    project = get_project(project_id)
    if not project:
        return False

    if company_id is not None and project.company_id != company_id:
        return False

    try:
        db.session.delete(project)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting project: {e}")
        return False