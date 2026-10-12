# Employee Management System (EMS)

A full-stack web and mobile application for managing employee records, built with
React Expo (TypeScript) on the frontend and Python FastAPI on the backend,
connected to a MySQL database.

---

## Features

- **Employee Directory** — view all employees in a sortable, searchable desktop table and mobile card layout
- **Employee CRUD** — create, view, edit, deactivate, and reactivate employees
- **Dashboard** — live workforce statistics (total, active, inactive, departments)
- **Search** — real-time search across name, email, employee code, and job title
- **Filters** — filter by department and employment status independently or in combination
- **Sorting** — click any column header to sort ascending/descending (name, code, department, join date, status)
- **Empty States** — contextual messages and reset actions when no results match
- **Form Validation** — required fields, email format, date format, duplicate code/email prevention
- **Date Picker** — native platform date picker for join date selection
- **Deactivation Confirmation** — modal dialog requiring explicit confirmation before deactivation
- **Notifications** — temporary success and error toast notifications for all operations
- **Responsive Layout** — desktop sidebar table view and mobile card layout with sort pill bar
- **Authentication backend modules** — login, refresh, logout, identity, role, and session code with focused tests; these routes are not currently mounted in the running application

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend framework | React Expo + TypeScript | Expo ~57, React 19 |
| Frontend web runtime | React Native Web | 0.21.x |
| Frontend icons | @expo/vector-icons (Ionicons) | 15.x |
| Backend framework | Python FastAPI | >=0.115.0 |
| ASGI server | Uvicorn | >=0.30.0 |
| ORM | SQLAlchemy | >=2.0.30 |
| Data validation | Pydantic v2 | >=2.8.0 |
| Database | MySQL 8.x | 8.0 (local) |
| MySQL driver | PyMySQL | >=1.1.0 |
| Backend tests | pytest | >=8.3.0 |

---

## Architecture

```
+-------------------------------------+
|        React Expo Frontend          |
|  (TypeScript + React Native Web)    |
|  http://localhost:8081  (dev)       |
|                                     |
|  Screens: Dashboard, Employee List  |
|  Components: Table, Cards, Modals,  |
|              Forms, Toasts          |
+---------------+---------------------+
                | REST API (JSON over HTTP)
                | http://127.0.0.1:8000/api
+---------------v---------------------+
|      Python FastAPI Backend         |
|  + SQLAlchemy ORM + Pydantic v2     |
|  http://127.0.0.1:8000              |
|                                     |
|  Routes: /api/health                |
|          /api/dashboard/stats       |
|          /api/employees             |
+---------------+---------------------+
                | SQLAlchemy connection pool
+---------------v---------------------+
|        MySQL 8.x Database           |
|  Database: ems_db                   |
|  User: ems_user (least privilege)   |
|  localhost:3306                     |
+-------------------------------------+
```

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|-------------|----------------|-------|
| Node.js | 18.x LTS | Required for frontend |
| npm | 9.x | Included with Node.js |
| Python | 3.11+ | Required for backend |
| MySQL Server | 8.0+ | Must be running locally |
| Git | 2.x | For version control |

---

## Local Setup

### 1. Clone or download the project

```bash
git clone <repository-url> "employment management"
cd "employment management"
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure environment variables

Copy `backend/.env.example` to `backend/.env` (excluded from version control),
then set values appropriate for your local environment. The example selects a
disposable SQLite database and contains only a non-working JWT placeholder.
Replace that placeholder with a unique random secret of at least 32 bytes
before enabling authentication. Never use the example secret in a deployed
environment.

> **Never commit `.env` or real credentials to version control.**

#### Set up MySQL database and user

Log in to MySQL as root and run the following once:

```sql
CREATE DATABASE IF NOT EXISTS ems_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'ems_user'@'localhost' IDENTIFIED BY 'YOUR_SECURE_PASSWORD';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER
  ON ems_db.* TO 'ems_user'@'localhost';

FLUSH PRIVILEGES;
```

Replace `YOUR_SECURE_PASSWORD` with a strong password, then use the same
password in `backend/.env`.

#### Schema and development data

Alembic is the only supported mechanism for creating or changing database
schemas. Application startup does not create tables and does not seed employee
records. The existing MySQL database has an unrecorded migration baseline; its
baseline adoption and any authentication migration must be planned, backed up,
and approved separately. Do not run the fresh-database baseline against that
existing database.

For an empty, disposable SQLite development database only, set these values in
`backend/.env`:

```ini
APP_ENV=development
DATABASE_URL=sqlite:///./ems_dev.db
```

From `backend/`, create the schema and then explicitly seed demo employees:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade 20261011_0001
.\venv\Scripts\python.exe -m app.dev_seed
```

The seed command refuses production mode, non-SQLite databases, missing
schemas, and databases that already contain employees. It never deletes or
replaces employee records. Do not use this demo-data workflow for MySQL or
production.

#### Start the backend server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is available at http://127.0.0.1:8000
Interactive API docs: http://127.0.0.1:8000/docs

---

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Expo development server
npx expo start --web
```

The frontend is available at http://localhost:8081

> The frontend connects to `http://127.0.0.1:8000/api` by default.
> This URL is configured in `frontend/src/services/api.ts`.
> Update `API_BASE_URL` there before deploying to a remote server.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_ENV` | Runtime mode; the safe local seed workflow requires `development` | `development` |
| `DATABASE_URL` | SQLAlchemy database connection URL | `sqlite:///./ems_dev.db` |
| `AUTH_JWT_SECRET_KEY` | Unique signing secret of at least 32 random bytes; required when authentication is enabled | Set a private random value; never commit it |
| `AUTH_TRUSTED_ORIGINS` | JSON list of permitted browser origins for authentication requests | `["http://localhost:8081"]` |
| `AUTH_COOKIE_SECURE` | Whether authentication cookies require HTTPS; set `false` only for local HTTP development | `false` locally; `true` for HTTPS |

Other settings have defaults in `backend/app/config.py`. The authentication
router is currently not registered by `backend/app/main.py`; the auth
environment settings alone do not enable those routes.

### Frontend

No `.env` file. The API base URL is set directly in `frontend/src/services/api.ts`:

```typescript
export const API_BASE_URL = 'http://127.0.0.1:8000/api';
```

Update this before deploying to a remote environment.

---

## API Endpoints

Base URL: `http://127.0.0.1:8000/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/dashboard/stats` | Workforce statistics |
| `GET` | `/employees` | List employees (query params: search, department, status, skip, limit) |
| `GET` | `/employees/{id}` | Get employee by ID |
| `POST` | `/employees` | Create employee |
| `PUT` | `/employees/{id}` | Update employee |
| `PATCH` | `/employees/{id}/status` | Update employment status |

### Example requests

```bash
# Health check
curl http://127.0.0.1:8000/api/health

# List all employees
curl http://127.0.0.1:8000/api/employees

# Search with filters
curl "http://127.0.0.1:8000/api/employees?search=Priya&department=Engineering&status=ACTIVE"

# Create employee
curl -X POST http://127.0.0.1:8000/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "employee_code": "EMP-1007",
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe@example.com",
    "job_title": "Software Engineer",
    "department": "Engineering",
    "date_of_joining": "2024-06-01",
    "employment_status": "ACTIVE"
  }'

# Update status
curl -X PATCH http://127.0.0.1:8000/api/employees/{id}/status \
  -H "Content-Type: application/json" \
  -d '{"employment_status": "INACTIVE"}'
```

---

## Running Tests

### Backend

```bash
cd backend
venv\Scripts\activate   # Windows
pytest -v
```

The backend test suite covers employee API behavior, authentication and
security services, migration generation, and startup/seeding safety. Tests
use isolated test databases; no production database should be used for tests.

### Frontend type checking

```bash
cd frontend
npx tsc --noEmit
```

### Frontend production build

```bash
cd frontend
npx expo export --platform web
# Output written to frontend/dist/
```

---

## Project Directory Structure

```
employment management/
|-- README.md                          # This file
|-- AWS_DEPLOYMENT.md                  # AWS Cloud Deployment & RDS Guide
|-- SRS.md                             # Software Requirements Specification
|-- IMPLEMENTATION_PLAN.md             # Implementation stages and tasks
|-- TECH_STACK.md                      # Technology decisions
|-- QUESTIONS_FOR_MENTOR.md            # Design questions for mentor
|-- .gitignore
|
|-- backend/
|   |-- .env                           # Local secrets (NOT committed)
|   |-- .env.example                   # Safe environment template
|   |-- requirements.txt               # Python dependencies
|   |-- app/
|   |   |-- main.py                    # FastAPI app, routes, CORS
|   |   |-- config.py                  # Settings (reads .env)
|   |   |-- database.py                # SQLAlchemy engine and session
|   |   |-- models.py                  # EmployeeModel ORM
|   |   |-- auth_api.py                # Authentication routes (not mounted)
|   |   |-- auth_models.py             # Authentication database models
|   |   |-- auth_service.py            # Refresh-session services
|   |   |-- security.py                # Password and token security helpers
|   |   |-- dev_seed.py                # Explicit SQLite development seeder
|   |   |-- schemas.py                 # Pydantic schemas
|   |   |-- crud.py                    # Database query functions
|   |   |-- alembic/                   # Database migrations
|   |   |-- init_mysql_database.py     # Database setup script
|   |   `-- migrate_to_mysql.py        # SQLite-to-MySQL migration
|   |-- tests/
|   |   |-- test_api.py                # Employee API tests
|   |   |-- test_auth_api.py           # Authentication API tests
|   |   |-- test_security.py           # Security tests
|   |   `-- ...                        # Migration and startup-safety tests
|   `-- venv/                          # Virtual environment (NOT committed)
|
`-- frontend/
    |-- package.json
    |-- tsconfig.json
    |-- app.json
    |-- index.ts
    |-- dist/                          # Production build (NOT committed)
    `-- src/
        |-- types/employee.ts          # TypeScript types
        |-- services/api.ts            # API client
        |-- theme/colors.ts            # Design tokens
        |-- screens/
        |   |-- DashboardScreen.tsx
        |   `-- EmployeeListScreen.tsx
        |-- components/
        |   |-- EmployeeTableDesktop.tsx
        |   |-- EmployeeCardMobile.tsx
        |   |-- EmployeeModalForm.tsx
        |   |-- DeactivateConfirmModal.tsx
        |   |-- NotificationToast.tsx
        |   |-- DatePickerInput.tsx
        |   |-- StatCard.tsx
        |   |-- Sidebar.tsx
        |   |-- Header.tsx
        |   `-- MobileBottomNav.tsx
        `-- data/mockEmployees.ts
```

---

## Future AWS Deployment (Prepared, Not Yet Deployed)

The application is designed for AWS deployment. See [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) for
the complete deployment guide.

**Planned architecture:**
- **Frontend** — AWS S3 + CloudFront (static Expo Web export)
- **Backend** — AWS Elastic Beanstalk or EC2 (FastAPI + Uvicorn)
- **Database** — Amazon RDS for MySQL 8.0

**Key steps before deploying:**
1. Update `API_BASE_URL` in `frontend/src/services/api.ts` to the production backend URL
2. Add the production domain to `CORS_ORIGINS` in `backend/app/config.py`
3. Set `DATABASE_URL` as a secure environment variable on the backend host (not in code)
4. Run `npx expo export --platform web` to produce the `dist/` folder for S3

> No AWS resources have been created. Deployment requires explicit authorization.

---

## Security Notes

- `.env` files are excluded from version control (see `.gitignore`)
- Credentials are never embedded in frontend code or committed to the repository
- The application connects as `ems_user` with least-privilege MySQL grants
- CORS is restricted to known development origins; update for production
- No secrets appear in API responses or application logs

---

## Known Limitations

- No authentication or authorization (all operations are open)
- Departments are a fixed enumeration in the backend schema
- No pagination UI (API supports skip/limit; frontend requests up to 100 records)
- No file upload or profile image support

---

## Local Quick Start

```bash
# Terminal 1 — Backend
cd "employment management/backend"
venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd "employment management/frontend"
npx expo start --web
```

Open http://localhost:8081 in your browser.
