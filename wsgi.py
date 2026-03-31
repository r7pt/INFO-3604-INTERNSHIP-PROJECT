from App.main import create_app
from App.database import get_migrate, db
from flask.cli import AppGroup
from App.models.staff import Staff
from App.models.student import Student
from App.models.company import Company
from App.models.project import Project
from werkzeug.security import generate_password_hash

app = create_app()
migrate = get_migrate(app)

@app.cli.command("init")
def initialize_database():
    db.drop_all()
    db.create_all()
    print("Database initialized.")

seed_cli = AppGroup("seed", help="Seed demo data")

@seed_cli.command("demo")
def seed_demo():
    try:
        existing_staff = Staff.query.filter_by(email="staff.demo@sta.uwi.edu").first()
        if not existing_staff:
            staff = Staff(
                email="staff.demo@sta.uwi.edu",
                password="demo123",
                first_name="Alicia",
                last_name="Baptiste",
                department="DCIT"
            )
            db.session.add(staff)

        existing_student_1 = Student.query.filter_by(email="816000001@my.uwi.edu").first()
        if not existing_student_1:
            s1 = Student(
                email="816000001@my.uwi.edu",
                password="demo123",
                first_name="Ravi",
                last_name="Maharaj",
                student_id="816000001",
                degree="BSc Computer Science"
            )
            s1.gpa = 3.62
            s1.year_of_study = 3
            s1.phone = "868-555-1001"
            s1.current_internship_status = "not_applied"
            s1.resume_path = "uploads/students/1/resume_demo.pdf"
            s1.transcript_path = "uploads/students/1/transcript_demo.pdf"
            s1.transcript_summary = "Strong programming and database background."
            db.session.add(s1)

        existing_student_2 = Student.query.filter_by(email="816000002@my.uwi.edu").first()
        if not existing_student_2:
            s2 = Student(
                email="816000002@my.uwi.edu",
                password="demo123",
                first_name="Keisha",
                last_name="Ali",
                student_id="816000002",
                degree="BSc Information Technology"
            )
            s2.gpa = 3.28
            s2.year_of_study = 2
            s2.phone = "868-555-1002"
            s2.current_internship_status = "not_applied"
            s2.resume_path = "uploads/students/2/resume_demo.pdf"
            s2.transcript_path = "uploads/students/2/transcript_demo.pdf"
            s2.transcript_summary = "Solid networking and web development courses completed."
            db.session.add(s2)

        existing_company = Company.query.filter_by(email="hr@techcorp.tt").first()
        if not existing_company:
            company = Company(
                company_name="TechCorp TT",
                website="https://techcorp.tt",
                category="Software / IT Services",
                email="hr@techcorp.tt"
            )
            company.password_hash = generate_password_hash("demo123", method="pbkdf2:sha256")
            db.session.add(company)

        db.session.commit()

        company = Company.query.filter_by(email="hr@techcorp.tt").first()

        existing_project_1 = Project.query.filter_by(project_name="Backend Intern").first()
        if not existing_project_1:
            p1 = Project(
                project_name="Backend Intern",
                number_of_interns=2,
                description="Work on Flask APIs and database integration.",
                details="Good Python and SQL skills preferred.",
                stipend=4500.0,
                place_of_work=True,
                international_students=False,
                hired_after=False,
                covid_vaccination=False,
                company_id=company.id
            )
            db.session.add(p1)

        existing_project_2 = Project.query.filter_by(project_name="Frontend Intern").first()
        if not existing_project_2:
            p2 = Project(
                project_name="Frontend Intern",
                number_of_interns=1,
                description="Work on HTML, CSS, JS and dashboard pages.",
                details="UI polish and responsive design experience preferred.",
                stipend=4200.0,
                place_of_work=True,
                international_students=False,
                hired_after=False,
                covid_vaccination=False,
                company_id=company.id
            )
            db.session.add(p2)

        db.session.commit()

        print("Demo data seeded successfully.")
        print("Staff login: staff.demo@sta.uwi.edu / demo123")
        print("Student login 1: 816000001@my.uwi.edu / demo123")
        print("Student login 2: 816000002@my.uwi.edu / demo123")
        print("Company login: hr@techcorp.tt / demo123")

    except Exception as e:
        db.session.rollback()
        print(f"Error seeding demo data: {e}")

app.cli.add_command(seed_cli)