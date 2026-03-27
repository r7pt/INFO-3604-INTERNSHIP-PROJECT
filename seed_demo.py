import os
from datetime import date, datetime, timedelta

from App.main import create_app
from App.database import db
from App.models.staff import Staff
from App.models.student import Student
from App.models.company import Company
from App.models.project import Project
from App.models.shortlist import Shortlist
from App.models.weeklyreport import WeeklyReport


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def ensure_pdf(path, title):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R
   /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 89 >>
stream
BT
/F1 18 Tf
72 720 Td
({title}) Tj
0 -30 Td
(Demo seed PDF for internship platform testing.) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000010 00000 n
0000000063 00000 n
0000000122 00000 n
0000000269 00000 n
0000000408 00000 n
trailer
<< /Root 1 0 R /Size 6 >>
startxref
478
%%EOF
"""
    with open(path, "w", encoding="latin-1") as f:
        f.write(content)


def seed():
    app = create_app()

    with app.app_context():
        uploads_dir = os.path.join(BASE_DIR, "uploads", "demo")
        resumes_dir = os.path.join(uploads_dir, "resumes")
        transcripts_dir = os.path.join(uploads_dir, "transcripts")
        reports_dir = os.path.join(uploads_dir, "weekly_reports")

        os.makedirs(resumes_dir, exist_ok=True)
        os.makedirs(transcripts_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        staff = Staff(
            email="staff@uwi.edu",
            password="staffpass123",
            first_name="Alicia",
            last_name="Joseph",
            department="Internship Coordination"
        )
        db.session.add(staff)
        db.session.flush()

        company1 = Company(
            company_name="Neon Systems Ltd",
            website="https://neonsystems.example.com",
            category="Software Development",
            email="hr@neonsystems.com",
            password="companypass123"
        )

        company2 = Company(
            company_name="Carib Analytics",
            website="https://caribanalytics.example.com",
            category="Data Analytics",
            email="careers@caribanalytics.com",
            password="companypass123"
        )

        db.session.add(company1)
        db.session.add(company2)
        db.session.flush()

        project1 = Project(
            project_name="Backend API Intern",
            international_students=False,
            place_of_work=True,
            description="Work on Flask APIs, authentication, and database integration.",
            stipend=4500.00,
            hired_after=True,
            number_of_interns=2,
            details="Experience with Python, Flask, SQLAlchemy, and REST APIs preferred.",
            covid_vaccination=False,
            company_id=company1.id
        )

        project2 = Project(
            project_name="Frontend Dashboard Intern",
            international_students=False,
            place_of_work=True,
            description="Work on dashboards and reporting views for internship tracking.",
            stipend=4000.00,
            hired_after=False,
            number_of_interns=1,
            details="Experience with HTML, CSS, JavaScript, and frontend integration preferred.",
            covid_vaccination=False,
            company_id=company1.id
        )

        project3 = Project(
            project_name="Data Analyst Intern",
            international_students=True,
            place_of_work=False,
            description="Analyze student placement data and build reporting insights.",
            stipend=5000.00,
            hired_after=True,
            number_of_interns=1,
            details="Experience with SQL, data cleaning, reporting, and analytics preferred.",
            covid_vaccination=False,
            company_id=company2.id
        )

        db.session.add(project1)
        db.session.add(project2)
        db.session.add(project3)
        db.session.flush()

        student1 = Student(
            email="816000001@my.uwi.edu",
            password="studpass123",
            first_name="Jaden",
            last_name="Baptiste",
            student_id="816000001",
            degree="BSc Computer Science"
        )
        student1.phone = "868-700-1001"
        student1.gender = "Male"
        student1.gpa = 3.62
        student1.year_of_study = 3
        student1.expected_graduation = date(2026, 6, 30)
        student1.current_internship_status = "hired"

        student2 = Student(
            email="816000002@my.uwi.edu",
            password="studpass123",
            first_name="Aaliyah",
            last_name="Maharaj",
            student_id="816000002",
            degree="BSc Information Technology"
        )
        student2.phone = "868-700-1002"
        student2.gender = "Female"
        student2.gpa = 3.41
        student2.year_of_study = 3
        student2.expected_graduation = date(2026, 6, 30)
        student2.current_internship_status = "applied"

        student3 = Student(
            email="816000003@my.uwi.edu",
            password="studpass123",
            first_name="Kareem",
            last_name="Ali",
            student_id="816000003",
            degree="BSc Computer Science"
        )
        student3.phone = "868-700-1003"
        student3.gender = "Male"
        student3.gpa = 3.15
        student3.year_of_study = 2
        student3.expected_graduation = date(2027, 6, 30)
        student3.current_internship_status = "not_applied"

        db.session.add(student1)
        db.session.add(student2)
        db.session.add(student3)
        db.session.flush()

        student1_resume = os.path.join(resumes_dir, "816000001_resume.pdf")
        student1_transcript = os.path.join(transcripts_dir, "816000001_transcript.pdf")
        student2_resume = os.path.join(resumes_dir, "816000002_resume.pdf")
        student2_transcript = os.path.join(transcripts_dir, "816000002_transcript.pdf")
        student3_resume = os.path.join(resumes_dir, "816000003_resume.pdf")
        student3_transcript = os.path.join(transcripts_dir, "816000003_transcript.pdf")
        report1_file = os.path.join(reports_dir, "816000001_week1.pdf")

        ensure_pdf(student1_resume, "Resume - 816000001")
        ensure_pdf(student1_transcript, "Transcript - 816000001")
        ensure_pdf(student2_resume, "Resume - 816000002")
        ensure_pdf(student2_transcript, "Transcript - 816000002")
        ensure_pdf(student3_resume, "Resume - 816000003")
        ensure_pdf(student3_transcript, "Transcript - 816000003")
        ensure_pdf(report1_file, "Weekly Report - 816000001 - Week 1")

        student1.resume_path = student1_resume
        student1.transcript_path = student1_transcript
        student2.resume_path = student2_resume
        student2.transcript_path = student2_transcript
        student3.resume_path = student3_resume
        student3.transcript_path = student3_transcript

        shortlist1 = Shortlist(
            staff_id=staff.id,
            student_id=student1.id,
            project_id=project1.id,
            match_reason="Strong backend skills and good GPA.",
            match_score=92.5
        )
        shortlist1.mark_as_hired()

        shortlist2 = Shortlist(
            staff_id=staff.id,
            student_id=student2.id,
            project_id=project3.id,
            match_reason="Good data skills and strong communication.",
            match_score=85.0
        )
        shortlist2.schedule_interview(datetime.utcnow() + timedelta(days=3))

        db.session.add(shortlist1)
        db.session.add(shortlist2)
        db.session.flush()

        report1 = WeeklyReport(
            student_id=student1.id,
            project_id=project1.id,
            week_number=1,
            report_file_path=report1_file,
            title="Week 1 Report",
            description="Completed onboarding, reviewed requirements, and explored the backend API structure.",
            hours_worked=20.0
        )
        db.session.add(report1)

        db.session.commit()

        print("Demo seed complete.")
        print("Staff: staff@uwi.edu / staffpass123")
        print("Companies: hr@neonsystems.com / companypass123")
        print("           careers@caribanalytics.com / companypass123")
        print("Students: 816000001@my.uwi.edu / studpass123")
        print("          816000002@my.uwi.edu / studpass123")
        print("          816000003@my.uwi.edu / studpass123")


if __name__ == "__main__":
    seed()