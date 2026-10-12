from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re

DepartmentType = Literal[
    "Engineering",
    "Design",
    "Product",
    "Human Resources",
    "Finance",
    "Marketing",
    "Sales",
    "Operations",
    "People Analytics",
]

EmploymentStatusType = Literal["ACTIVE", "INACTIVE"]
EmployeeSortField = Literal[
    "name",
    "employee_code",
    "first_name",
    "last_name",
    "email",
    "job_title",
    "department",
    "date_of_joining",
    "employment_status",
    "created_at",
    "updated_at",
]
SortDirectionType = Literal["asc", "desc"]


class EmployeeBase(BaseModel):
    employee_code: str = Field(..., min_length=2, max_length=20, examples=["EMP-1001"])
    first_name: str = Field(..., min_length=1, max_length=50, examples=["Priya"])
    last_name: str = Field(..., min_length=1, max_length=50, examples=["Sharma"])
    email: str = Field(..., min_length=5, max_length=100, examples=["priya.sharma@example.com"])
    phone_number: Optional[str] = Field(default="", max_length=25, examples=["+1 (555) 234-5678"])
    job_title: str = Field(..., min_length=1, max_length=100, examples=["Senior Software Engineer"])
    department: DepartmentType = Field(..., examples=["Engineering"])
    date_of_joining: str = Field(..., examples=["2024-01-15"])
    employment_status: EmploymentStatusType = Field(default="ACTIVE", examples=["ACTIVE"])

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        email = v.strip().lower()
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            raise ValueError("Invalid email format.")
        return email

    @field_validator("employee_code")
    @classmethod
    def clean_employee_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("date_of_joining")
    @classmethod
    def validate_iso_date(cls, v: str) -> str:
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, v.strip()):
            raise ValueError("Date of joining must follow YYYY-MM-DD format.")
        return v.strip()


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = Field(None, min_length=5, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=25)
    job_title: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[DepartmentType] = None
    date_of_joining: Optional[str] = None
    employment_status: Optional[EmploymentStatusType] = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        email = v.strip().lower()
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            raise ValueError("Invalid email format.")
        return email


class EmployeeStatusUpdate(BaseModel):
    employment_status: EmploymentStatusType = Field(..., examples=["INACTIVE"])


class EmployeeResponse(EmployeeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeListItem(EmployeeBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class EmployeeListResponse(BaseModel):
    items: List[EmployeeListItem]
    total: int
    skip: int
    limit: int
    page: int
    total_pages: int
    has_previous: bool
    has_next: bool


class DashboardStatsResponse(BaseModel):
    totalEmployees: int
    activeEmployees: int
    inactiveEmployees: int
    departmentsCount: int


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database_driver: str
