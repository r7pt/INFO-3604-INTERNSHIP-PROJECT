from datetime import datetime, date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import or_, func

from App.database import db
from App.controllers.auth import login
from App.models.staff import Staff
from App.models.student import Student
from App.models.company import Company
from App.models.project import Project
from App.models.shortlist import Shortlist
from App.models.announcement import Announcement
from App.models.weeklyreport import WeeklyReport
from App.models.Meeting import Meeting
from App.models.studentevaluation import StudentEvaluation


staff_views = Blueprint("staff_views", __name__, url_prefix="/api/staff")


def _json_error(message, status=400, extra=None):
    payload = {"error": message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _require_staff():
    if current_user is None:
        return None, _json_error("Not authenticated", 401)
    if getattr(current_user, "role", None) != "staff":
        return None, _json_error("Forbidden - staff access only", 403)
    staff = db.session.get(Staff, current_user.id)
    if staff is None:
        return None, _json_error("Staff profile not found", 404)
    return staff, None


def _parse_bool(value, default=None):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    return default


def _parse_int(value, field_name, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer")


def _parse_float(value, field_name, default=None):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number")


def _parse_datetime(value, field_name):
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        raise ValueError(f"{field_name} must be a valid ISO 8601 datetime")


def _parse_date(value, field_name):
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValueError(f"{field_name} must be a valid ISO 8601 date")


def _student_payload(student):
    return {
        **student.get_json(),
        "resume_path": student.resume_path,
        "transcript_path": student.transcript_path,
        "transcript_summary": student.transcript_summary,
    }


def _company_payload(company):
    data = company.get_json()
    data["project_count"] = len(company.projects or [])
    return data


def _project_payload(project):
    return {
        **project.get_json(),
        "description": project.description,
        "details": project.details,
        "company_id": project.company_id,
        "company_name": project.company.company_name if getattr(project, "company", None) else None,
        "registration_id": project.registration_id,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def _shortlist_payload(shortlist):
    return {
        **shortlist.get_json(),
        "student": _student_payload(shortlist.student) if shortlist.student else None,
        "project": _project_payload(shortlist.project) if shortlist.project else None,
        "staff": shortlist.staff.get_json() if shortlist.staff else None,
    }


def _weekly_report_payload(report):
    return {
        **report.get_json(),
        "student": _student_payload(report.student) if report.student else None,
        "project": _project_payload(report.project) if report.project else None,
    }


def _meeting_payload(meeting):
    return {
        **meeting.get_json(),
        "student": _student_payload(meeting.student) if meeting.student else None,
        "project": _project_payload(meeting.project) if meeting.project else None,
        "staff": meeting.staff.get_json() if meeting.staff else None,
    }


def _evaluation_payload(evaluation):
    return {
        **evaluation.get_json(),
        "student": _student_payload(evaluation.student) if evaluation.student else None,
        "project": _project_payload(evaluation.project) if evaluation.project else None,
        "company": _company_payload(evaluation.company) if evaluation.company else None,
    }


@staff_views.post("/login")
def api_staff_login():
    return login()


@staff_views.get("/me")
@jwt_required()
def api_staff_me():
    staff, err = _require_staff()
    if err:
        return err
    return jsonify({"user": staff.get_json()}), 200


@staff_views.get("/dashboard")
@jwt_required()
def api_staff_dashboard():
    staff, err = _require_staff()
    if err:
        return err

    now = datetime.utcnow()

    total_students = db.session.query(func.count(Student.id)).scalar() or 0
    total_companies = db.session.query(func.count(Company.id)).scalar() or 0
    total_projects = db.session.query(func.count(Project.id)).scalar() or 0
    total_shortlists = db.session.query(func.count(Shortlist.id)).scalar() or 0

    students_missing_resume = db.session.query(func.count(Student.id)).filter(
        or_(Student.resume_path.is_(None), Student.resume_path == "")
    ).scalar() or 0

    students_missing_transcript = db.session.query(func.count(Student.id)).filter(
        or_(Student.transcript_path.is_(None), Student.transcript_path == "")
    ).scalar() or 0

    pending_weekly_reports = db.session.query(func.count(WeeklyReport.id)).filter(
        WeeklyReport.status.in_(["submitted", "needs_revision"])
    ).scalar() or 0

    pending_evaluations = db.session.query(func.count(StudentEvaluation.id)).filter(
        StudentEvaluation.reviewed_by_staff.is_(False)
    ).scalar() or 0

    upcoming_meetings = Meeting.query.filter(
        Meeting.staff_id == staff.id,
        Meeting.scheduled_at >= now,
        Meeting.status == "scheduled",
    ).order_by(Meeting.scheduled_at.asc()).limit(10).all()

    upcoming_interviews = Shortlist.query.filter(
        Shortlist.interview_date.isnot(None),
        Shortlist.interview_date >= now,
        Shortlist.status == "interview_scheduled",
    ).order_by(Shortlist.interview_date.asc()).limit(10).all()

    recent_shortlists = Shortlist.query.order_by(Shortlist.created_at.desc()).limit(10).all()

    return jsonify({
        "counts": {
            "students": total_students,
            "companies": total_companies,
            "projects": total_projects,
            "shortlists": total_shortlists,
            "students_missing_resume": students_missing_resume,
            "students_missing_transcript": students_missing_transcript,
            "pending_weekly_reports": pending_weekly_reports,
            "pending_evaluations": pending_evaluations,
        },
        "upcoming_meetings": [_meeting_payload(m) for m in upcoming_meetings],
        "upcoming_interviews": [_shortlist_payload(s) for s in upcoming_interviews],
        "recent_shortlists": [_shortlist_payload(s) for s in recent_shortlists],
    }), 200


@staff_views.get("/students")
@jwt_required()
def api_staff_students():
    _, err = _require_staff()
    if err:
        return err

    query = Student.query

    q = request.args.get("q")
    degree = request.args.get("degree")
    status = request.args.get("status")
    year_of_study = request.args.get("year_of_study")
    min_gpa = request.args.get("min_gpa")
    max_gpa = request.args.get("max_gpa")
    has_resume = request.args.get("has_resume")
    has_transcript = request.args.get("has_transcript")

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Student.first_name.ilike(search),
                Student.last_name.ilike(search),
                Student.student_id.ilike(search),
                Student.email.ilike(search),
            )
        )

    if degree:
        query = query.filter(Student.degree.ilike(f"%{degree.strip()}%"))

    if status:
        query = query.filter(Student.current_internship_status == status.strip())

    if year_of_study:
        try:
            query = query.filter(Student.year_of_study == _parse_int(year_of_study, "year_of_study"))
        except ValueError as e:
            return _json_error(str(e), 400)

    if min_gpa:
        try:
            query = query.filter(Student.gpa >= _parse_float(min_gpa, "min_gpa"))
        except ValueError as e:
            return _json_error(str(e), 400)

    if max_gpa:
        try:
            query = query.filter(Student.gpa <= _parse_float(max_gpa, "max_gpa"))
        except ValueError as e:
            return _json_error(str(e), 400)

    if has_resume is not None:
        resume_required = _parse_bool(has_resume)
        if resume_required is True:
            query = query.filter(Student.resume_path.isnot(None), Student.resume_path != "")
        elif resume_required is False:
            query = query.filter(or_(Student.resume_path.is_(None), Student.resume_path == ""))

    if has_transcript is not None:
        transcript_required = _parse_bool(has_transcript)
        if transcript_required is True:
            query = query.filter(Student.transcript_path.isnot(None), Student.transcript_path != "")
        elif transcript_required is False:
            query = query.filter(or_(Student.transcript_path.is_(None), Student.transcript_path == ""))

    students = query.order_by(Student.last_name.asc(), Student.first_name.asc()).all()
    return jsonify({"students": [_student_payload(s) for s in students]}), 200


@staff_views.get("/students/<int:student_id>")
@jwt_required()
def api_staff_student_detail(student_id):
    _, err = _require_staff()
    if err:
        return err

    student = db.session.get(Student, student_id)
    if student is None:
        return _json_error("Student not found", 404)

    shortlists = Shortlist.query.filter_by(student_id=student_id).order_by(Shortlist.created_at.desc()).all()
    weekly_reports = WeeklyReport.query.filter_by(student_id=student_id).order_by(WeeklyReport.week_number.asc()).all()
    evaluations = StudentEvaluation.query.filter_by(student_id=student_id).order_by(StudentEvaluation.created_at.desc()).all()
    meetings = Meeting.query.filter_by(student_id=student_id).order_by(Meeting.scheduled_at.desc()).all()

    return jsonify({
        "student": _student_payload(student),
        "shortlists": [_shortlist_payload(s) for s in shortlists],
        "weekly_reports": [_weekly_report_payload(r) for r in weekly_reports],
        "evaluations": [_evaluation_payload(e) for e in evaluations],
        "meetings": [_meeting_payload(m) for m in meetings],
    }), 200


@staff_views.patch("/students/<int:student_id>")
@jwt_required()
def api_staff_update_student(student_id):
    _, err = _require_staff()
    if err:
        return err

    student = db.session.get(Student, student_id)
    if student is None:
        return _json_error("Student not found", 404)

    data = request.get_json(silent=True) or {}

    try:
        if "first_name" in data:
            student.first_name = str(data["first_name"]).strip()
        if "last_name" in data:
            student.last_name = str(data["last_name"]).strip()
        if "phone" in data:
            student.phone = str(data["phone"]).strip() if data["phone"] is not None else None
        if "gender" in data:
            student.gender = str(data["gender"]).strip() if data["gender"] is not None else None
        if "degree" in data:
            student.degree = str(data["degree"]).strip()
        if "gpa" in data:
            student.gpa = _parse_float(data["gpa"], "gpa")
        if "year_of_study" in data:
            student.year_of_study = _parse_int(data["year_of_study"], "year_of_study")
        if "expected_graduation" in data:
            student.expected_graduation = _parse_date(data["expected_graduation"], "expected_graduation")
        if "current_internship_status" in data:
            student.current_internship_status = str(data["current_internship_status"]).strip()
        if "transcript_summary" in data:
            student.transcript_summary = data["transcript_summary"]
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return _json_error(str(e), 400)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update student", 500)

    return jsonify({"message": "Student updated", "student": _student_payload(student)}), 200


@staff_views.patch("/students/<int:student_id>/status")
@jwt_required()
def api_staff_update_student_status(student_id):
    _, err = _require_staff()
    if err:
        return err

    student = db.session.get(Student, student_id)
    if student is None:
        return _json_error("Student not found", 404)

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if not status:
        return _json_error("status is required", 400)

    try:
        student.current_internship_status = str(status).strip()
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update student status", 500)

    return jsonify({"message": "Student status updated", "student": _student_payload(student)}), 200


@staff_views.patch("/students/<int:student_id>/transcript-summary")
@jwt_required()
def api_staff_update_transcript_summary(student_id):
    _, err = _require_staff()
    if err:
        return err

    student = db.session.get(Student, student_id)
    if student is None:
        return _json_error("Student not found", 404)

    data = request.get_json(silent=True) or {}
    summary = data.get("transcript_summary")
    if summary is None:
        return _json_error("transcript_summary is required", 400)

    try:
        student.transcript_summary = str(summary)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update transcript summary", 500)

    return jsonify({"message": "Transcript summary updated", "student": _student_payload(student)}), 200


@staff_views.get("/companies")
@jwt_required()
def api_staff_companies():
    _, err = _require_staff()
    if err:
        return err

    query = Company.query
    q = request.args.get("q")
    category = request.args.get("category")

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Company.company_name.ilike(search),
                Company.email.ilike(search),
                Company.website.ilike(search),
            )
        )

    if category:
        query = query.filter(Company.category.ilike(f"%{category.strip()}%"))

    companies = query.order_by(Company.company_name.asc()).all()
    return jsonify({"companies": [_company_payload(c) for c in companies]}), 200


@staff_views.get("/companies/<int:company_id>")
@jwt_required()
def api_staff_company_detail(company_id):
    _, err = _require_staff()
    if err:
        return err

    company = db.session.get(Company, company_id)
    if company is None:
        return _json_error("Company not found", 404)

    projects = Project.query.filter_by(company_id=company_id).order_by(Project.created_at.desc()).all()
    evaluations = StudentEvaluation.query.filter_by(company_id=company_id).order_by(StudentEvaluation.created_at.desc()).all()

    return jsonify({
        "company": _company_payload(company),
        "projects": [_project_payload(p) for p in projects],
        "evaluations": [_evaluation_payload(e) for e in evaluations],
    }), 200


@staff_views.get("/projects")
@jwt_required()
def api_staff_projects():
    _, err = _require_staff()
    if err:
        return err

    query = Project.query
    q = request.args.get("q")
    company_id = request.args.get("company_id")

    if q:
        search = f"%{q.strip()}%"
        query = query.join(Company).filter(
            or_(
                Project.project_name.ilike(search),
                Project.description.ilike(search),
                Project.details.ilike(search),
                Company.company_name.ilike(search),
            )
        )

    if company_id:
        try:
            query = query.filter(Project.company_id == _parse_int(company_id, "company_id"))
        except ValueError as e:
            return _json_error(str(e), 400)

    projects = query.order_by(Project.created_at.desc()).all()
    return jsonify({"projects": [_project_payload(p) for p in projects]}), 200


@staff_views.post("/projects")
@jwt_required()
def api_staff_create_project():
    _, err = _require_staff()
    if err:
        return err

    data = request.get_json(silent=True) or {}

    required = ["company_id", "project_name", "number_of_interns"]
    missing = [k for k in required if data.get(k) in [None, ""]]
    if missing:
        return _json_error("Missing required fields", 400, {"missing": missing})

    try:
        company_id = _parse_int(data.get("company_id"), "company_id")
        number_of_interns = _parse_int(data.get("number_of_interns"), "number_of_interns")
        stipend = _parse_float(data.get("stipend"), "stipend")
    except ValueError as e:
        return _json_error(str(e), 400)

    company = db.session.get(Company, company_id)
    if company is None:
        return _json_error("Company not found", 404)

    try:
        project = Project(
            project_name=str(data.get("project_name")).strip(),
            international_students=_parse_bool(data.get("international_students"), False),
            place_of_work=_parse_bool(data.get("place_of_work"), False),
            description=data.get("description"),
            stipend=stipend,
            hired_after=_parse_bool(data.get("hired_after"), False),
            number_of_interns=number_of_interns,
            details=data.get("details"),
            covid_vaccination=_parse_bool(data.get("covid_vaccination"), False),
            company_id=company_id,
            registration_id=data.get("registration_id"),
        )
        db.session.add(project)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to create project", 500)

    return jsonify({"message": "Project created", "project": _project_payload(project)}), 201


@staff_views.patch("/projects/<int:project_id>")
@jwt_required()
def api_staff_update_project(project_id):
    _, err = _require_staff()
    if err:
        return err

    project = db.session.get(Project, project_id)
    if project is None:
        return _json_error("Project not found", 404)

    data = request.get_json(silent=True) or {}

    try:
        if "project_name" in data:
            project.project_name = str(data["project_name"]).strip()
        if "description" in data:
            project.description = data["description"]
        if "details" in data:
            project.details = data["details"]
        if "stipend" in data:
            project.stipend = _parse_float(data["stipend"], "stipend")
        if "number_of_interns" in data:
            project.number_of_interns = _parse_int(data["number_of_interns"], "number_of_interns")
        if "international_students" in data:
            project.international_students = _parse_bool(data["international_students"], project.international_students)
        if "place_of_work" in data:
            project.place_of_work = _parse_bool(data["place_of_work"], project.place_of_work)
        if "hired_after" in data:
            project.hired_after = _parse_bool(data["hired_after"], project.hired_after)
        if "covid_vaccination" in data:
            project.covid_vaccination = _parse_bool(data["covid_vaccination"], project.covid_vaccination)
        if "company_id" in data:
            company_id = _parse_int(data["company_id"], "company_id")
            company = db.session.get(Company, company_id)
            if company is None:
                return _json_error("Company not found", 404)
            project.company_id = company_id
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return _json_error(str(e), 400)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update project", 500)

    return jsonify({"message": "Project updated", "project": _project_payload(project)}), 200


@staff_views.delete("/projects/<int:project_id>")
@jwt_required()
def api_staff_delete_project(project_id):
    _, err = _require_staff()
    if err:
        return err

    project = db.session.get(Project, project_id)
    if project is None:
        return _json_error("Project not found", 404)

    try:
        db.session.delete(project)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to delete project", 500)

    return jsonify({"message": "Project deleted"}), 200


@staff_views.get("/shortlists")
@jwt_required()
def api_staff_shortlists():
    _, err = _require_staff()
    if err:
        return err

    query = Shortlist.query
    status = request.args.get("status")
    student_id = request.args.get("student_id")
    project_id = request.args.get("project_id")
    staff_id = request.args.get("staff_id")

    if status:
        query = query.filter(Shortlist.status == status)

    try:
        if student_id:
            query = query.filter(Shortlist.student_id == _parse_int(student_id, "student_id"))
        if project_id:
            query = query.filter(Shortlist.project_id == _parse_int(project_id, "project_id"))
        if staff_id:
            query = query.filter(Shortlist.staff_id == _parse_int(staff_id, "staff_id"))
    except ValueError as e:
        return _json_error(str(e), 400)

    shortlists = query.order_by(Shortlist.created_at.desc()).all()
    return jsonify({"shortlists": [_shortlist_payload(s) for s in shortlists]}), 200


@staff_views.get("/shortlists/<int:shortlist_id>")
@jwt_required()
def api_staff_shortlist_detail(shortlist_id):
    _, err = _require_staff()
    if err:
        return err

    shortlist = db.session.get(Shortlist, shortlist_id)
    if shortlist is None:
        return _json_error("Shortlist not found", 404)

    return jsonify({"shortlist": _shortlist_payload(shortlist)}), 200


@staff_views.post("/shortlists")
@jwt_required()
def api_staff_create_shortlist():
    staff, err = _require_staff()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    required = ["student_id", "project_id"]
    missing = [k for k in required if data.get(k) in [None, ""]]
    if missing:
        return _json_error("Missing required fields", 400, {"missing": missing})

    try:
        student_id = _parse_int(data.get("student_id"), "student_id")
        project_id = _parse_int(data.get("project_id"), "project_id")
        match_score = _parse_float(data.get("match_score"), "match_score")
    except ValueError as e:
        return _json_error(str(e), 400)

    student = db.session.get(Student, student_id)
    if student is None:
        return _json_error("Student not found", 404)

    project = db.session.get(Project, project_id)
    if project is None:
        return _json_error("Project not found", 404)

    existing = Shortlist.query.filter_by(student_id=student_id, project_id=project_id).first()
    if existing is not None:
        return _json_error("Student already shortlisted for this project", 409)

    try:
        shortlist = Shortlist(
            staff_id=staff.id,
            student_id=student_id,
            project_id=project_id,
            match_reason=data.get("match_reason"),
            match_score=match_score,
        )
        db.session.add(shortlist)
        student.current_internship_status = "shortlisted"
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to create shortlist", 500)

    return jsonify({"message": "Student shortlisted", "shortlist": _shortlist_payload(shortlist)}), 201


@staff_views.patch("/shortlists/<int:shortlist_id>")
@jwt_required()
def api_staff_update_shortlist(shortlist_id):
    staff, err = _require_staff()
    if err:
        return err

    shortlist = db.session.get(Shortlist, shortlist_id)
    if shortlist is None:
        return _json_error("Shortlist not found", 404)

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()

    try:
        if action == "schedule_interview":
            interview_date = _parse_datetime(data.get("interview_date"), "interview_date")
            if interview_date is None:
                return _json_error("interview_date is required for schedule_interview", 400)
            shortlist.schedule_interview(interview_date)
            if shortlist.student:
                shortlist.student.current_internship_status = "interview_scheduled"

        elif action == "mark_interviewed":
            shortlist.mark_as_interviewed(data.get("interview_notes"))
            if shortlist.student:
                shortlist.student.current_internship_status = "interviewed"

        elif action == "hire":
            shortlist.mark_as_hired()
            if shortlist.student:
                shortlist.student.current_internship_status = "hired"

        elif action == "reject":
            shortlist.mark_as_rejected(data.get("reason"))
            if shortlist.student:
                shortlist.student.current_internship_status = "rejected"

        elif action == "add_note":
            note = data.get("note")
            if not note:
                return _json_error("note is required for add_note", 400)
            shortlist.add_staff_note(str(note), staff.id)

        elif action == "notify_student":
            shortlist.notify_student()

        elif action == "notify_company":
            shortlist.notify_company()

        else:
            if "match_reason" in data:
                shortlist.match_reason = data.get("match_reason")
            if "match_score" in data:
                shortlist.match_score = _parse_float(data.get("match_score"), "match_score")
            if "status" in data:
                shortlist.status = str(data.get("status")).strip()
            if "interview_notes" in data:
                shortlist.interview_notes = data.get("interview_notes")
            if "rejection_reason" in data:
                shortlist.rejection_reason = data.get("rejection_reason")
            if "staff_notes" in data:
                shortlist.staff_notes = data.get("staff_notes")

        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return _json_error(str(e), 400)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update shortlist", 500)

    return jsonify({"message": "Shortlist updated", "shortlist": _shortlist_payload(shortlist)}), 200


@staff_views.delete("/shortlists/<int:shortlist_id>")
@jwt_required()
def api_staff_delete_shortlist(shortlist_id):
    _, err = _require_staff()
    if err:
        return err

    shortlist = db.session.get(Shortlist, shortlist_id)
    if shortlist is None:
        return _json_error("Shortlist not found", 404)

    try:
        db.session.delete(shortlist)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to delete shortlist", 500)

    return jsonify({"message": "Shortlist deleted"}), 200


@staff_views.get("/weekly-reports")
@jwt_required()
def api_staff_weekly_reports():
    _, err = _require_staff()
    if err:
        return err

    query = WeeklyReport.query
    student_id = request.args.get("student_id")
    project_id = request.args.get("project_id")
    status = request.args.get("status")
    reviewed = request.args.get("reviewed")

    try:
        if student_id:
            query = query.filter(WeeklyReport.student_id == _parse_int(student_id, "student_id"))
        if project_id:
            query = query.filter(WeeklyReport.project_id == _parse_int(project_id, "project_id"))
    except ValueError as e:
        return _json_error(str(e), 400)

    if status:
        query = query.filter(WeeklyReport.status == status)

    if reviewed is not None:
        reviewed_bool = _parse_bool(reviewed)
        if reviewed_bool is not None:
            query = query.filter(WeeklyReport.reviewed == reviewed_bool)

    reports = query.order_by(WeeklyReport.submission_date.desc()).all()
    return jsonify({"weekly_reports": [_weekly_report_payload(r) for r in reports]}), 200


@staff_views.patch("/weekly-reports/<int:report_id>/review")
@jwt_required()
def api_staff_review_weekly_report(report_id):
    staff, err = _require_staff()
    if err:
        return err

    report = db.session.get(WeeklyReport, report_id)
    if report is None:
        return _json_error("Weekly report not found", 404)

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "review").strip().lower()
    feedback = data.get("feedback")

    try:
        if action == "approve":
            report.approve_report(staff.id)
        elif action == "needs_revision":
            if not feedback:
                return _json_error("feedback is required when requesting revision", 400)
            report.request_revision(staff.id, feedback)
        else:
            report.add_staff_feedback(staff.id, feedback)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to review weekly report", 500)

    return jsonify({"message": "Weekly report reviewed", "weekly_report": _weekly_report_payload(report)}), 200


@staff_views.get("/meetings")
@jwt_required()
def api_staff_meetings():
    staff, err = _require_staff()
    if err:
        return err

    query = Meeting.query.filter(Meeting.staff_id == staff.id)
    student_id = request.args.get("student_id")
    project_id = request.args.get("project_id")
    status = request.args.get("status")

    try:
        if student_id:
            query = query.filter(Meeting.student_id == _parse_int(student_id, "student_id"))
        if project_id:
            query = query.filter(Meeting.project_id == _parse_int(project_id, "project_id"))
    except ValueError as e:
        return _json_error(str(e), 400)

    if status:
        query = query.filter(Meeting.status == status)

    meetings = query.order_by(Meeting.scheduled_at.desc()).all()
    return jsonify({"meetings": [_meeting_payload(m) for m in meetings]}), 200


@staff_views.post("/meetings")
@jwt_required()
def api_staff_create_meeting():
    staff, err = _require_staff()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    required = ["student_id", "scheduled_at"]
    missing = [k for k in required if data.get(k) in [None, ""]]
    if missing:
        return _json_error("Missing required fields", 400, {"missing": missing})

    try:
        student_id = _parse_int(data.get("student_id"), "student_id")
        project_id = _parse_int(data.get("project_id"), "project_id")
        program_id = _parse_int(data.get("program_id"), "program_id")
        scheduled_at = _parse_datetime(data.get("scheduled_at"), "scheduled_at")
    except ValueError as e:
        return _json_error(str(e), 400)

    student = db.session.get(Student, student_id)
    if student is None:
        return _json_error("Student not found", 404)

    if project_id is not None:
        project = db.session.get(Project, project_id)
        if project is None:
            return _json_error("Project not found", 404)

    try:
        meeting = Meeting(
            student_id=student_id,
            staff_id=staff.id,
            scheduled_at=scheduled_at,
            meeting_type=data.get("meeting_type") or "weekly",
            program_id=program_id,
            project_id=project_id,
            location=data.get("location"),
            meeting_link=data.get("meeting_link"),
            agenda=data.get("agenda"),
            notes=data.get("notes"),
            status=data.get("status") or "scheduled",
        )
        db.session.add(meeting)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to create meeting", 500)

    return jsonify({"message": "Meeting created", "meeting": _meeting_payload(meeting)}), 201


@staff_views.patch("/meetings/<int:meeting_id>")
@jwt_required()
def api_staff_update_meeting(meeting_id):
    staff, err = _require_staff()
    if err:
        return err

    meeting = db.session.get(Meeting, meeting_id)
    if meeting is None:
        return _json_error("Meeting not found", 404)
    if meeting.staff_id != staff.id:
        return _json_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()

    try:
        if action == "complete":
            meeting.mark_completed()
        elif action == "cancel":
            meeting.cancel(data.get("reason"))
        elif action == "add_note":
            note = data.get("note")
            if not note:
                return _json_error("note is required for add_note", 400)
            meeting.add_notes(str(note))
        else:
            if "scheduled_at" in data:
                meeting.scheduled_at = _parse_datetime(data.get("scheduled_at"), "scheduled_at")
            if "meeting_type" in data:
                meeting.meeting_type = str(data.get("meeting_type")).strip()
            if "location" in data:
                meeting.location = data.get("location")
            if "meeting_link" in data:
                meeting.meeting_link = data.get("meeting_link")
            if "agenda" in data:
                meeting.agenda = data.get("agenda")
            if "notes" in data:
                meeting.notes = data.get("notes")
            if "status" in data:
                meeting.status = str(data.get("status")).strip()
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return _json_error(str(e), 400)
    except Exception:
        db.session.rollback()
        return _json_error("Failed to update meeting", 500)

    return jsonify({"message": "Meeting updated", "meeting": _meeting_payload(meeting)}), 200


@staff_views.get("/evaluations")
@jwt_required()
def api_staff_evaluations():
    _, err = _require_staff()
    if err:
        return err

    query = StudentEvaluation.query
    student_id = request.args.get("student_id")
    project_id = request.args.get("project_id")
    company_id = request.args.get("company_id")
    reviewed = request.args.get("reviewed")
    status = request.args.get("status")

    try:
        if student_id:
            query = query.filter(StudentEvaluation.student_id == _parse_int(student_id, "student_id"))
        if project_id:
            query = query.filter(StudentEvaluation.project_id == _parse_int(project_id, "project_id"))
        if company_id:
            query = query.filter(StudentEvaluation.company_id == _parse_int(company_id, "company_id"))
    except ValueError as e:
        return _json_error(str(e), 400)

    if reviewed is not None:
        reviewed_bool = _parse_bool(reviewed)
        if reviewed_bool is not None:
            query = query.filter(StudentEvaluation.reviewed_by_staff == reviewed_bool)

    if status:
        query = query.filter(StudentEvaluation.status == status)

    evaluations = query.order_by(StudentEvaluation.created_at.desc()).all()
    return jsonify({"evaluations": [_evaluation_payload(e) for e in evaluations]}), 200


@staff_views.patch("/evaluations/<int:evaluation_id>/review")
@jwt_required()
def api_staff_review_evaluation(evaluation_id):
    staff, err = _require_staff()
    if err:
        return err

    evaluation = db.session.get(StudentEvaluation, evaluation_id)
    if evaluation is None:
        return _json_error("Evaluation not found", 404)

    data = request.get_json(silent=True) or {}
    notes = data.get("notes")
    finalize = _parse_bool(data.get("finalize"), False)

    try:
        evaluation.add_staff_review(staff.id, notes)
        if finalize:
            evaluation.finalize_evaluation()
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to review evaluation", 500)

    return jsonify({"message": "Evaluation reviewed", "evaluation": _evaluation_payload(evaluation)}), 200


@staff_views.get("/announcements")
@jwt_required()
def api_staff_announcements():
    _, err = _require_staff()
    if err:
        return err

    audience = request.args.get("audience")
    query = Announcement.query
    if audience:
        query = query.filter(Announcement.audience == audience)

    announcements = query.order_by(Announcement.created_at.desc()).all()
    return jsonify({"announcements": [a.get_json() for a in announcements]}), 200


@staff_views.post("/announcements")
@jwt_required()
def api_staff_create_announcement():
    _, err = _require_staff()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    required = ["title", "message"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _json_error("Missing required fields", 400, {"missing": missing})

    try:
        announcement = Announcement(
            title=str(data.get("title")).strip(),
            message=str(data.get("message")).strip(),
            audience=str(data.get("audience") or "all").strip(),
        )
        db.session.add(announcement)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to create announcement", 500)

    return jsonify({"message": "Announcement created", "announcement": announcement.get_json()}), 201


@staff_views.delete("/announcements/<int:announcement_id>")
@jwt_required()
def api_staff_delete_announcement(announcement_id):
    _, err = _require_staff()
    if err:
        return err

    announcement = db.session.get(Announcement, announcement_id)
    if announcement is None:
        return _json_error("Announcement not found", 404)

    try:
        db.session.delete(announcement)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return _json_error("Failed to delete announcement", 500)

    return jsonify({"message": "Announcement deleted"}), 200