import pytest
from sqlalchemy.exc import IntegrityError
from App.database import db
from App.database import create_db
from flask import Flask
from datetime import datetime,timedelta
from wsgi import app as flask_app
from App.models import (
    User, Shortlist, Staff, Student, Announcement, 
    Company, CompanyRegistration, Meeting, Notes, Project,
    Student_application, StudentEvaluation, Transcript_summary, 
    WeeklyReport, Email,Program  
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
from App.controllers.notification import (application_received_notification,weeklyReport_received_notification,get_announcement_statistics)
from App.controllers.auth import setup_jwt, _issue_tokens



class TestIntegration:

    @pytest.fixture(autouse=True)
    def setup_database(self):
        flask_app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
        })
        with flask_app.app_context():
            db.create_all()
            yield
            db.session.remove()
            db.drop_all()

    def test_program(self):
        program = Program(
            name = "comp 2604",
            description ="Focuses on software engineering and theory"
        )

        db.session.add(program)
        db.session.commit()

        retrieved = Program.query.filter_by(id=program.id).first()
        assert retrieved is not None
        assert retrieved.name == "comp 2604"
        assert retrieved.description == "Focuses on software engineering and theory"


    def test_student_creation(self):
        student = Student(
            email="816000001@my.uwi.edu",
            password="password123",
            first_name="Ravi",
            last_name="Maharaj",
            student_id="816000001",
            degree="BSc Computer Science"
        )
        db.session.add(student)
        db.session.commit()

        retrieved = Student.query.filter_by(student_id="816000001").first()
        assert retrieved != None
        assert retrieved.full_name == "Ravi Maharaj"
        assert retrieved.email == "816000001@my.uwi.edu"

    def test_Student_controller_creation(self):
        student = create_student(
            email="816000001@my.uwi.edu",
            password="password123",
            first_name="Ravi",
            last_name="Maharaj",
            student_id="816000001",
            degree="BSc Computer Science"
        )
        db.session.add(student)
        db.session.commit()

        retrieved = Student.query.filter_by(student_id="816000001").first()
        assert retrieved != None
        assert retrieved.full_name =="Ravi Maharaj"
        assert retrieved.email =="816000001@my.uwi.edu"

    def test_duplicate_student_fail(self):
        student1 = Student(
            email="816000001@my.uwi.edu",
            password="password123",
            first_name="Ravi",
            last_name="Maharaj",
            student_id="816000001",
            degree="BSc Computer Science"
        )
        db.session.add(student1)
        db.session.commit()

        student2 = Student(
            email="816000001@my.uwi.edu", 
            password="password456",
            first_name="dup",
            last_name="man",
            student_id="816000001",      
            degree="BSc Computer Science"
        )
        
        db.session.add(student2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
            
        db.session.rollback()

    def test_staff_creation(self):
        new_staff = Staff(
            email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        db.session.add(new_staff)
        db.session.commit()
        
        retrieved = Staff.query.filter_by(staff_id=new_staff.staff_id).first()
        assert retrieved.full_name =="jane doe"
        assert retrieved.role == "staff"
        assert retrieved.get_json()['department'] =="dcit"

    def test_staff_controller_creation(self):
        new_staff = create_staff(
            email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        db.session.add(new_staff)
        db.session.commit()
        
        retrieved = Staff.query.filter_by(staff_id=new_staff.staff_id).first()
        assert retrieved.full_name =="jane doe"
        assert retrieved.role == "staff"
        assert retrieved.get_json()['department'] =="dcit"

    def test_staff_controller_handles_duplicate(self):
        create_staff(
            email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        db.session.commit()
        result =  create_staff(
            email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        if result is None:
            db.session.rollback() 

        assert result is None


    def test_company_regisration(self):
        software_registration=CompanyRegistration(
            company_name="software",
            website="https://software.com",
            category="ai"
        )

        db.session.add(software_registration)
        db.session.commit()

        retrieved = CompanyRegistration.query.get(software_registration.id)
        assert retrieved is not None
        assert retrieved.company_name == "software"
        assert retrieved.website == "https://software.com"
        assert retrieved.category == "ai"

    def test_company_creation(self):
        company = Company(
             company_name = "software", 
             website="https://software.com", 
             category="ai", 
             email="software@company.com",
             password=None
        )

        db.session.add(company)
        db.session.commit()

        retrieved =Company.query.get(company.id)
        assert retrieved is not None
        assert retrieved.company_name == "software"
        assert retrieved.website == "https://software.com"
        assert retrieved.category == "ai"
        assert retrieved.email == "software@company.com"

    def test_project_creation(self):
        company = Company(
             company_name = "software", 
             website="https://software.com", 
             category="ai", 
             email="software@company.com",
             password=None
        )

        db.session.add(company)
        db.session.commit()

        project = Project(project_name="IT intern",international_students=True,place_of_work=True,description="An automated system for universities to manage student internship placements, academic eligibility vetting, and industry-partner communication in one centralized platform.",stipend = 5200,hired_after= False,number_of_interns = 1,details = "must be good",covid_vaccination = True,company_id = company.id,registration_id=None)

        db.session.add(project)
        db.session.commit()

        retrieved =Project.query.get(project.id)
        assert retrieved is not None
        assert retrieved.project_name == "IT intern"
        assert retrieved.international_students == True
        assert retrieved.place_of_work==True
        assert retrieved.description=="An automated system for universities to manage student internship placements, academic eligibility vetting, and industry-partner communication in one centralized platform."
        assert retrieved.stipend == 5200
        assert retrieved.hired_after== False
        assert retrieved.number_of_interns == 1
        assert retrieved.details == "must be good"
        assert retrieved.covid_vaccination == True
        assert retrieved.company_id == company.id
        assert retrieved.registration_id==None

    def test_project_with_invalid_company(self):
        invalid_company_id=446
        project = Project(project_name="IT intern",international_students=True,place_of_work=True,description="An automated system for universities to manage student internship placements, academic eligibility vetting, and industry-partner communication in one centralized platform.",stipend = 5200,hired_after= False,number_of_interns = 1,details = "must be good",covid_vaccination = True,company_id = invalid_company_id,registration_id=None)

        db.session.add(project)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback() 

       
    def test_meeting_creation(self):
            staff =Staff(
            email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
            student = Student("816000001@my.uwi.edu", "pass", "ravi", "maharaj", "816000001", "CS")
            db.session.add_all([staff, student])
            db.session.commit()

            meeting_time = datetime.utcnow() + timedelta(days=1)
            meeting = Meeting(
                student_id=student.id,
                staff_id=staff.staff_id,
                scheduled_at=meeting_time,
                meeting_type='weekly',
                location="Virtual",
                agenda="Discuss internship progress"
            )
            db.session.add(meeting)
            db.session.commit()

            retrieved = Meeting.query.get(meeting.id)
            assert retrieved is not None
            assert retrieved.staff.email == "staff@sta.uwi.edu"
            assert retrieved.student.student_id == "816000001"
            assert len(staff.meetings) == 1
            assert len(student.meetings) == 1


    def test_notes(self):
        staff = Staff(email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        student = Student("816000001@my.uwi.edu", "pass", "ravi", "maharaj", "816000001", "CS")
          
        db.session.add_all([staff,student])
        db.session.commit()

        meeting_time = datetime.utcnow() + timedelta(days=1)
        meeting = Meeting(
                student_id=student.student_id,
                staff_id=staff.staff_id,
                scheduled_at=meeting_time,
                meeting_type='weekly',
                location="Virtual",
                agenda="Discuss internship progress"
            )
        db.session.add(meeting)
        db.session.commit()

        note = Notes(
            student_id = student.student_id,
            staff_id=staff.staff_id,
            meeting_id=meeting.id,
            description = "When you finally move from these integration tests to a real production environment, always check your email controllers first.",
            parent_id=None
        )

        db.session.add(note)
        db.session.commit()

        retrieved = Notes.query.get(note.note_id)
        assert retrieved is not None
        assert retrieved.student_id == int(student.student_id)#student_id is str, note student id is int
        assert retrieved.staff_id==staff.staff_id
        assert retrieved.meeting_id==meeting.id
        assert retrieved.description == "When you finally move from these integration tests to a real production environment, always check your email controllers first."
        assert retrieved.parent_id==None

    def test_announcement(self):
        announcement = Announcement(
            title = "no meeting",
            message = " there will be no meetign this week",
            audience = "all")

        db.session.add(announcement)
        db.session.commit()

        retrieved = Announcement.query.get(announcement.id)
        assert retrieved is not None
        assert retrieved.title == "no meeting"
        assert retrieved.message == " there will be no meetign this week"
        assert retrieved.audience ==  "all"

    def test_email_student_to_staff(self):
        staff = Staff(email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        student = Student("816000001@my.uwi.edu", "pass", "ravi", "maharaj", "816000001", "CS")  
        db.session.add_all([staff,student])
        db.session.commit()
        
        email_student_to_staff = Email(
            sender_id=student.id,
            recipient_id=staff.id,
            subject = " project update",
            description = "completed models",
            graphic= None,
            attachment= None
        )

        db.session.add(email_student_to_staff)
        db.session.commit()


        retrieved = Email.query.get(email_student_to_staff.email_id)
        assert retrieved is not None
        assert retrieved.sender_id==student.id
        assert retrieved.recipient_id==staff.id
        assert retrieved.subject == " project update"
        assert retrieved.description == "completed models"
        assert retrieved.graphic== None
        assert retrieved.attachment== None

    def test_email_staff_to_company(self):
       
        staff = Staff(email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        company = Company(company_name = "software", website="https://softwarecom", category="ai", email="software@company.com",password=None)   
        db.session.add_all([staff,company])
        db.session.commit()
        email_staff_to_company = Email(
            sender_id=staff.id,
            recipient_id=company.id,
            subject = "project error",
            description = "wrong system requiremnets",
            graphic= None,
            attachment= None
        )
        db.session.add(email_staff_to_company)
        db.session.commit()

        retrieved = Email.query.get(email_staff_to_company.email_id)
        assert retrieved is not None
        assert retrieved.sender_id==staff.id
        assert retrieved.recipient_id==company.id
        assert retrieved.subject == "project error"
        assert retrieved.description == "wrong system requiremnets"
        assert retrieved.graphic== None
        assert retrieved.attachment== None

    def test_student_to_staff_to_company_email_workflow(self):
        student = Student("816000001@my.uwi.edu", "pass", "ravi", "maharaj", "816000001", "CS")  
        staff = Staff(email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        company = Company(company_name="wayne Ent", email="notbatman@wayne.com")
        db.session.add_all([student, staff, company])
        db.session.commit()

        student_email = Email(
            sender_id=student.id,
            recipient_id=staff.id,
            subject="project access blocker",
            description="i lack access to the production database.",
            graphic=None,
            attachment=None
        )
        db.session.add(student_email)
        db.session.commit()

        staff_email = Email(
            sender_id=staff.id,
            recipient_id=company.id,
            subject="problem intern lacks access",
            description="Please grant Bruce access to the DB.",
            graphic=None,
            attachment=None
        )
        
        db.session.add(staff_email)
        db.session.commit()
        assert Email.query.filter_by(sender_id=student.id).count()== 1
        assert Email.query.filter_by(recipient_id=staff.id).count()== 1
        assert Email.query.filter_by(recipient_id=company.id).count()== 1
        retrieved_staff_email = Email.query.filter_by(sender_id=staff.id).first()
        assert retrieved_staff_email.subject == "problem intern lacks access"


    def test_shortlist(self):
        staff = Staff(email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        student = Student("816000001@my.uwi.edu", "pass", "ravi", "maharaj", "816000001", "CS")  
        company = Company(company_name = "software", website="ttls://softwarecom", category="ai", email="software@company.com",password=None) 
        db.session.add_all([staff,student,company])
        db.session.commit()
        project = Project(project_name="IT intern",international_students=True,place_of_work=True,description="ffo difff feo'nfe enf'fef foijwejjf isdfjjdsf",stipend = 5200,hired_after= False,number_of_interns = 1,details = "eff ff[of fomfsd] ofnsif nfeofnen ijfjjfd ifjsfj ijp- oononnoe",covid_vaccination = True,company_id = company.id,registration_id=None)

        db.session.add(project)
        db.session.commit()

        shortlist=Shortlist(
            staff_id = staff.staff_id,
            student_id=student.student_id, 
            project_id=project.id,
            match_reason="good grades",
            match_score=None
        )

        db.session.add(shortlist)
        db.session.commit()

        retrieved = Shortlist.query.get(shortlist.id)
        assert retrieved is not None
        assert retrieved.staff_id == staff.staff_id
        assert retrieved.student_id==int(student.student_id)
        assert retrieved.project_id==project.id
        assert retrieved.match_reason=="good grades"
        assert retrieved.match_score==None

    def test_shortlist_rejection_workflow(self):
        staff = Staff(email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        student = Student("816000001@my.uwi.edu", "pass", "ravi", "maharaj", "816000001", "CS")  
        company = Company(company_name = "software", website="ttls://softwarecom", category="ai", email="software@company.com",password=None) 
        db.session.add_all([company, staff, student])
        db.session.commit()

        project = Project(project_name="IT intern",international_students=True,place_of_work=True,description="An automated system for universities to manage student internship placements, academic eligibility vetting, and industry-partner communication in one centralized platform.",stipend = 5200,hired_after= False,number_of_interns = 1,details = "must be good",covid_vaccination = True,company_id = company.id,registration_id=None)
        db.session.add(project)
        db.session.commit()

        shortlist = Shortlist(staff_id=staff.staff_id, student_id=student.student_id, project_id=project.id)
        db.session.add(shortlist)
        db.session.commit()

        shortlist.schedule_interview(datetime.utcnow() + timedelta(days=2))
        db.session.commit()

        shortlist.mark_as_rejected(reason="Lacked required framework experience.")
        db.session.commit()


        final_shortlist = Shortlist.query.get(shortlist.id)
        assert final_shortlist.status == 'rejected'
        assert final_shortlist.hired is False
        assert final_shortlist.rejection_reason == "Lacked required framework experience."


    def test_company_scheduling_interview(self):
        staff = Staff(email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        student = Student("816000001@my.uwi.edu", "pass", "ravi", "maharaj", "816000001", "CS")  
        company = Company(company_name = "software", website="ttls://softwarecom", category="ai", email="software@company.com",password=None)
        db.session.add_all([staff,company, student])
        db.session.commit()

        project = Project(project_name="IT intern",international_students=True,place_of_work=True,description="An automated system for universities to manage student internship placements, academic eligibility vetting, and industry-partner communication in one centralized platform.",stipend = 5200,hired_after= False,number_of_interns = 1,details = "must be good",covid_vaccination = True,company_id = company.id,registration_id=None)
        db.session.add(project)
        db.session.commit()
        shortlist =Shortlist(staff.staff_id, student.student_id, project.id, match_reason=None, match_score=None)
        db.session.add(shortlist)
        db.session.commit()
        interview_date= datetime.utcnow() + timedelta(days=1)
        shortlist.schedule_interview(interview_date)

        retrieved = Shortlist.query.get(shortlist.id)
        assert retrieved.interview_date == interview_date
        assert retrieved.interview_scheduled== True

    def test_staff_notes(self):
        staff = Staff(email="staff@sta.uwi.edu",
            password="pass",
            first_name="jane",
            last_name="doe",
            department="dcit"
        )
        student = Student("816000001@my.uwi.edu", "pass", "ravi", "maharaj", "816000001", "CS")  
        company = Company(company_name = "software", website="ttls://softwarecom", category="ai", email="software@company.com",password=None)
 
        db.session.add_all([staff,company, student])
        db.session.commit()

        project = Project(project_name="IT intern",international_students=True,place_of_work=True,description="An automated system for universities to manage student internship placements, academic eligibility vetting, and industry-partner communication in one centralized platform.",stipend = 5200,hired_after= False,number_of_interns = 1,details = "must be good",covid_vaccination = True,company_id = company.id,registration_id=None)    
        db.session.add(project)
        db.session.commit()

        shortlist =Shortlist(staff.staff_id,student.student_id, project.id, match_reason=None, match_score=None)
        db.session.add(shortlist)
        db.session.commit()

        shortlist.add_staff_note("s", staff.staff_id)
        assert "s" in shortlist.staff_notes #adds on to time stamp to note
        assert f"Staff {staff.staff_id}" in shortlist.staff_notes


    def test_company_interview_notes(self):
        company = Company(company_name = "software", website="ttls://softwarecom", category="ai", email="software@company.com",password=None)   
        staff = Staff("alicia@sta.uwi.edu", "pass", "Alicia", "Baptiste", "DCIT")
        student = Student("816000001@my.uwi.edu", "pass", "Ravi", "M", "816000001", "CS")
        db.session.add_all([staff,company, student])
        db.session.commit()

        project = Project(project_name="IT intern",international_students=True,place_of_work=True,description="ffo difff feo'nfe enf'fef foijwejjf isdfjjdsf",stipend = 5200,hired_after= False,number_of_interns = 1,details = "eff ff[of fomfsd] ofnsif nfeofnen ijfjjfd ifjsfj ijp- oononnoe",covid_vaccination = True,company_id = company.id,registration_id=None)
        db.session.add(project)
        db.session.commit()

        shortlist =Shortlist(staff.staff_id, student.student_id, project.id, match_reason=None, match_score=None)
        db.session.add(shortlist)
        db.session.commit()

        interview_notes = "ingerg nriegig gonrgnoi ingrno no gnio nifefq0n nine iienetn inonew "

        shortlist.mark_as_interviewed(interview_notes)
        shortlist.mark_as_hired()

        assert shortlist.interview_notes == interview_notes
        assert shortlist.hired == True

    def test_meeting_completed(self):
        staff = Staff("coord@sta.uwi.edu", "pass", "Alicia", "Baptiste", "DCIT")
        student = Student("816000001@my.uwi.edu", "pass", "Ravi", "M", "816000001", "CS")
        db.session.add_all([staff, student])
        db.session.commit()

        # Create the meeting
        meeting_time = datetime.utcnow() + timedelta(days=1)
        meeting = Meeting(
                student_id=student.id,
                staff_id=staff.staff_id,
                scheduled_at=meeting_time,
                meeting_type='weekly',
                location="Virtual",
                agenda="Discuss internship progress"
            )
        db.session.add(meeting)
        db.session.commit()

        meeting.mark_completed()
        assert meeting.status == 'completed'
    
    def test_meeting_cancel(self):
        staff = Staff("coord@sta.uwi.edu", "pass", "Alicia", "Baptiste", "DCIT")
        student = Student("816000001@my.uwi.edu", "pass", "Ravi", "M", "816000001", "CS")
        db.session.add_all([staff, student])
        db.session.commit()

        meeting_time = datetime.utcnow() + timedelta(days=1)
        meeting = Meeting(
                student_id=student.id,
                staff_id=staff.staff_id,
                scheduled_at=meeting_time,
                meeting_type='weekly',
                location="Virtual",
                agenda="discuss internship progress"
            )
        db.session.add(meeting)
        db.session.commit()

        meeting.cancel()
        assert meeting.status == 'cancelled'

    def test_company_update_project(self):
        staff = Staff("alicia@sta.uwi.edu", "pass", "Alicia", "Baptiste", "DCIT")
        company = Company(company_name = "software", website="ttls://softwarecom", category="ai", email="software@company.com",password=None)   
        project = Project(project_name="IT intern",international_students=True,place_of_work=True,description="ffo difff feo'nfe enf'fef foijwejjf isdfjjdsf",stipend = 5200,hired_after= False,number_of_interns = 1,details = "eff ff[of fomfsd] ofnsif nfeofnen ijfjjfd ifjsfj ijp- oononnoe",covid_vaccination = True,company_id = company.id,registration_id=None)
        db.session.add_all([staff,company,project])
        db.session.commit()

        project.update_project(
            project.id,
            company_id=None,
            project_name="cs intern",
            number_of_interns=None,
            description=None,
            details=None,
            stipend=None,
            place_of_work=None,
            international_students=None,
            hired_after=None,
            covid_vaccination=None,
            registration_id=None)
        assert project.project_name == "cs intern"

    def test_staff_schedule_meeting_logic(self):
        staff = Staff("alicia@sta.uwi.edu", "pass", "Alicia", "Baptiste", "DCIT")
        student = Student("816000001@my.uwi.edu", "pass", "Ravi", "M", "816000001", "CS")
        db.session.add_all([staff, student])
        db.session.commit()

        new_meeting = Meeting(
            student_id=student.id,
            staff_id=staff.staff_id,
            scheduled_at=datetime(2026,5,20,14,30),
            meeting_type="onboarding"
        )
        db.session.add(new_meeting)
        db.session.commit()

        new_meeting.add_notes("initial session completed.")
        db.session.commit()

        assert new_meeting.status == 'scheduled'
        assert "Initial onboarding session completed." in new_meeting.notes

    def test_end_to_end_application_workflow(self):
        
        company = Company(company_name="TechFlow", website="https://techflow.com", category="IT", email="hr@techflow.com", password=None)
        staff = Staff("coord@sta.uwi.edu", "pass", "Alicia", "Baptiste", "DCIT")
        student = Student("816000999@my.uwi.edu", "pass", "Ravi", "M", "816000999", "CS")
        
        db.session.add_all([company, staff, student])
        db.session.commit()

        project = Project(project_name="IT  backend intern",international_students=True,place_of_work=True,description="ffo difff feo'nfe enf'fef foijwejjf isdfjjdsf",stipend = 8200,hired_after= False,number_of_interns = 2,details = "eff ff[of fomfsd] ofnsif nfeofnen ijfjjfd ifjsfj ijp- oononnoe",covid_vaccination = True,company_id = company.id,registration_id=None)
 
        db.session.add(project)
        db.session.commit()

        application = Student_application(
            student_id=student.student_id,
            first_name="Ravi",
            last_name="M",
            email="816000999@my.uwi.edu",
            contact_number="1234567",
            covid_19_vaccination=True,
            summer_requirment="Yes",
            program="BSc Computer Science",
            cover_letter="iam very interested in this role.",
            internship_credits=3,
            citizenship="Local",
            profile_picture="pic.jpg",
            returning_intern=False,
            year_of_study=2,
            resume="resume.pdf",
            transcript="transcript.pdf"
        )
        db.session.add(application)
        db.session.commit()

        shortlist = Shortlist(
            staff_id=staff.staff_id, 
            student_id=student.student_id, 
            project_id=project.id,
            match_reason="strong backend skills"
        )
        db.session.add(shortlist)
        db.session.commit()

        shortlist.mark_as_hired()
        student.current_internship_status='hired'
        db.session.commit()

        retrieved_shortlist = Shortlist.query.get(shortlist.id)
        
        retrieved_student = Student.query.filter_by(id=student.id).first()
      
        assert retrieved_shortlist.hired == True
        assert retrieved_shortlist.status == 'hired'
        assert retrieved_student.current_internship_status == 'hired'

    def test_internship_evaluation_workflow(self):
        
        company = Company(company_name="Techflow", website="https://techflow.com", category="IT", email="hrefef@techflow.com", password=None)
        staff = Staff("coord@sta.uwi.edu", "pass", "Alicia", "B", "DCIT")
        student = Student("816000123@my.uwi.edu", "pass", "John", "D", "816000123", "CS")
        db.session.add_all([company, staff, student])
        db.session.commit()

        project = Project(project_name="IT  backend intern",international_students=True,place_of_work=True,description="ffo difff feo'nfe enf'fef foijwejjf isdfjjdsf",stipend = 8200,hired_after= False,number_of_interns = 2,details = "eff ff[of fomfsd] ofnsif nfeofnen ijfjjfd ifjsfj ijp- oononnoe",covid_vaccination = True,company_id = company.id,registration_id=None)
 
        db.session.add(project)
        db.session.commit()

        eval_report = StudentEvaluation(
            company_id=company.id,
            student_id=student.id,
            project_id=project.id,
            evaluation_form_path="final_eval.pdf",
            evaluator_name="jane "
        )
        
        db.session.add(eval_report)
        db.session.commit()

        retrieved_eval = StudentEvaluation.query.get(eval_report.id)
        retrieved_eval.add_staff_review(staff.staff_id, "Student performed exceptionally well.")
        db.session.commit()

        final_eval = StudentEvaluation.query.get(eval_report.id)
        
        assert final_eval.status == 'reviewed_by_staff'
        assert final_eval.reviewed_by_staff == True
        assert final_eval.staff_reviewer.first_name== "Alicia"
        assert final_eval.company.company_name== "Techflow"

    def test_weekly_report_approval_workflow(self):
        staff = Staff("coord2@sta.uwi.edu", "pass", "Alicia", "B", "DCIT")
        student =Student("816000777@my.uwi.edu", "pass", "mark", "S", "816000777", "CS")
        company = Company(company_name="Innovate", email="hr@innovate.com", password="pass")
        db.session.add_all([staff, student, company])
        db.session.commit()

        project = Project(project_name="IT  backend intern",international_students=True,place_of_work=True,description="ffo difff feo'nfe enf'fef foijwejjf isdfjjdsf",stipend = 8200,hired_after= False,number_of_interns = 2,details = "eff ff[of fomfsd] ofnsif nfeofnen ijfjjfd ifjsfj ijp- oononnoe",covid_vaccination = True,company_id = company.id,registration_id=None)
        db.session.add(project)
        db.session.commit()

        report = WeeklyReport(
            student_id=student.id,
            project_id=project.id,
            week_number=1,
            report_file_path="week1_report.pdf",
            description="completed the database design.",
            hours_worked=15.5
        )
        db.session.add(report)
        db.session.commit()
        retrieved_report = WeeklyReport.query.filter_by(
            student_id=student.id, 
            week_number=1
        ).first()
        
        retrieved_report.approve_report(staff.staff_id)
        db.session.commit()

        final_report = WeeklyReport.query.get(report.id)
        assert final_report.status =="approved"
        assert final_report.reviewed ==True
        assert final_report.reviewed_by ==staff.staff_id
        assert final_report.student.first_name =="mark"
        assert final_report.reviewer.first_name =="alicia"

    def test_student_duplicate_id_fail(self):
        student1 = Student(
            email="ravi.1@my.uwi.edu",
            password="password123",
            first_name="ravi",
            last_name="maharaj",
            student_id="816000001",
            degree="CS"
        )
        db.session.add(student1)
        db.session.commit()

        student2 = Student(
            email="new@my.uwi.edu",
            password="password123",
            first_name="john",
            last_name="doe",
            student_id="816000001",
            degree="CS"
        )
        db.session.add(student2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback() 
