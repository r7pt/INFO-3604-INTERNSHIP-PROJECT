from .auth import (
    setup_jwt,
    add_auth_context,
    register_student,
    login,
    whoami
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
