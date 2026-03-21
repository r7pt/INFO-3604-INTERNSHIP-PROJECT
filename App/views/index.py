
from flask import Blueprint, jsonify, render_template

index_views = Blueprint('index_views', __name__)

@index_views.get('/')
def home():
    return render_template('index.html')

@index_views.get('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@index_views.get('/login')
def login_page():
    return render_template('login.html')

@index_views.get('/register')
@index_views.get('/register/student')
@index_views.get('/register/company')
def register_page():
    return render_template('register.html')

STUDENT_PAGE_META = {
    'overview': ('Student Overview', 'A cleaner student landing page with the overview shown by itself.'),
    'profile': ('My Profile', 'Your account and academic details in a dedicated page.'),
    'documents': ('Documents', 'Upload your CV and transcript on a page of its own.'),
    'status': ('My Status', 'Track your internship matching status on a dedicated page.'),
    'reports': ('Weekly Reports', 'Submit and review weekly reports without other sections mixed in.'),
    'console': ('API Console', 'Developer utility for testing student endpoints.'),
}

COMPANY_PAGE_META = {
    'overview': ('Company Overview', 'A dedicated overview page for your company portal.'),
    'projects': ('Projects', 'Create and manage internship positions on a separate page.'),
    'shortlist': ('Shortlisted Students', 'Review shortlisted candidates without the rest of the dashboard clutter.'),
    'reports': ('Weekly Reports', 'View intern weekly reports on their own page.'),
    'console': ('API Console', 'Developer utility for company endpoint checks.'),
}

STAFF_PAGE_META = {
    'overview': ('Staff Overview', 'A dedicated overview page for the staff side of the portal.'),
    'shortlists': ('Shortlists', 'Match students to projects on a separate page.'),
    'announcements': ('Announcements', 'Create and review announcements on a page of their own.'),
    'meetings': ('Meetings', 'Schedule and review meetings without mixing in other tools.'),
    'reports': ('Weekly Reports', 'Review submitted reports from a dedicated staff page.'),
    'console': ('API Console', 'Developer utility for staff endpoint checks.'),
}

@index_views.get('/student')
@index_views.get('/student/dashboard')
@index_views.get('/student/<page>')
def student_portal(page='overview'):
    page = page if page in STUDENT_PAGE_META else 'overview'
    title, subtitle = STUDENT_PAGE_META[page]
    return render_template('student_portal.html', active_page=page, page_title=title, page_subtitle=subtitle)

@index_views.get('/company')
@index_views.get('/company/dashboard')
@index_views.get('/company/<page>')
def company_dashboard(page='overview'):
    page = page if page in COMPANY_PAGE_META else 'overview'
    title, subtitle = COMPANY_PAGE_META[page]
    return render_template('company_dashboard.html', active_page=page, page_title=title, page_subtitle=subtitle)

@index_views.get('/staff')
@index_views.get('/staff/dashboard')
@index_views.get('/staff/<page>')
def staff_dashboard(page='overview'):
    page = page if page in STAFF_PAGE_META else 'overview'
    title, subtitle = STAFF_PAGE_META[page]
    return render_template('staff_dashboard.html', active_page=page, page_title=title, page_subtitle=subtitle)
