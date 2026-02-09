# Flask MVC Template - Replit Setup

## Overview
This is a Flask MVC web application following the Model-View-Controller pattern. The project has been successfully configured to run in the Replit environment.

## Project Architecture
- **Language**: Python 3.11
- **Framework**: Flask with SQLAlchemy, Flask-Migrate, Flask-Admin, Flask-JWT-Extended
- **Database**: SQLite (development) with PostgreSQL support
- **Structure**: MVC pattern with organized controllers, models, views, and templates
- **Authentication**: JWT-based authentication system

## Recent Changes (September 28, 2025)
- Fresh GitHub import setup completed for Replit environment
- Installed Python 3.11 environment and all Flask dependencies from requirements.txt
- Initialized SQLite database with user management system using `flask init`
- Configured Flask development server to run on 0.0.0.0:5000 for Replit proxy compatibility
- Set up Flask Server workflow with debug mode enabled for development
- Updated Gunicorn configuration to bind to port 5000 for production consistency
- Configured deployment settings for autoscale deployment using Gunicorn with proper wsgi:app entry point
- Verified web application functionality - Flask MVC app loads successfully with login interface

## Current State
- ✅ Flask server running on port 5000
- ✅ Database initialized with user management
- ✅ All dependencies installed and working
- ✅ Development workflow configured
- ✅ Deployment configuration set up
- ✅ Test users created and verified

## Available Commands
- `flask run` - Start development server
- `flask init` - Initialize database
- `flask user create <username> <password>` - Create new user
- `flask user list` - List all users
- `pytest` - Run tests

## Key Files
- `wsgi.py` - Application entry point
- `App/main.py` - Flask application factory
- `App/config.py` - Configuration management
- `App/default_config.py` - Development configuration
- `requirements.txt` - Python dependencies
- `gunicorn_config.py` - Production server configuration

## Development Server
The Flask development server is configured to run on 0.0.0.0:5000 with debug mode enabled, making it accessible through Replit's proxy system.

## Deployment
Configured for autoscale deployment using Gunicorn with the command:
`gunicorn --bind=0.0.0.0:5000 --reuse-port wsgi:app`