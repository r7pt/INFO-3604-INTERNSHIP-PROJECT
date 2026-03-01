from App.main import create_app
from App.database import get_migrate

app = create_app()
migrate = get_migrate(app)