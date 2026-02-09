from .user import create_user
from .shortlist import add_student_to_shortlist
from .position import open_position
from App.database import db


def initialize():
    db.drop_all()
    db.create_all()
    create_user('bob', 'bobpass', "student")
    create_user('frank', 'frankpass', "employer")
    create_user('john', 'johnpass', "staff")
    open_position(user_id=2, title='Software Engineer', number_of_positions= 6)
    open_position(user_id=2, title='Mechanical Engineer', number_of_positions= 6)
    add_student_to_shortlist(student_id=1, position_id=1, staff_id=3)
