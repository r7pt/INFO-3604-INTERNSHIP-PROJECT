from App.database import db
from datetime import datetime

class Announcement(db.Model):
    __tablename__ = 'announcement'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    message = db.Column(db.Text, nullable=False)

    audience = db.Column(db.String(50), default='all', index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, title, message, audience='all'):
        self.title = title
        self.message = message
        self.audience = audience

    def get_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'audience': self.audience,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Announcement {self.id}: {self.title}>"