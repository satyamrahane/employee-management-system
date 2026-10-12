from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from .models import EmployeeModel
from .schemas import (
    DashboardStatsResponse,
    EmployeeCreate,
    EmployeeSortField,
    EmployeeUpdate,
    SortDirectionType,
)


SORTABLE_EMPLOYEE_FIELDS = {
    "employee_code": EmployeeModel.employee_code,
    "first_name": EmployeeModel.first_name,
    "last_name": EmployeeModel.last_name,
    "email": EmployeeModel.email,
    "job_title": EmployeeModel.job_title,
    "department": EmployeeModel.department,
    "date_of_joining": EmployeeModel.date_of_joining,
    "employment_status": EmployeeModel.employment_status,
    "created_at": EmployeeModel.created_at,
    "updated_at": EmployeeModel.updated_at,
}


def get_employees(
    db: Session,
    search: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: EmployeeSortField = "name",
    sort_order: SortDirectionType = "asc",
) -> Tuple[List[EmployeeModel], int]:
    """Return one filtered employee page and the total number of matches."""
    query = db.query(EmployeeModel)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                EmployeeModel.first_name.ilike(search_term),
                EmployeeModel.last_name.ilike(search_term),
                EmployeeModel.email.ilike(search_term),
                EmployeeModel.employee_code.ilike(search_term),
                EmployeeModel.job_title.ilike(search_term),
            )
        )

    if department and department != "All":
        query = query.filter(EmployeeModel.department == department)

    if status and status != "ALL":
        query = query.filter(EmployeeModel.employment_status == status)

    total = query.count()
    sort_columns = (
        [EmployeeModel.first_name, EmployeeModel.last_name]
        if sort_by == "name"
        else [SORTABLE_EMPLOYEE_FIELDS[sort_by]]
    )
    ordering = [
        column.asc() if sort_order == "asc" else column.desc()
        for column in sort_columns
    ]
    ordering.append(EmployeeModel.id.asc())
    items = query.order_by(*ordering).offset(skip).limit(limit).all()
    return items, total


def get_employee_by_id(db: Session, employee_id: str) -> Optional[EmployeeModel]:
    return db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()


def get_employee_by_email(db: Session, email: str) -> Optional[EmployeeModel]:
    return db.query(EmployeeModel).filter(EmployeeModel.email == email.strip().lower()).first()


def get_employee_by_code(db: Session, code: str) -> Optional[EmployeeModel]:
    return db.query(EmployeeModel).filter(EmployeeModel.employee_code == code.strip().upper()).first()


def create_employee(db: Session, employee_in: EmployeeCreate) -> EmployeeModel:
    db_employee = EmployeeModel(
        employee_code=employee_in.employee_code,
        first_name=employee_in.first_name,
        last_name=employee_in.last_name,
        email=employee_in.email,
        phone_number=employee_in.phone_number or "",
        job_title=employee_in.job_title,
        department=employee_in.department,
        date_of_joining=employee_in.date_of_joining,
        employment_status=employee_in.employment_status,
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def update_employee(
    db: Session,
    db_employee: EmployeeModel,
    employee_in: EmployeeUpdate,
) -> EmployeeModel:
    update_data = employee_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_employee, field, value)

    db_employee.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def update_employee_status(
    db: Session,
    db_employee: EmployeeModel,
    new_status: str,
) -> EmployeeModel:
    db_employee.employment_status = new_status
    db_employee.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def get_dashboard_stats(db: Session) -> DashboardStatsResponse:
    total = db.query(func.count(EmployeeModel.id)).scalar() or 0
    active = db.query(func.count(EmployeeModel.id)).filter(EmployeeModel.employment_status == "ACTIVE").scalar() or 0
    inactive = db.query(func.count(EmployeeModel.id)).filter(EmployeeModel.employment_status == "INACTIVE").scalar() or 0
    departments = db.query(func.count(func.distinct(EmployeeModel.department))).scalar() or 0

    return DashboardStatsResponse(
        totalEmployees=total,
        activeEmployees=active,
        inactiveEmployees=inactive,
        departmentsCount=departments,
    )
