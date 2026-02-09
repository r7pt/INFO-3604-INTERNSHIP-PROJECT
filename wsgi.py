import click, pytest, sys
from flask.cli import with_appcontext, AppGroup

from App.database import db, get_migrate
from App.models import User
from App.main import create_app
from App.controllers import ( create_user, get_all_users_json, get_all_users, initialize, open_position, add_student_to_shortlist, decide_shortlist, get_shortlist_by_student, get_shortlist_by_position, get_positions_by_employer)


# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    print('database intialized')

'''
User Commands
'''

# Commands can be organized using groups

# create a group, it would be the first argument of the comand
# eg : flask user <command>
user_cli = AppGroup('user', help='User object commands') 

# Then define the command and any parameters and annotate it with the group (@)
@user_cli.command("create", help="Creates a user")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
@click.argument("user_type", default="student")
def create_user_command(username, password, user_type):
    result = create_user(username, password, user_type)
    if result:
        print(f'{username} created!')
    else:
        print("User creation failed")

# this command will be : flask user create bob bobpass

@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_user_command(format):
    if format == 'string':
        print(get_all_users())
    else:
        print(get_all_users_json())

@user_cli.command("add_position", help="Adds a position")
@click.argument("title", default="Software Engineer")
@click.argument("employer_id", default=1)
@click.argument("number", default=1)
def add_position_command(title, employer_id, number):
    position = open_position(title, employer_id, number)
    if position:
        print(f'{title} created!')
    else:
        print(f'Employer {employer_id} does not exist')

@user_cli.command("add_to_shortlist", help="Adds a student to a shortlist")
@click.argument("student_id", default=1)
@click.argument("position_id", default=1)
@click.argument("staff_id", default=1)
def add_to_shortlist_command(student_id, position_id, staff_id):
    test = add_student_to_shortlist(student_id, position_id, staff_id)
    if test:
        print(f'Student {student_id} added to shortlist for position {position_id}')
        print("\n\n__________________________________________________________________________\n\n")
    else:
        print('One of the following is the issue:')
        print(f'    Position {position_id} is not open')
        print(f'    Student {student_id} already in shortlist for position {position_id}')
        print(f'    There is no more open slots for position {position_id}')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("decide_shortlist", help="Decides on a shortlist")
@click.argument("student_id", default=1)
@click.argument("position_id", default=1)
@click.argument("decision", default="accepted")
def decide_shortlist_command(student_id, position_id, decision):
    test = decide_shortlist(student_id, position_id, decision)
    if test:
        print(f'Student {student_id} is {decision} for position {position_id}')
        print("\n\n__________________________________________________________________________\n\n")
    else:
        print(f'Student {student_id} not in shortlist for position {position_id}')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("get_shortlist", help="Gets a shortlist for a student")
@click.argument("student_id", default=1)
def get_shortlist_command(student_id):
    list = get_shortlist_by_student(student_id)
    if list:
        for item in list:
            print(f'Student {item.student_id} is {item.status.value} for position {item.position_id}')

        print("\n\n__________________________________________________________________________\n\n")
    else:
        print(f'Student {student_id} has no shortlists')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("get_shortlist_by_position", help="Gets a shortlist for a position")
@click.argument("position_id", default=1)
def get_shortlist_by_position_command(position_id):
    list = get_shortlist_by_position(position_id)
    if list:
        for item in list:
            print(f'Student {item.student_id} is {item.status.value} for {item.position.title} id: {item.position_id}')
            print(f'    Staff {item.staff_id} added this student to the shortlist')
            print(f'    Position {item.position_id} is {item.position.status.value}')
            print(f'    Position {item.position_id} has {item.position.number_of_positions} slots')
            print(f'    Position {item.position_id} is for {item.position.title}')
            print("\n\n__________________________________________________________________________\n\n")

    else:
        print(f'Position {position_id} has no shortlists')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("get_positions_by_employer", help="Gets all positions for an employer")
@click.argument("employer_id", default=1)
def get_positions_by_employer_command(employer_id):
    list = get_positions_by_employer(employer_id)
    if list:
        for item in list:
            print(f'Position {item.id} is {item.status.value}')
            print(f'    Position {item.id} has {item.number_of_positions} slots')
            print(f'    Position {item.id} is for {item.title}')
            print("\n\n__________________________________________________________________________\n\n")
    else:
            print(f'Employer {employer_id} has no positions')
            print("\n\n__________________________________________________________________________\n\n")
            
app.cli.add_command(user_cli) # add the group to the cli

'''
Test Commands
'''

test = AppGroup('test', help='Testing commands') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
    

app.cli.add_command(test)