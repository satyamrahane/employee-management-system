import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from .database import Base


def generate_uuid() -> str:
    return f"emp-{uuid.uuid4().hex[:10]}"


class EmployeeModel(Base):
    """SQLAlchemy ORM model representing the 'employees' relational table.

    Matches Section 7 and 8 of SRS.md and the frontend Employee interface.
    """
    __tablename__ = "employees"

    id = Column(String(50), primary_key=True, default=generate_uuid, index=True)
    employee_code = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=True, default="")
    job_title = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False, index=True)
    date_of_joining = Column(String(10), nullable=False)  # ISO Date YYYY-MM-DD
    employment_status = Column(String(20), nullable=False, default="ACTIVE", index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
