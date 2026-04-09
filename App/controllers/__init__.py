from .auth import (
    setup_jwt,
    add_auth_context,
    register_student,
    login,
    whoami
)


from .auth import *
from .user import (
    create_user,
    get_user,
    get_all_users,
    get_all_users_json,
    get_user_by_email,
    update_user,
    delete_user
)

from .student import (
    get_student,
    get_student_by_email,
    get_student_by_student_id,
    get_all_students,
    get_all_students_json,
    create_student,
    update_student,
    delete_student,
    upload_student_resume,
    upload_student_transcript,
    upload_student_profile_pic,
    set_transcript_summary,
    get_student_application_status,
    update_student_internship_status,
    check_can_apply_to_project,
    get_student_shortlists,
    get_student_shortlists_json,
    get_student_weekly_reports,
    get_student_weekly_reports_json,
    search_students,
    filter_students,
    get_students_by_status
)

from .document import DocumentController

from .project import (
    get_project,
    get_all_projects,
    get_all_projects_json,
    get_company_projects,
    get_company_projects_json,
    create_project,
    update_project,
    delete_project
)


from .evaluation import (
    get_evaluation,
    get_company_evaluations,
    get_company_evaluations_json,
    get_project_evaluations,
    get_student_evaluations,
    create_evaluation,
    update_evaluation,
    delete_evaluation
)

from .shortlist import (
    create_shortlist,
    get_shortlist,
    get_all_shortlists,
    schedule_interview,
    mark_as_hired,
    delete_shortlist
)

from .email import (
    send_email,
    render_email_template,
    send_templated_email,
    list_inbox_emails,
    get_email_by_uid
)
from .staff import (
    get_staff,
    get_staff_by_email,
    get_all_staff,
    get_all_staff_json,
    create_staff,
    update_staff,
    delete_staff,
    get_staff_shortlist,
    get_all_staff_shortlist_json,
    get_staff_notes,
    get_all_staff_note_json
)


from .weeklyreport import (
    get_weekly_report,
    get_all_weekly_reports,
    get_all_weekly_reports_json,
    create_weekly_report,
    upload_weekly_report,
    update_weekly_report,
    delete_weekly_report,
    add_staff_feedback,
    approve_weekly_report,
    request_revision,
    get_reports_by_student,
    get_reports_by_project,
    get_report_by_student_and_week,
    get_reports_by_status,
    get_pending_reviews,
    get_late_reports,
    get_reports_needing_revision,
    search_weekly_reports,
    filter_weekly_reports,
    get_weekly_report_with_details,
    get_student_report_summary
)

from .student_application import create_application, pdf_checker

from .transcript_summary import parse_transcript, Course, Report

from App.controllers.notification import (
    application_received_notification,
    weeklyReport_received_notification,
    get_announcement_statistics
)