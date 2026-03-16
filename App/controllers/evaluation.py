from datetime import datetime
from App.database import db
from App.models.studentevaluation import StudentEvaluation
from App.models.project import Project


def get_evaluation(evaluation_id):
    return db.session.get(StudentEvaluation, evaluation_id)


def get_company_evaluations(company_id):
    return (
        StudentEvaluation.query
        .filter_by(company_id=company_id)
        .order_by(StudentEvaluation.created_at.desc())
        .all()
    )


def get_company_evaluations_json(company_id):
    evaluations = get_company_evaluations(company_id)
    return [e.get_json() for e in evaluations] if evaluations else []


def get_project_evaluations(project_id, company_id=None):
    query = StudentEvaluation.query.filter_by(project_id=project_id)
    if company_id is not None:
        query = query.filter_by(company_id=company_id)
    return query.order_by(StudentEvaluation.created_at.desc()).all()


def get_student_evaluations(student_id, company_id=None):
    query = StudentEvaluation.query.filter_by(student_id=student_id)
    if company_id is not None:
        query = query.filter_by(company_id=company_id)
    return query.order_by(StudentEvaluation.created_at.desc()).all()


def create_evaluation(
    company_id,
    student_id,
    project_id,
    evaluation_form_path,
    evaluation_period='final',
    evaluator_name=None,
    evaluator_title=None,
    evaluator_email=None,
    overall_rating=None,
    technical_skills_rating=None,
    communication_rating=None,
    professionalism_rating=None,
    teamwork_rating=None,
    problem_solving_rating=None,
    strengths=None,
    areas_for_improvement=None,
    comments=None,
    recommend_for_future_employment=None,
    would_hire_again=None,
    internship_completed=True,
    completion_date=None,
    status='submitted'
):
    project = db.session.get(Project, project_id)
    if project is None or project.company_id != company_id:
        return None

    existing = StudentEvaluation.query.filter_by(
        student_id=student_id,
        project_id=project_id,
        evaluation_period=evaluation_period
    ).first()

    if existing is not None:
        return 'duplicate'

    try:
        evaluation = StudentEvaluation(
            company_id=company_id,
            student_id=student_id,
            project_id=project_id,
            evaluation_form_path=evaluation_form_path,
            evaluation_period=evaluation_period,
            evaluator_name=evaluator_name,
            evaluator_title=evaluator_title,
            evaluator_email=evaluator_email
        )

        evaluation.set_ratings(
            overall=overall_rating,
            technical=technical_skills_rating,
            communication=communication_rating,
            professionalism=professionalism_rating,
            teamwork=teamwork_rating,
            problem_solving=problem_solving_rating
        )

        evaluation.strengths = strengths
        evaluation.areas_for_improvement = areas_for_improvement
        evaluation.comments = comments
        evaluation.recommend_for_future_employment = recommend_for_future_employment
        evaluation.would_hire_again = would_hire_again
        evaluation.internship_completed = internship_completed
        evaluation.status = status

        if completion_date is not None:
            evaluation.completion_date = completion_date

        db.session.add(evaluation)
        db.session.commit()
        return evaluation
    except Exception as e:
        db.session.rollback()
        print(f"Error creating evaluation: {e}")
        return None


def update_evaluation(
    evaluation_id,
    company_id=None,
    evaluation_form_path=None,
    evaluation_period=None,
    evaluator_name=None,
    evaluator_title=None,
    evaluator_email=None,
    overall_rating=None,
    technical_skills_rating=None,
    communication_rating=None,
    professionalism_rating=None,
    teamwork_rating=None,
    problem_solving_rating=None,
    strengths=None,
    areas_for_improvement=None,
    comments=None,
    recommend_for_future_employment=None,
    would_hire_again=None,
    internship_completed=None,
    completion_date=None,
    status=None
):
    evaluation = get_evaluation(evaluation_id)
    if evaluation is None:
        return None

    if company_id is not None and evaluation.company_id != company_id:
        return None

    try:
        if evaluation_form_path is not None:
            evaluation.upload_evaluation_form(evaluation_form_path)

        if evaluation_period is not None:
            evaluation.evaluation_period = evaluation_period
        if evaluator_name is not None:
            evaluation.evaluator_name = evaluator_name
        if evaluator_title is not None:
            evaluation.evaluator_title = evaluator_title
        if evaluator_email is not None:
            evaluation.evaluator_email = evaluator_email

        evaluation.set_ratings(
            overall=overall_rating,
            technical=technical_skills_rating,
            communication=communication_rating,
            professionalism=professionalism_rating,
            teamwork=teamwork_rating,
            problem_solving=problem_solving_rating
        )

        if strengths is not None:
            evaluation.strengths = strengths
        if areas_for_improvement is not None:
            evaluation.areas_for_improvement = areas_for_improvement
        if comments is not None:
            evaluation.comments = comments
        if recommend_for_future_employment is not None:
            evaluation.recommend_for_future_employment = recommend_for_future_employment
        if would_hire_again is not None:
            evaluation.would_hire_again = would_hire_again
        if internship_completed is not None:
            evaluation.internship_completed = internship_completed
        if completion_date is not None:
            evaluation.completion_date = completion_date
        if status is not None:
            evaluation.status = status

        evaluation.updated_at = datetime.utcnow()
        db.session.commit()
        return evaluation
    except Exception as e:
        db.session.rollback()
        print(f"Error updating evaluation: {e}")
        return None


def delete_evaluation(evaluation_id, company_id=None):
    evaluation = get_evaluation(evaluation_id)
    if evaluation is None:
        return False

    if company_id is not None and evaluation.company_id != company_id:
        return False

    try:
        db.session.delete(evaluation)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting evaluation: {e}")
        return False