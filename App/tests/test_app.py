import os
import pytest
from App.main import create_app
import unittest
import logging
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock, mock_open
from App.database import create_db, db 
from flask import Flask

from App.models import (
    User, Shortlist, Staff, Student, Announcement, 
    Company, CompanyRegistration, Meeting, Notes, Project,
    Student_application, StudentEvaluation, Transcript_summary, 
    WeeklyReport, Email  
)

from App.controllers import (
    register_student, login, get_user, update_user,
    create_project, update_project,
    create_shortlist, schedule_interview, mark_as_hired,
    create_staff, update_staff, get_all_staff,
    create_student, update_student, update_student_internship_status,
    create_application, pdf_checker,
    send_email, render_email_template,
    create_weekly_report, approve_weekly_report
)

from App.controllers.email import send_email, render_email_template, _decode_header_value
from App.controllers.project import create_project, update_project
from App.controllers.shortlist import create_shortlist, schedule_interview, mark_as_hired, mark_as_rejected
from App.controllers.staff import create_staff, update_staff, get_all_staff
from App.controllers.student import create_student, update_student, update_student_internship_status
from App.controllers.student_application import create_application, pdf_checker
from App.controllers.document import DocumentController
from App.controllers.transcript_summary import parse_transcript, Course, Report
from App.controllers.weeklyreport import create_weekly_report, approve_weekly_report
from App.controllers.notification import (
    application_received_notification,
    weeklyReport_received_notification,
    get_announcement_statistics
)
from App.controllers.auth import setup_jwt, _issue_tokens


LOGGER = logging.getLogger(__name__)


class AnnouncementUnitTests(unittest.TestCase):

    def test_new_announcement(self):
        announcement = Announcement(title="New Internship", message="Apply now!", audience="students")
        assert announcement.title == "New Internship"
        assert announcement.message == "Apply now!"
        assert announcement.audience == "students"

    def test_announcement_default_audience(self):
        announcement = Announcement(title="General Update", message="System maintenance tonight.")
        assert announcement.audience == "all"

    def test_announcement_get_json(self):
        announcement = Announcement(title="Title", message="Msg", audience="all")
        announcement.id = 1
        announcement.created_at = datetime(2024, 1, 1, 12, 0, 0)
        announcement.updated_at = datetime(2024, 1, 1, 12, 0, 0)

        json_data = announcement.get_json()
        assert json_data['id'] == 1
        assert json_data['title'] == "Title"
        assert '2024-01-01' in json_data['created_at']


class NotificationControllerUnitTests(unittest.TestCase):

    def test_get_announcement_statistics_empty(self):
        results = []
        stats = get_announcement_statistics(results)
        assert stats['total'] == 0
        assert stats['sent'] == 0

    def test_get_announcement_statistics_success(self):
        results = [
            {'status': 'sent'},
            {'status': 'sent'},
            {'status': 'failed'},
            {'status': 'error'}
        ]
        stats = get_announcement_statistics(results)
        assert stats['total'] == 4
        assert stats['sent'] == 2
        assert stats['failed'] == 1
        assert stats['errors'] == 1


class CompanyUnitTests(unittest.TestCase):

    def test_new_company(self):
        company = Company(
            company_name="TechCorp",
            email="hr@techcorp.com",
            password="securepassword123"
        )
        assert company.company_name == "TechCorp"
        assert company.email == "hr@techcorp.com"
        assert company.password_hash != "securepassword123"

    def test_check_password(self):
        company = Company("TestInc", password="mypassword")
        assert company.check_password("mypassword") is True
        assert company.check_password("wrongpassword") is False

    def test_company_get_json(self):
        company = Company(
            company_name="Innovate",
            website="https://innovate.io",
            category="Software",
            email="info@innovate.io"
        )
        company.id = 101
        json_data = company.get_json()

        assert json_data['id'] == 101
        assert json_data['company_name'] == "Innovate"
        assert json_data['email'] == "info@innovate.io"
        assert 'password_hash' not in json_data


class CompanyRegistrationUnitTests(unittest.TestCase):

    def test_new_registration(self):
        reg = CompanyRegistration(
            company_name="Innovate Ltd",
            website="https://innovate.tt",
            category="Energy"
        )
        assert reg.company_name == "Innovate Ltd"
        assert reg.website == "https://innovate.tt"
        assert reg.category == "Energy"

    def test_registration_get_json(self):
        reg = CompanyRegistration("Tech Solutions", "tech.com", "IT")
        reg.id = 5
        json_data = reg.get_json()

        assert json_data['id'] == 5
        assert json_data['company_name'] == "Tech Solutions"
        assert 'created_at' in json_data


class EmailUnitTests(unittest.TestCase):

    def test_new_email_object(self):
        email = Email(
            sender_id=1,
            recipient_id=2,
            subject="Internship Update",
            description="Your application is under review.",
            graphic="path/to/graphic.png",
            attachment="resume.pdf"
        )
        assert email.sender_id == 1
        assert email.subject == "Internship Update"
        assert email.status is False

    def test_email_get_json(self):
        email = Email(1, 2, "Sub", "Desc", "G", "A")
        data = email.get_json()
        assert data['subject'] == "Sub"
        assert data['description'] == "Desc"
        assert data['sender_id'] == 1


class EmailServiceUtilsTests(unittest.TestCase):

    def test_render_email_template(self):
        template = "Hello {{ first_name }}, welcome to {{ company }}!"
        context = {"first_name": "John", "company": "UWI"}
        result = render_email_template(template, context)
        assert result == "Hello John, welcome to UWI!"

    def test_render_email_template_empty_context(self):
        template = "General Announcement"
        result = render_email_template(template, {})
        assert result == "General Announcement"

    def test_decode_header_value(self):
        assert _decode_header_value("Simple Subject") == "Simple Subject"
        assert _decode_header_value(None) == ""


class EmailSendLogicTests(unittest.TestCase):

    @patch('smtplib.SMTP')
    @patch('App.controllers.email_service._cfg')
    @patch('App.controllers.email_service.smtplib.SMTP')
    def test_send_email_calls_smtp(self, mock_bool, mock_cfg, mock_smtp):
        mock_cfg.side_effect = lambda k, default=None: "test_val" if k != "MAIL_PORT" else 587
        mock_bool.return_value = False

        instance = mock_smtp.return_value

        result = send_email(to_email="test@user.com", subject="Hello", body_text="Test Body")

        assert result["sent"] is True
        assert mock_smtp.called
        instance.login.assert_called()
        instance.send_message.assert_called()


class MeetingProjectNotesTests(unittest.TestCase):

    def test_new_meeting(self):
        scheduled_time = datetime(2026, 5, 20, 14, 30)
        meeting = Meeting(
            student_id=1,
            staff_id=5,
            scheduled_at=scheduled_time,
            meeting_type='initial',
            location='Office 101'
        )
        self.assertEqual(meeting.student_id, 1)
        self.assertEqual(meeting.status, 'scheduled')
        self.assertEqual(meeting.meeting_type, 'initial')

    def test_meeting_notes_and_completion(self):
        meeting = Meeting(1, 5, datetime.utcnow())

        meeting.add_notes("Discussed project milestones.")
        self.assertIn("Discussed project milestones.", meeting.notes)
        self.assertIn("[", meeting.notes)

        meeting.mark_completed()
        self.assertEqual(meeting.status, 'completed')

    def test_meeting_cancel(self):
        meeting = Meeting(1, 5, datetime.utcnow())
        meeting.cancel(reason="Student ill")
        self.assertEqual(meeting.status, 'cancelled')
        self.assertIn("Cancelled: Student ill", meeting.notes)

    def test_new_note_initialization(self):
        note = Notes(
            student_id=1,
            staff_id=2,
            meeting_id=10,
            description="Follow up required for coding tasks."
        )
        self.assertEqual(note.student_id, 1)
        self.assertEqual(note.description, "Follow up required for coding tasks.")
        self.assertIsNone(note.parent_id)

    def test_project_get_json(self):
        project = Project(
            project_name="Web App",
            international_students=True,
            place_of_work=False,
            description="Build a Flask app",
            stipend=1200.0,
            hired_after=True,
            number_of_interns=3,
            details="HTML/CSS/JS",
            covid_vaccination=True,
            company_id=1
        )
        project.id = 99
        data = project.get_json()

        self.assertEqual(data['id'], 99)
        self.assertEqual(data['project_name'], "Web App")
        self.assertEqual(data['stipend'], 1200.0)
        self.assertTrue(data['international_students'])

    def test_create_project_logic(self):
        with patch('App.database.db.session.add') as mock_add:
            with patch('App.database.db.session.commit') as mock_commit:
                project = create_project(
                    company_id=1,
                    project_name="Data Science Intern",
                    number_of_interns=1,
                    stipend=2000.0
                )
                self.assertIsNotNone(project)
                self.assertEqual(project.project_name, "Data Science Intern")

    def test_update_project_constraints(self):
        fake_project = Project("Test", False, False, "Desc", 0, False, 1, "Det", False, company_id=1)

        with patch('App.controllers.project.get_project', return_value=fake_project):
            result = update_project(project_id=1, company_id=2, project_name="Hacked")
            self.assertIsNone(result)
            self.assertNotEqual(fake_project.project_name, "Hacked")


class ShortlistUnitTests(unittest.TestCase):

    def test_new_shortlist(self):
        shortlist = Shortlist(
            staff_id=1,
            student_id=10,
            project_id=100,
            match_reason="Strong Python skills",
            match_score=85.5
        )
        self.assertEqual(shortlist.status, 'shortlisted')
        self.assertEqual(shortlist.match_score, 85.5)
        self.assertFalse(shortlist.interview_scheduled)

    def test_shortlist_status_transitions(self):
        shortlist = Shortlist(1, 10, 100)

        future_date = datetime.utcnow() + timedelta(days=2)
        shortlist.schedule_interview(future_date)
        self.assertEqual(shortlist.status, 'interview_scheduled')
        self.assertTrue(shortlist.interview_scheduled)

        shortlist.mark_as_interviewed(interview_notes="Candidate performed well.")
        self.assertEqual(shortlist.status, 'interviewed')
        self.assertTrue(shortlist.interviewed)
        self.assertEqual(shortlist.interview_notes, "Candidate performed well.")

        shortlist.mark_as_hired()
        self.assertEqual(shortlist.status, 'hired')
        self.assertTrue(shortlist.hired)

    def test_shortlist_rejection(self):
        shortlist = Shortlist(1, 10, 100)
        shortlist.mark_as_rejected(reason="Lacked specific domain knowledge")
        self.assertEqual(shortlist.status, 'rejected')
        self.assertFalse(shortlist.hired)
        self.assertEqual(shortlist.rejection_reason, "Lacked specific domain knowledge")

    def test_shortlist_staff_notes(self):
        shortlist = Shortlist(1, 10, 100)
        shortlist.add_staff_note("Needs background check", staff_id=1)
        self.assertIn("Needs background check", shortlist.staff_notes)
        self.assertIn("Staff 1", shortlist.staff_notes)

    def test_shortlist_get_json(self):
        shortlist = Shortlist(1, 10, 100)
        shortlist.id = 5
        data = shortlist.get_json()
        self.assertEqual(data['id'], 5)
        self.assertEqual(data['student_id'], 10)
        self.assertEqual(data['status'], 'shortlisted')

    @patch('App.controllers.shortlist.db.session.get')
    @patch('App.models.shortlist.Shortlist.query')
    def test_create_shortlist_duplicate_prevention(self, mock_query, mock_get):
        mock_get.return_value = MagicMock()
        mock_query.filter_by.return_value.first.return_value = MagicMock()

        result = create_shortlist(1, 10, 100)

        self.assertIsNone(result)

    @patch('App.controllers.shortlist.get_shortlist')
    @patch('App.database.db.session.commit')
    def test_schedule_interview_date_parsing(self, mock_commit, mock_get_shortlist):
        mock_shortlist = MagicMock()
        mock_get_shortlist.return_value = mock_shortlist

        date_str = "2026-06-01 10:00:00"
        schedule_interview(1, date_str)

        args, _ = mock_shortlist.schedule_interview.call_args
        self.assertIsInstance(args[0], datetime)
        self.assertEqual(args[0].year, 2026)

    @patch('App.controllers.shortlist.get_shortlist')
    @patch('App.controllers.shortlist.db.session.get')
    @patch('App.database.db.session.commit')
    def test_mark_as_hired_updates_student_status(self, mock_commit, mock_get_student, mock_get_shortlist):
        mock_shortlist = MagicMock(student_id=10)
        mock_get_shortlist.return_value = mock_shortlist
        mock_student = MagicMock()
        mock_get_student.return_value = mock_student

        mark_as_hired(1)

        self.assertEqual(mock_student.current_internship_status, 'hired')
        mock_shortlist.mark_as_hired.assert_called_once()


class StaffUnitTests(unittest.TestCase):

    def test_new_staff_initialization(self):
        staff = Staff(
            email="j.doe@uwi.edu",
            password="password123",
            first_name="John",
            last_name="Doe",
            department="Computing"
        )
        self.assertEqual(staff.email, "j.doe@uwi.edu")
        self.assertEqual(staff.full_name, "John Doe")
        self.assertEqual(staff.role, "staff")
        self.assertEqual(staff.__mapper_args__["polymorphic_identity"], "staff")

    def test_staff_id_alias(self):
        staff = Staff("e@mail.com", "pass", "A", "B", "Dept")
        staff.id = 50
        self.assertEqual(staff.staffID, 50)

        staff.staffID = 75
        self.assertEqual(staff.id, 75)

    def test_staff_get_json(self):
        staff = Staff("jane@uwi.edu", "pass", "Jane", "Smith", "Engineering")
        staff.id = 101
        data = staff.get_json()

        self.assertEqual(data['id'], 101)
        self.assertEqual(data['full_name'], "Jane Smith")
        self.assertEqual(data['department'], "Engineering")
        self.assertEqual(data['role'], "staff")

    @patch('App.controllers.staff.get_staff_by_email')
    @patch('App.database.db.session.add')
    @patch('App.database.db.session.commit')
    def test_create_staff_duplicate_logic(self, mock_commit, mock_add, mock_get_email):
        mock_get_email.return_value = MagicMock()

        result = create_staff("exists@uwi.edu", "pass", "John", "Doe", "Math")

        self.assertIsNone(result)
        mock_add.assert_not_called()

    @patch('App.controllers.staff.get_staff')
    @patch('App.database.db.session.commit')
    def test_update_staff_partial_fields(self, mock_commit, mock_get_staff):
        fake_staff = Staff("old@uwi.edu", "pass", "Old", "Name", "OldDept")
        mock_get_staff.return_value = fake_staff

        update_staff(1, last_name="NewName", department="NewDept")

        self.assertEqual(fake_staff.last_name, "NewName")
        self.assertEqual(fake_staff.department, "NewDept")
        self.assertEqual(fake_staff.first_name, "Old")
        mock_commit.assert_called_once()

    @patch('App.controllers.staff.db.session.scalars')
    def test_get_all_staff_logic(self, mock_scalars):
        get_all_staff()
        self.assertTrue(mock_scalars.called)

    def test_delete_staff_not_found(self):
        with patch('App.controllers.staff.get_staff', return_value=None):
            from App.controllers.staff import delete_staff
            result = delete_staff(999)
            self.assertIsNone(result)


class StudentApplicationTests(unittest.TestCase):

    def test_valid_uwi_email(self):
        app = Student_application.__new__(Student_application)
        self.assertEqual(app._validate_uwi_email("test@my.uwi.edu"), "test@my.uwi.edu")
        self.assertEqual(app._validate_uwi_email("staff@uwi.edu"), "staff@uwi.edu")

        with self.assertRaises(ValueError):
            app._validate_uwi_email("test@gmail.com")

    def test_contact_number_validation(self):
        app = Student_application.__new__(Student_application)
        valid_num = "+18687001234"
        self.assertEqual(app._validate_contact_number(valid_num), valid_num)

        with self.assertRaises(Exception):
            app._validate_contact_number("123")

    def test_get_json_structure(self):
        app = Student_application(
            student_id="81600000",
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@my.uwi.edu",
            contact_number="+18686622002",
            covid_19_vaccination=True,
            summer_requirment="Yes",
            program="BSc Computer Science",
            cover_letter="I am very motivated...",
            internship_credits=3,
            citizenship="Trinidadian",
            profile_picture="pic.jpg",
            returning_intern=False,
            year_of_study=2,
            resume="res.pdf",
            transcript="trans.pdf"
        )
        data = app.get_json()
        self.assertEqual(data['first_name'], "Jane")
        self.assertEqual(data['status'], "pending")

    @patch('magic.from_file')
    def test_pdf_checker_logic(self, mock_magic):
        mock_magic.return_value = "application/pdf"
        self.assertFalse(pdf_checker("test.pdf"))

        mock_magic.return_value = "image/jpeg"
        self.assertTrue(pdf_checker("test.jpg"))

    @patch('App.controllers.student_application.db.session.add')
    @patch('App.controllers.student_application.db.session.commit')
    def test_create_application_regex_validation(self, mock_commit, mock_add):
        result = create_application(
            student_id="ABC",
            first_name="John",
            last_name="Doe",
            email="john@my.uwi.edu",
            contact_number="6622002",
            covid_19_vaccination=True,
            summer_requirment="Yes",
            program="IT",
            cover_letter="Hello",
            internship_credits=3,
            citizenship="Local",
            profile_picture="path/to/img.jpg",
            returning_intern=False,
            year_of_study=3,
            resume="path/to/res.pdf",
            transcript="path/to/trans.pdf"
        )
        mock_add.assert_not_called()

    def test_full_name_helper(self):
        app = Student_application.__new__(Student_application)
        app.first_name = "John"
        app.last_name = "Smith"
        self.assertEqual(app.get_full_name(), "John Smith")


class StudentUnitTests(unittest.TestCase):

    def test_student_uwi_email_validation(self):
        s1 = Student("stud@my.uwi.edu", "pass", "John", "Doe", "816000", "BSc CS")
        s2 = Student("prof@sta.uwi.edu", "pass", "Jane", "Doe", "816001", "BSc IT")
        self.assertEqual(s1.email, "stud@my.uwi.edu")

        with self.assertRaises(ValueError):
            Student("hacker@gmail.com", "pass", "Mal", "Ware", "666", "None")

    def test_calculate_age(self):
        student = Student("test@my.uwi.edu", "pass", "A", "B", "1", "CS")
        student.dob = date.today() - timedelta(days=365*20 + 5)
        self.assertEqual(student.calculate_age(), 20)

    def test_upload_constraints(self):
        student = Student("test@my.uwi.edu", "pass", "A", "B", "1", "CS")

        student.upload_resume("my_resume.pdf")
        self.assertEqual(student.resume_path, "my_resume.pdf")

        with self.assertRaises(ValueError):
            student.upload_resume("my_resume.exe")

    def test_can_apply_logic(self):
        student = Student("test@my.uwi.edu", "pass", "A", "B", "1", "CS")
        self.assertFalse(student.can_apply_to_project(None))

        student.upload_resume("r.pdf")
        student.upload_transcript("t.pdf")
        self.assertTrue(student.can_apply_to_project(None))

        student.current_internship_status = 'hired'
        self.assertFalse(student.can_apply_to_project(None))

    @patch('App.controllers.student.db.session.add')
    @patch('App.controllers.student.db.session.commit')
    def test_create_student_controller_parsing(self, mock_commit, mock_add):
        student = create_student(
            "new@my.uwi.edu", "pass", "New", "Student", "816099", "BSc",
            dob="2000-01-01"
        )
        self.assertIsNotNone(student)
        self.assertIsInstance(student.dob, date)
        self.assertEqual(student.dob.year, 2000)

    @patch('App.controllers.student.get_student')
    @patch('App.database.db.session.commit')
    def test_update_internship_status_validation(self, mock_commit, mock_get):
        mock_student = MagicMock()
        mock_get.return_value = mock_student

        result = update_student_internship_status(1, "looking_for_work")
        self.assertIsNone(result)

        result = update_student_internship_status(1, "active")
        self.assertIsNotNone(result)
        self.assertEqual(mock_student.current_internship_status, "active")

    @patch('App.controllers.student.get_student')
    @patch('App.database.db.session.commit')
    def test_partial_update_student(self, mock_commit, mock_get):
        fake_student = Student("old@my.uwi.edu", "pass", "Old", "Old", "1", "Old")
        mock_get.return_value = fake_student

        update_student(1, degree="New Degree", gpa=3.8)

        self.assertEqual(fake_student.degree, "New Degree")
        self.assertEqual(fake_student.gpa, 3.8)
        self.assertEqual(fake_student.first_name, "Old")


class EvaluationAndDocumentTests(unittest.TestCase):

    def test_evaluation_initialization(self):
        eval_obj = StudentEvaluation(
            company_id=1, student_id=2, project_id=3,
            evaluation_form_path="eval.pdf", evaluation_period="midterm"
        )
        self.assertEqual(eval_obj.status, 'submitted')
        self.assertIsNotNone(eval_obj.submitted_at)

        with self.assertRaises(ValueError):
            StudentEvaluation(1, 2, 3, "eval.docx")

    def test_calculate_average_rating(self):
        eval_obj = StudentEvaluation(1, 2, 3, "eval.pdf")

        eval_obj.set_ratings(overall=4.0, technical=5.0)
        self.assertEqual(eval_obj.calculate_average_rating(), 4.5)

        eval_empty = StudentEvaluation(1, 2, 3, "eval.pdf")
        self.assertIsNone(eval_empty.calculate_average_rating())

    def test_staff_review_transition(self):
        eval_obj = StudentEvaluation(1, 2, 3, "eval.pdf")
        eval_obj.add_staff_review(staff_id=10, notes="Great progress.")

        self.assertTrue(eval_obj.reviewed_by_staff)
        self.assertEqual(eval_obj.status, 'reviewed_by_staff')
        self.assertEqual(eval_obj.staff_reviewer_id, 10)

    def test_is_allowed_file(self):
        self.assertTrue(DocumentController.is_allowed_file("test.pdf", {"pdf"}))
        self.assertTrue(DocumentController.is_allowed_file("test.PDF", {"pdf"}))

        self.assertTrue(DocumentController.is_allowed_file("image.png", DocumentController.IMAGE_EXTENSIONS))

        self.assertFalse(DocumentController.is_allowed_file("script.sh", {"pdf", "png"}))
        self.assertFalse(DocumentController.is_allowed_file("no_extension", {"pdf"}))

    def test_build_filename_security(self):
        original = "my resume!.pdf"
        category = "resume"

        with patch('App.controllers.document.datetime') as mock_date:
            mock_date.utcnow.return_value.strftime.return_value = "20260101_120000"
            new_name = DocumentController.build_filename(original, category)

            self.assertEqual(new_name, "resume_20260101_120000_my_resume.pdf")

    @patch('App.controllers.document.os.makedirs')
    @patch('App.controllers.document.current_app')
    def test_ensure_upload_path(self, mock_app, mock_makedirs):
        mock_app.instance_path = "/tmp/instance"
        path = DocumentController.ensure_upload_path(owner_id=5, category="transcripts")

        expected = os.path.join("/tmp/instance", "uploads", "5", "transcripts")
        self.assertEqual(path, expected)
        mock_makedirs.assert_called_with(expected, exist_ok=True)

    @patch('App.controllers.document.DocumentController.save_document')
    def test_save_student_resume_wrapper(self, mock_save):
        mock_file = MagicMock()
        DocumentController.save_student_resume(mock_file, student_id=99)

        mock_save.assert_called_once()
        args, kwargs = mock_save.call_args
        self.assertEqual(kwargs['category'], "resume")
        self.assertEqual(kwargs['owner_id'], 99)


class TranscriptTests(unittest.TestCase):

    def test_transcript_summary_json(self):
        summary = Transcript_summary(student_id=1, application_id=101, report="Pass")
        json_data = summary.get_json()

        self.assertEqual(json_data['student_id'], 1)
        self.assertEqual(json_data['report'], "Pass")

    def test_course_processing_logic(self):
        from App.controllers.transcript import process_course_line

        words = "COMP 2611 Data Structures A" 
        course = process_course_line(words)

        self.assertEqual(course['subject'], "COMP")
        self.assertEqual(course.code, "2611")
        self.assertEqual(course.grade, "A")
        self.assertIn("Data Structures", course.title)

    def test_grade_extraction_edge_cases(self):
        from App.controllers.transcript import extract_grade

        grade, remaining = extract_grade("0.003.00A+SomeText")
        self.assertEqual(grade, "A+")

        grade, remaining = extract_grade("Z-")
        self.assertIsNone(grade)

    @patch('App.controllers.transcript_summary.PdfReader')
    @patch('builtins.open', new_callable=mock_open, read_data=b"dummy pdf data")
    def test_parse_transcript_flow(self, mock_file, mock_reader):
        # Mocking the reader pages
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Record of: John Doe\nStudent Number: 816000123\nSubject Course Title Grade Duration\nCOMP 1601 Computer Programming A UGS"
        mock_reader.return_value.pages = [mock_page]

        report = parse_transcript("dummy.pdf") 
        self.assertEqual(report.student_name, "John Doe")
        self.assertEqual(report.student_id, "816000123")
        self.assertTrue(len(report.courses) > 0)
        self.assertEqual(report.courses[0].subject, "COMP")

    def test_edit_transcript_report_logic(self):
        existing_report = MagicMock()
        existing_report.student_name = "Original Name"
        existing_report.courses = [Course(subject="MATH", code="1111")]

        new_data = MagicMock()
        new_data.new_name = "Updated Name"
        new_data.courses = [Course(subject="STAT", code="1111")]

        with patch('App.controllers.transcript.__get_transcript_by_id', return_value=existing_report):
            from App.controllers.transcript import edit_transcript_report
            updated = edit_transcript_report(1, new_data)

            self.assertEqual(updated.student_name, "Updated Name")
            self.assertEqual(updated.courses[0].subject, "STAT")


class WeeklyReportTests(unittest.TestCase):

    def test_weekly_report_initialization(self):
        report = WeeklyReport(
            student_id=1, project_id=2, week_number=1,
            report_file_path="week1_report.pdf"
        )
        self.assertEqual(report.status, 'submitted')
        self.assertFalse(report.is_late)

        with self.assertRaises(ValueError):
            WeeklyReport(1, 2, 1, "week1_report.docx")

    def test_late_submission_logic(self):
        past_due_date = datetime.utcnow() - timedelta(days=2)

        report = WeeklyReport(
            student_id=1, project_id=2, week_number=1,
            report_file_path="report.pdf", due_date=past_due_date
        )
        self.assertTrue(report.is_late)

    def test_status_transitions(self):
        report = WeeklyReport(1, 2, 1, "report.pdf")

        report.request_revision(staff_id=10, feedback="Please add more details.")
        self.assertTrue(report.reviewed)
        self.assertEqual(report.status, 'needs_revision')
        self.assertEqual(report.reviewed_by, 10)
        self.assertEqual(report.staff_feedback, "Please add more details.")

        report.approve_report(staff_id=11)
        self.assertEqual(report.status, 'approved')
        self.assertEqual(report.reviewed_by, 11)

    @patch('App.controllers.weeklyreport.db.session')
    @patch('App.controllers.weeklyreport.Shortlist')
    @patch('App.controllers.weeklyreport.WeeklyReport')
    def test_create_weekly_report_success(self, MockWeeklyReport, MockShortlist, mock_session):
        mock_student = MagicMock()
        mock_student.current_internship_status = 'hired'
        mock_project = MagicMock()

        mock_session.get.side_effect = [mock_student, mock_project]

        mock_shortlist_query = MagicMock()
        mock_shortlist_query.first.return_value = MagicMock()
        MockShortlist.query.filter_by.return_value = mock_shortlist_query

        mock_report_query = MagicMock()
        mock_report_query.first.return_value = None
        MockWeeklyReport.query.filter_by.return_value = mock_report_query

        mock_new_report = MagicMock()
        MockWeeklyReport.return_value = mock_new_report

        result = create_weekly_report(
            student_id=1, project_id=2, week_number=3, report_file_path="report.pdf"
        )

        self.assertIsNotNone(result)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('App.controllers.weeklyreport.db.session')
    def test_create_weekly_report_not_hired(self, mock_session):
        mock_student = MagicMock()
        mock_student.current_internship_status = 'pending'
        mock_project = MagicMock()

        mock_session.get.side_effect = [mock_student, mock_project]

        result = create_weekly_report(
            student_id=1, project_id=2, week_number=1, report_file_path="report.pdf"
        )

        self.assertIsNone(result)
        mock_session.add.assert_not_called()

    @patch('App.controllers.weeklyreport.db.session')
    @patch('App.controllers.weeklyreport.get_weekly_report')
    def test_approve_weekly_report(self, mock_get_report, mock_session):
        mock_report = MagicMock()
        mock_staff = MagicMock()

        mock_get_report.return_value = mock_report
        mock_session.get.return_value = mock_staff

        result = approve_weekly_report(report_id=5, staff_id=10)

        mock_report.approve_report.assert_called_once_with(10)
        mock_session.commit.assert_called_once()
        self.assertEqual(result, mock_report)


class NotificationTests(unittest.TestCase):

    @patch('App.controllers.notification.email_controller.send_templated_email')
    def test_application_received_params(self, mock_send_email):
        mock_app = MagicMock()
        mock_app.get_full_name.return_value = "Jane Doe"
        mock_app.student.email = "jane@example.com"

        application_received_notification(mock_app)

        args, kwargs = mock_send_email.call_args
        self.assertEqual(args[0], "jane@example.com")
        self.assertEqual(args[1], "Internship Application Received")
        self.assertIn("Dear Jane Doe", args[2])

    @patch('App.controllers.notification.email_controller.send_templated_email')
    def test_weekly_report_received_params(self, mock_send_email):
        mock_student = MagicMock()
        mock_student.first_name = "Bob"
        mock_student.last_name = "Smith"
        mock_student.email = "bob@example.com"

        weeklyReport_received_notification(mock_student)

        args, _ = mock_send_email.call_args
        self.assertEqual(args[0], "bob@example.com")
        self.assertIn("Dear Bob Smith", args[2])

    @patch('App.controllers.notification.email_controller.send_templated_email')
    def test_notification_error_handling(self, mock_send_email):
        mock_send_email.side_effect = Exception("SMTP Timeout")
        mock_student = MagicMock(email="test@test.com", first_name="A", last_name="B")

        try:
            weeklyReport_received_notification(mock_student)
        except Exception as e:
            self.fail(f"Notification function raised {e} instead of catching it")


class AuthUnitTests(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['JWT_SECRET_KEY'] = 'test-secret'
        self.jwt = setup_jwt(self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('App.models.User.query')
    def test_user_lookup_loader_student(self, mock_user_query):
        mock_user = MagicMock(id=1, role='student')
        mock_user_query.filter_by.return_value.first.return_value = mock_user

        loader = self.app.extensions['flask-jwt-extended']._user_lookup_callback
        result = loader(None, {"sub": "1"})

        self.assertEqual(result.id, 1)
        mock_user_query.filter_by.assert_called_with(id=1)

    @patch('App.models.company.Company.query')
    def test_user_lookup_loader_company(self, mock_company_query):
        mock_company = MagicMock(id=5)
        mock_company_query.get.return_value = mock_company

        loader = self.app.extensions['flask-jwt-extended']._user_lookup_callback
        result = loader(None, {"sub": "company:5"})

        self.assertEqual(result.id, 5)
        mock_company_query.get.assert_called_with(5)

    def test_issue_tokens(self):
        mock_user = MagicMock(id=10, role='staff')

        with self.app.app_context(): 
            access, refresh = _issue_tokens(mock_user)
            self.assertIsNotNone(access)


class UserUnitTests(unittest.TestCase):

    def test_password_hashing(self):
        user = User(email="test@example.com", password="securepassword123", role="user")

        self.assertNotEqual(user.password, "securepassword123")

        self.assertTrue(user.check_password("securepassword123"))
        self.assertFalse(user.check_password("wrongpassword"))

    def test_user_json_serialization(self):
        user = User(email="dev@app.com", password="password", role="admin")
        user.id = 1

        json_data = user.get_json()

        self.assertEqual(json_data['id'], 1)
        self.assertEqual(json_data['email'], "dev@app.com")
        self.assertEqual(json_data['role'], "admin")
        self.assertEqual(json_data['is_active'], True)
        self.assertIn('created_at', json_data)

    def test_default_permissions(self):
        user = User(email="guest@app.com", password="password", role="user")

        self.assertFalse(user.can_shortlist_application(None))
        self.assertFalse(user.can_create_project())
        self.assertFalse(user.can_accept_application(None))
        self.assertFalse(user.can_match_student_to_project())

    def test_update_last_login(self):
        user = User(email="login@test.com", password="password", role="user")
        self.assertIsNone(user.last_login)

        with unittest.mock.patch('App.database.db.session.commit', MagicMock()):
            user.update_last_login()
            self.assertIsNotNone(user.last_login)
            self.assertIsInstance(user.last_login, datetime)

    def test_repr_output(self):
        user = User(email="test@test.com", password="password", role="user")
        user.id = 99
        self.assertEqual(str(user), "<User 99: test@test.com>")


if __name__ == '__main__':
    unittest.main()
'''
    Integration Tests
'''


@pytest.fixture(autouse=True, scope="function")
def empty_db():
    
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    
    with app.app_context():
        db.create_all() 
        yield app.test_client()
        db.session.remove()
        db.drop_all()

'''
class UserIntegrationTests(unittest.TestCase):

    def test_create_user(self):
        
        staff = create_user("rick", "bobpass", "staff")
        assert staff.username == "rick" 

        employer = create_user("sam", "sampass", "employer")
        assert employer.username == "sam"

        student = create_user("hannah", "hannahpass", "student")
        assert student.username == "hannah"

   # def test_get_all_users_json(self):
     #   users_json = get_all_users_json()
      #  self.assertListEqual([{"id":1, "username":"bob"}, {"id":2, "username":"rick"}], users_json)

    # Tests data changes in the database
    #def test_update_user(self):
      #  update_user(1, "ronnie")
      #  user = get_user(1)
       # assert user.username == "ronnie"
        
    def test_open_position(self):
        position_count = 2
        employer = create_user("sally", "sallypass", "employer")
        assert employer is not None
        position = open_position("IT Support", employer.id, position_count)
        positions = get_positions_by_employer(employer.id)
        assert position is not None
        assert position.number_of_positions == position_count
        assert len(positions) > 0
        assert any(p.id == position.id for p in positions)
        
        invalid_position = open_position("Developer",-1,1)
        assert invalid_position is False


    def test_add_to_shortlist(self):
        position_count = 3
        staff = create_user("linda", "lindapass", "staff")
        assert staff is not None
        student = create_user("hank", "hankpass", "student")
        assert student is not None
        employer =  create_user("ken", "kenpass", "employer")
        assert employer is not None
        position = open_position("Database Manager", employer.id, position_count)
        invalid_position = open_position("Developer",-1,1)
        assert invalid_position is False
        added_shortlist = add_student_to_shortlist(student.id, position.id ,staff.id)
        assert position is not None
        assert (added_shortlist)
        shortlists = get_shortlist_by_student(student.id)
        assert any(s.id == added_shortlist.id for s in shortlists)


    def test_decide_shortlist(self):
        position_count = 3
        student = create_user("jack", "jackpass", "student")
        assert student is not None
        staff = create_user ("pat", "patpass", "staff")
        assert staff is not None
        employer =  create_user("frank", "pass", "employer")
        assert employer is not None
        position = open_position("Intern", employer.id, position_count)
        assert position is not None
        stud_shortlist = add_student_to_shortlist(student.id, position.id ,staff.id)
        assert (stud_shortlist)
        decided_shortlist = decide_shortlist(student.id, position.id, "accepted")
        assert (decided_shortlist)
        shortlists = get_shortlist_by_student(student.id)
        assert any(s.status == PositionStatus.accepted for s in shortlists)
        assert position.number_of_positions == (position_count-1)
        assert len(shortlists) > 0
        invalid_decision = decide_shortlist(-1, -1, "accepted")
        assert invalid_decision is False


    def test_student_view_shortlist(self):

        student = create_user("john", "johnpass", "student")
        assert student is not None
        staff = create_user ("tim", "timpass", "staff")
        assert staff is not None
        employer =  create_user("joe", "joepass", "employer")
        assert employer is not None
        position = open_position("Software Intern", employer.id, 4)
        assert position is not None
        shortlist = add_student_to_shortlist(student.id, position.id ,staff.id)
        shortlists = get_shortlist_by_student(student.id)
        assert any(shortlist.id == s.id for s in shortlists)
        assert len(shortlists) > 0
'''
    # Tests data changes in the database
    #def test_update_user(self):
    #    update_user(1, "ronnie")
    #   user = get_user(1)
    #   assert user.username == "ronnie"

