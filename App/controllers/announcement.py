from App.models import Student, Shortlist
from App.database import db
from App.controllers.email_service import send_email, send_templated_email
from datetime import datetime


def notify_all_students_course_orientation(subject, message, email_template=None):
    
    students = Student.query.all()
    
    if not students:
        print("No students found")
        return []
    
    results = []
    for student in students:
        try:
            if email_template:
                result = send_templated_email(
                    to_email=student.email,
                    subject_template=subject,
                    body_template=email_template,
                    context={
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'student_id': student.student_id,
                        'full_name': student.full_name
                    }
                )
            else:
                result = send_email(
                    to_email=student.email,
                    subject=subject,
                    body_text=message
                )
            
            results.append({
                'student_id': student.id,
                'email': student.email,
                'status': 'sent' if result.get('sent') else 'failed'
            })
        except Exception as e:
            print(f"Error sending email to {student.email}: {e}")
            results.append({
                'student_id': student.id,
                'email': student.email,
                'status': 'error',
                'error': str(e)
            })
    
    return results

def notify_shortlisted_students_company_orientation(subject, message, project_id=None, email_template=None):
    if project_id:
        shortlists = Shortlist.query.filter_by(
            project_id=project_id,
            status='shortlisted'
        ).all()
    else:
        shortlists = Shortlist.query.filter_by(status='shortlisted').all()
    
    if not shortlists:
        print("No shortlisted students found")
        return []
    
    results = []
    for shortlist in shortlists:
        student = shortlist.student
        if not student:
            continue
        
        try:
            if email_template:
                result = send_templated_email(
                    to_email=student.email,
                    subject_template=subject,
                    body_template=email_template,
                    context={
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'student_id': student.student_id,
                        'full_name': student.full_name,
                        'project_name': shortlist.project.project_name if shortlist.project else 'N/A',
                        'company_name': shortlist.project.company.company_name if shortlist.project and shortlist.project.company else 'N/A'
                    }
                )
            else:
                result = send_email(
                    to_email=student.email,
                    subject=subject,
                    body_text=message
                )
            results.append({
                'student_id': student.id,
                'shortlist_id': shortlist.id,
                'email': student.email,
                'status': 'sent' if result.get('sent') else 'failed'
            })
        except Exception as e:
            print(f"Error sending email to {student.email}: {e}")
            results.append({
                'student_id': student.id,
                'shortlist_id': shortlist.id,
                'email': student.email,
                'status': 'error',
                'error': str(e)
            })
    
    return results

def notify_student_of_shortlist(shortlist_id, email_template=None):
    shortlist = db.session.get(Shortlist, shortlist_id)
    if not shortlist:
        print("Shortlist not found")
        return None
    
    student = shortlist.student
    if not student:
        print("Student not found")
        return None
    
    try:
        subject = f"Internship Shortlist Notification - {shortlist.project.project_name if shortlist.project else 'Project'}"
        if email_template:
            result = send_templated_email(
                to_email=student.email,
                subject_template=subject,
                body_template=email_template,
                context={
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'full_name': student.full_name,
                    'project_name': shortlist.project.project_name if shortlist.project else 'N/A',
                    'company_name': shortlist.project.company.company_name if shortlist.project and shortlist.project.company else 'N/A',
                    'match_reason': shortlist.match_reason or ''
                }
            )
        else:
            message = f"""
Dear {student.full_name},

Congratulations! You have been shortlisted for the internship project: 
{shortlist.project.project_name if shortlist.project else 'N/A'}

Company: {shortlist.project.company.company_name if shortlist.project and shortlist.project.company else 'N/A'}

The company will review your application and contact you regarding next steps.

Best regards,
Department of Computing and Information Technology
"""
            result = send_email(
                to_email=student.email,
                subject=subject,
                body_text=message
            )
        
        
        if result.get('sent'):
            shortlist.notify_student()
            db.session.commit()
        
        return {
            'student_id': student.id,
            'shortlist_id': shortlist.id,
            'email': student.email,
            'status': 'sent' if result.get('sent') else 'failed'
        }
    
    except Exception as e:
        db.session.rollback()
        print(f"Error notifying student: {e}")
        return {
            'student_id': student.id,
            'shortlist_id': shortlist.id,
            'email': student.email,
            'status': 'error',
            'error': str(e)
        }

def send_bulk_announcement_to_students(subject, message, student_ids=None, filter_status=None, email_template=None):
    if student_ids:
        students = Student.query.filter(Student.id.in_(student_ids)).all()
    elif filter_status:
        students = Student.query.filter_by(current_internship_status=filter_status).all()
    else:
        students = Student.query.all()
    
    if not students:
        print("No students found")
        return []
    
    results = []
    for student in students:
        try:
            if email_template:
                result = send_templated_email(
                    to_email=student.email,
                    subject_template=subject,
                    body_template=email_template,
                    context={
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'full_name': student.full_name,
                        'student_id': student.student_id
                    }
                )
            else:
                result = send_email(
                    to_email=student.email,
                    subject=subject,
                    body_text=message
                )
            
            results.append({
                'student_id': student.id,
                'email': student.email,
                'status': 'sent' if result.get('sent') else 'failed'
            })
        except Exception as e:
            print(f"Error sending email to {student.email}: {e}")
            results.append({
                'student_id': student.id,
                'email': student.email,
                'status': 'error',
                'error': str(e)
            })
    
    return results

def get_announcement_statistics(results):
    if not results:
        return {
            'total': 0,
            'sent': 0,
            'failed': 0,
            'errors': 0
        }
    
    return {
        'total': len(results),
        'sent': sum(1 for r in results if r.get('status') == 'sent'),
        'failed': sum(1 for r in results if r.get('status') == 'failed'),
        'errors': sum(1 for r in results if r.get('status') == 'error')
    }