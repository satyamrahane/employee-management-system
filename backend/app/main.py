from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .schemas import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeSortField,
    EmployeeUpdate,
    EmployeeStatusUpdate,
    EmployeeResponse,
    DashboardStatsResponse,
    DepartmentType,
    EmploymentStatusType,
    HealthResponse,
    SortDirectionType,
)
from . import crud


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="REST API for the Employee Management System",
)

# Configure CORS Middleware for Frontend Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 1. Health Endpoint ---
@app.get(
    f"{settings.API_PREFIX}/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
)
def health_check():
    """Returns application health status and current database driver info."""
    db_driver = settings.DATABASE_URL.split(":")[0]
    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        database_driver=db_driver,
    )


# --- 2. Dashboard Statistics Endpoint ---
@app.get(
    f"{settings.API_PREFIX}/dashboard/stats",
    response_model=DashboardStatsResponse,
    tags=["Dashboard"],
    summary="Get workforce statistics",
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes total employees, active count, inactive count, and unique departments count."""
    return crud.get_dashboard_stats(db)


# --- 3. Employee Endpoints ---
@app.get(
    f"{settings.API_PREFIX}/employees",
    response_model=EmployeeListResponse,
    tags=["Employees"],
    summary="List, filter, search, and sort a page of employees",
)
def list_employees(
    search: Optional[str] = Query(
        None, min_length=1, max_length=100,
        description="Search name, email, employee code, or job title",
    ),
    department: Optional[DepartmentType] = Query(None, description="Filter by department"),
    status: Optional[EmploymentStatusType] = Query(None, description="Filter by employment status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    sort_by: EmployeeSortField = Query("name"),
    sort_order: SortDirectionType = Query("asc"),
    db: Session = Depends(get_db),
):
    """Return a bounded page and matching-result metadata."""
    items, total = crud.get_employees(
        db=db,
        search=search,
        department=department,
        status=status,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = (total + limit - 1) // limit
    return EmployeeListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        page=(skip // limit) + 1,
        total_pages=total_pages,
        has_previous=skip > 0,
        has_next=skip + len(items) < total,
    )


@app.get(
    f"{settings.API_PREFIX}/employees/{{employee_id}}",
    response_model=EmployeeResponse,
    tags=["Employees"],
    summary="Get an employee by ID",
)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    """Retrieve a single employee record by ID."""
    employee = crud.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID '{employee_id}' not found.",
        )
    return employee


@app.post(
    f"{settings.API_PREFIX}/employees",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Employees"],
    summary="Create a new employee",
)
def create_employee(employee_in: EmployeeCreate, db: Session = Depends(get_db)):
    """Creates a new employee record after verifying uniqueness of email and employee code."""
    # Check duplicate employee code
    if crud.get_employee_by_code(db, employee_in.employee_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee code '{employee_in.employee_code}' already exists.",
        )

    # Check duplicate email
    if crud.get_employee_by_email(db, employee_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email address '{employee_in.email}' is already registered.",
        )

    return crud.create_employee(db, employee_in)


@app.put(
    f"{settings.API_PREFIX}/employees/{{employee_id}}",
    response_model=EmployeeResponse,
    tags=["Employees"],
    summary="Update an existing employee",
)
def update_employee(
    employee_id: str,
    employee_in: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    """Updates an existing employee record, preventing email collisions with other employees."""
    db_employee = crud.get_employee_by_id(db, employee_id)
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID '{employee_id}' not found.",
        )

    # If updating email, ensure it is not taken by another employee
    if employee_in.email and employee_in.email.lower() != db_employee.email.lower():
        existing = crud.get_employee_by_email(db, employee_in.email)
        if existing and existing.id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email address '{employee_in.email}' is already registered to another employee.",
            )

    return crud.update_employee(db, db_employee, employee_in)


@app.patch(
    f"{settings.API_PREFIX}/employees/{{employee_id}}/status",
    response_model=EmployeeResponse,
    tags=["Employees"],
    summary="Update employee employment status",
)
def update_employee_status(
    employee_id: str,
    status_in: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
):
    """Toggles or updates an employee's status between ACTIVE and INACTIVE (soft-deactivation)."""
    db_employee = crud.get_employee_by_id(db, employee_id)
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID '{employee_id}' not found.",
        )

    return crud.update_employee_status(db, db_employee, status_in.employment_status)
