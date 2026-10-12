import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import EmployeeModel

# In-memory SQLite database specifically for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables for every test and tear them down afterwards."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    # Seed 2 standard test records
    emp1 = EmployeeModel(
        id="test-emp-1",
        employee_code="TEST-1001",
        first_name="Priya",
        last_name="Sharma",
        email="priya.test@example.com",
        phone_number="+1 555-0101",
        job_title="Software Engineer",
        department="Engineering",
        date_of_joining="2023-01-15",
        employment_status="ACTIVE",
    )
    emp2 = EmployeeModel(
        id="test-emp-2",
        employee_code="TEST-1002",
        first_name="Marcus",
        last_name="Vance",
        email="marcus.test@example.com",
        phone_number="+1 555-0102",
        job_title="Designer",
        department="Design",
        date_of_joining="2022-05-20",
        employment_status="INACTIVE",
    )
    db.add(emp1)
    db.add(emp2)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_dashboard_stats():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["totalEmployees"] == 2
    assert data["activeEmployees"] == 1
    assert data["inactiveEmployees"] == 1
    assert data["departmentsCount"] == 2


def test_list_employees():
    response = client.get("/api/employees")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert data["skip"] == 0
    assert data["limit"] == 100
    assert data["page"] == 1
    assert data["total_pages"] == 1
    assert data["has_previous"] is False
    assert data["has_next"] is False
    assert "created_at" not in data["items"][0]
    assert "updated_at" not in data["items"][0]


def test_search_and_filter_employees():
    # Search by name
    res_search = client.get("/api/employees?search=Priya")
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) == 1
    assert res_search.json()["items"][0]["first_name"] == "Priya"

    # Filter by department
    res_dept = client.get("/api/employees?department=Design")
    assert res_dept.status_code == 200
    assert len(res_dept.json()["items"]) == 1
    assert res_dept.json()["items"][0]["department"] == "Design"

    # Filter by status
    res_status = client.get("/api/employees?status=INACTIVE")
    assert res_status.status_code == 200
    assert len(res_status.json()["items"]) == 1
    assert res_status.json()["total"] == 1
    assert res_status.json()["items"][0]["employment_status"] == "INACTIVE"


def test_employee_pagination_and_filtered_total():
    response = client.get("/api/employees?skip=1&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["first_name"] == "Priya"
    assert data["total"] == 2
    assert data["skip"] == 1
    assert data["limit"] == 1
    assert data["page"] == 2
    assert data["total_pages"] == 2
    assert data["has_previous"] is True
    assert data["has_next"] is False


def test_employee_sorting_uses_stable_id_tiebreaker():
    db = TestingSessionLocal()
    db.add(
        EmployeeModel(
            id="test-emp-0",
            employee_code="TEST-1000",
            first_name="Aarav",
            last_name="Sharma",
            email="aarav.test@example.com",
            phone_number="",
            job_title="Engineer",
            department="Engineering",
            date_of_joining="2023-01-10",
            employment_status="ACTIVE",
        )
    )
    db.commit()
    db.close()

    response = client.get("/api/employees?sort_by=department&sort_order=asc")
    assert response.status_code == 200
    items = response.json()["items"]
    engineering_ids = [item["id"] for item in items if item["department"] == "Engineering"]
    assert engineering_ids == ["test-emp-0", "test-emp-1"]


@pytest.mark.parametrize(
    "query",
    [
        "skip=-1",
        "limit=0",
        "limit=101",
        "department=Unknown",
        "status=ON_LEAVE",
        "sort_by=not_a_field",
        "sort_order=sideways",
        f"search={'x' * 101}",
    ],
)
def test_employee_list_rejects_invalid_parameters(query):
    response = client.get(f"/api/employees?{query}")
    assert response.status_code == 422


def test_employee_list_empty_results():
    response = client.get("/api/employees?search=not-found")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["total_pages"] == 0
    assert data["has_next"] is False


def test_get_single_employee_success():
    response = client.get("/api/employees/test-emp-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-emp-1"
    assert data["email"] == "priya.test@example.com"


def test_get_single_employee_not_found():
    response = client.get("/api/employees/non-existent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_create_employee_success():
    payload = {
        "employee_code": "TEST-1003",
        "first_name": "Amina",
        "last_name": "El-Sayed",
        "email": "amina.test@example.com",
        "phone_number": "+1 555-0103",
        "job_title": "Product Manager",
        "department": "Product",
        "date_of_joining": "2024-02-01",
        "employment_status": "ACTIVE",
    }
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["employee_code"] == "TEST-1003"
    assert data["id"].startswith("emp-")

    # Verify stats updated
    stats_res = client.get("/api/dashboard/stats")
    assert stats_res.json()["totalEmployees"] == 3


def test_create_employee_duplicate_code():
    payload = {
        "employee_code": "TEST-1001",  # Already exists
        "first_name": "Duplicate",
        "last_name": "Code",
        "email": "diff.email@example.com",
        "job_title": "Engineer",
        "department": "Engineering",
        "date_of_joining": "2024-01-01",
        "employment_status": "ACTIVE",
    }
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_employee_duplicate_email():
    payload = {
        "employee_code": "TEST-9999",
        "first_name": "Duplicate",
        "last_name": "Email",
        "email": "priya.test@example.com",  # Already exists
        "job_title": "Engineer",
        "department": "Engineering",
        "date_of_joining": "2024-01-01",
        "employment_status": "ACTIVE",
    }
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_update_employee():
    update_payload = {
        "job_title": "Principal Lead Engineer",
        "department": "Engineering",
    }
    response = client.put("/api/employees/test-emp-1", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_title"] == "Principal Lead Engineer"


def test_patch_employee_status():
    patch_payload = {"employment_status": "INACTIVE"}
    response = client.patch("/api/employees/test-emp-1/status", json=patch_payload)
    assert response.status_code == 200
    assert response.json()["employment_status"] == "INACTIVE"

    # Verify stats updated
    stats_res = client.get("/api/dashboard/stats")
    assert stats_res.json()["activeEmployees"] == 0
    assert stats_res.json()["inactiveEmployees"] == 2
