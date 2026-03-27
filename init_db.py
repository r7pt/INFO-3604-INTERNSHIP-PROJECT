from App.main import create_app
from App.controllers import initialize

app = create_app()

with app.app_context():
    initialize()
    print("Database initialized + seeded.")