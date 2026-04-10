from App.database import db
from App.models.user import User


class Staff(User):
    __tablename__ = 'staff'

    staff_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(256), nullable=False)

    shortlists = db.relationship(
        'Shortlist',
        back_populates='staff',
        foreign_keys='Shortlist.staff_id',
        lazy=True
    )

    meetings = db.relationship(
        'Meeting',
        back_populates='staff',
        foreign_keys='Meeting.staff_id',
        lazy=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "staff",
    }

    def __init__(self, email, password, first_name, last_name, department, role="staff"):
        super().__init__(email, password, role)
        self.first_name = first_name
        self.last_name = last_name
        self.department = department

    @property
    def staffID(self):
        return self.staff_id

    @staffID.setter
    def staffID(self, value):
        self.staff_id = value

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_json(self):
        base_json = super().get_json()
        staff_json = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "department": self.department
        }
        return {**base_json, **staff_json}

    def __repr__(self):
        return f"<Staff {self.staff_id}: {self.full_name} ({self.department})>"