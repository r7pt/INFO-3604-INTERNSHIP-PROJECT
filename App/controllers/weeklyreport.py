from App.models import WeeklyReport, Student, Project, Staff, Shortlist
from App.database import db
from datetime import datetime

def get_weekly_report(report_id):
    return db.session.get(WeeklyReport, report_id)

def get_all_weekly_reports():
    return db.session.scalars(db.select(WeeklyReport)).all()

def get_all_weekly_reports_json():
    reports = get_all_weekly_reports()
    return [r.get_json() for r in reports] if reports else []

def create_weekly_report(student_id, project_id, week_number, report_file_path,
                        title=None, description=None, hours_worked=None, due_date=None):
    
    student = db.session.get(Student, student_id)
    project = db.session.get(Project, project_id)
    
    if not student:
        print("Student not found")
        return None
    if not project:
        print("Project not found")
        return None
    
    if student.current_internship_status not in ['hired', 'active']:
        print("Student must be hired to upload weekly reports")
        return None

    hired_shortlist = Shortlist.query.filter_by(
        student_id=student_id,
        project_id=project_id,
        status='hired'
    ).first()

    if hired_shortlist is None:
        print("Student is not hired for this project")
        return None
    
    existing = WeeklyReport.query.filter_by(
        student_id=student_id,
        project_id=project_id,
        week_number=week_number
    ).first()
    
    if existing:
        print("Weekly report already exists for this week")
        return None
    
    try:
        if due_date and isinstance(due_date, str):
            due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
        
        report = WeeklyReport(
            student_id=student_id,
            project_id=project_id,
            week_number=week_number,
            report_file_path=report_file_path,
            title=title,
            description=description,
            hours_worked=hours_worked,
            due_date=due_date
        )
        db.session.add(report)
        db.session.commit()
        return report
    except ValueError as e:
        db.session.rollback()
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error creating weekly report: {e}")
        return None

def upload_weekly_report(report_id, file_path):
    report = get_weekly_report(report_id)
    if not report:
        return None
    
    try:
        report.upload_report(file_path)
        db.session.commit()
        return report
    except ValueError as e:
        db.session.rollback()
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error uploading report: {e}")
        return None

def update_weekly_report(report_id, title=None, description=None, hours_worked=None):
    report = get_weekly_report(report_id)
    if not report:
        return None
    
    try:
        if title is not None:
            report.title = title
        if description is not None:
            report.description = description
        if hours_worked is not None:
            report.hours_worked = hours_worked
        
        report.updated_at = datetime.utcnow()
        db.session.commit()
        return report
    except Exception as e:
        db.session.rollback()
        print(f"Error updating weekly report: {e}")
        return None

def delete_weekly_report(report_id):
    report = get_weekly_report(report_id)
    if not report:
        return False
    try:
        db.session.delete(report)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting weekly report: {e}")
        return False

def add_staff_feedback(report_id, staff_id, feedback):
    report = get_weekly_report(report_id)
    if not report:
        return None
    
    staff = db.session.get(Staff, staff_id)
    if not staff:
        print("Staff not found")
        return None
    
    try:
        report.add_staff_feedback(staff_id, feedback)
        db.session.commit()
        return report
    except Exception as e:
        db.session.rollback()
        print(f"Error adding staff feedback: {e}")
        return None

def approve_weekly_report(report_id, staff_id):
    report = get_weekly_report(report_id)
    if not report:
        return None
    
    staff = db.session.get(Staff, staff_id)
    if not staff:
        print("Staff not found")
        return None
    
    try:
        report.approve_report(staff_id)
        db.session.commit()
        return report
    except Exception as e:
        db.session.rollback()
        print(f"Error approving report: {e}")
        return None

def request_revision(report_id, staff_id, feedback):
    report = get_weekly_report(report_id)
    if not report:
        return None
    
    staff = db.session.get(Staff, staff_id)
    if not staff:
        print("Staff not found")
        return None
    
    try:
        report.request_revision(staff_id, feedback)
        db.session.commit()
        return report
    except Exception as e:
        db.session.rollback()
        print(f"Error requesting revision: {e}")
        return None


def get_reports_by_student(student_id):
    return WeeklyReport.query.filter_by(student_id=student_id).order_by(WeeklyReport.week_number).all()

def get_reports_by_project(project_id):
    return WeeklyReport.query.filter_by(project_id=project_id).order_by(WeeklyReport.submission_date.desc()).all()

def get_report_by_student_and_week(student_id, project_id, week_number):
    return WeeklyReport.query.filter_by(
        student_id=student_id,
        project_id=project_id,
        week_number=week_number
    ).first()

def get_reports_by_status(status):
    return WeeklyReport.query.filter_by(status=status).all()

def get_pending_reviews():
    return WeeklyReport.query.filter_by(
        reviewed=False,
        status='submitted'
    ).order_by(WeeklyReport.submission_date).all()

def get_late_reports():
    return WeeklyReport.query.filter_by(is_late=True).all()

def get_reports_needing_revision():
    return WeeklyReport.query.filter_by(status='needs_revision').all()


def search_weekly_reports(student_name=None, project_name=None):
    query = WeeklyReport.query
    
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

def filter_weekly_reports(status=None, reviewed=None, is_late=None, 
                         min_hours=None, max_hours=None, start_date=None, end_date=None):
    query = WeeklyReport.query
    
    if status:
        query = query.filter_by(status=status)
    if reviewed is not None:
        query = query.filter_by(reviewed=reviewed)
    if is_late is not None:
        query = query.filter_by(is_late=is_late)
    if min_hours:
        query = query.filter(WeeklyReport.hours_worked >= min_hours)
    if max_hours:
        query = query.filter(WeeklyReport.hours_worked <= max_hours)
    if start_date:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(WeeklyReport.submission_date >= start_date)
    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(WeeklyReport.submission_date <= end_date)
    
    return query.all()

def get_weekly_report_with_details(report_id):
    report = get_weekly_report(report_id)
    if not report:
        return None
    
    return {
        **report.get_json(),
        'student': report.student.get_json() if report.student else None,
        'project': report.project.get_json() if report.project else None,
        'reviewer': report.reviewer.get_json() if report.reviewer else None
    }

def get_student_report_summary(student_id, project_id):
    reports = WeeklyReport.query.filter_by(
        student_id=student_id,
        project_id=project_id
    ).order_by(WeeklyReport.week_number).all()
    
    if not reports:
        return None
    
    total_hours = sum(r.hours_worked for r in reports if r.hours_worked)
    late_count = sum(1 for r in reports if r.is_late)
    reviewed_count = sum(1 for r in reports if r.reviewed)
    
    return {
        'student_id': student_id,
        'project_id': project_id,
        'total_reports': len(reports),
        'total_hours': total_hours,
        'late_reports': late_count,
        'reviewed_reports': reviewed_count,
        'pending_reviews': len(reports) - reviewed_count,
        'reports': [r.get_json() for r in reports]
    }

