# Software Requirements Specification (SRS)
## Employee Management System (EMS)

**Document Status:** Draft — Awaiting Mentor Review & Confirmation  
**Version:** 1.1  
**Target Audience:** Project Mentor, Student Developer, Academic Evaluators  

---

## 1. Project Overview
The Employee Management System (EMS) is an administrative software application designed to streamline employee record management, organizational tracking, and operational visibility. The system provides both mobile and desktop client interfaces communicating over a RESTful interface with a centralized Python backend and a managed SQL cloud database hosted on Amazon Web Services (AWS RDS). The source code and project documentation are maintained on GitHub.

---

## 2. Project Objectives
- **Centralized Record Keeping:** Provide a reliable single source of truth for organizational employee data.
- **Cross-Platform Accessibility:** Deliver both a mobile application view and a browser-based desktop interface using React Expo.
- **Maintainable Architecture:** Implement clean, decoupled separation of concerns across presentation, API service, and data layers so the system is straightforward to explain, debug, and modify by a student.
- **Cloud Database Connectivity:** Connect the application backend to a managed relational database on AWS RDS.
- **Traceable Versioning:** Maintain all project code, configurations, and documentation transparently on GitHub.

---

## 3. Problem Statement
Small-to-medium organizations and academic simulations often rely on fragmented spreadsheets or disparate files to track employee details, departmental allocations, and employment statuses. This manual workflow introduces data duplication, human error, security risks, lack of concurrent updates, and an inability to access data across desktop workstations and mobile devices seamlessly. A centralized, cloud-connected Employee Management System solves these problems by enforcing consistent schemas, secure data access, and structured record management across mobile and desktop interfaces.

---

## 4. Project Scope

### 4.1 Requirements Classification: Mentor Mandates vs. Proposed Choices

| Category | Status | Details |
| :--- | :---: | :--- |
| **Frontend Framework** | **Mentor Mandated** | **React Expo** |
| **Client Views** | **Mentor Mandated** | **Mobile view and Desktop view** |
| **Desktop Delivery Method** | *Proposed Choice* | **Browser-based desktop interface via Expo Web support** *(No standalone desktop executable assumed)* |
| **Mobile Delivery Method** | *Proposed Choice* | **Mobile application via Expo** (tested in Expo Go / mobile simulator) |
| **Backend Language** | **Mentor Mandated** | **Python** |
| **Backend Framework** | *Proposed Choice* | **FastAPI** *(Requires mentor confirmation)* |
| **Persistence Model** | **Mentor Mandated** | **SQL Database** |
| **Database Engine** | *Proposed Choice* | **MySQL 8.0** *(Requires mentor confirmation)* |
| **Database Connectivity** | *Proposed Choice* | **SQLAlchemy ORM** *(Requires mentor confirmation)* |
| **Cloud Infrastructure** | **Mentor Mandated** | **AWS with RDS Connectivity** |
| **Cloud Architecture & Pricing** | *Proposed Choice* | **AWS RDS instance for SQL database** *(Engine, hosting architecture, and pricing assumptions require confirmation before provisioning; free resources not guaranteed)* |
| **Version Control** | **Mentor Mandated** | **GitHub Repository** |

### 4.2 Features Included in Initial Proposed Scope

#### Core Employee Record Management (Primary Focus)
1. **Add Employee Records:** Capture and store new employee profiles with validated fields.
2. **View Employee Records:** Display a comprehensive directory list and individual detail views.
3. **Update Employee Records:** Edit existing employee contact, position, and status details.
4. **Deactivate Employee Records:** Soft-delete/deactivate employees to preserve historical records.
5. **Search and Filtering:** Filter employee records by department or status; search by name, email, or employee code.
6. **Basic Employee Statistics:** Summary metrics on the dashboard (e.g., total employees, active count, inactive count).
7. **Form Validation & Error Feedback:** Clear, actionable feedback on input errors.
8. **Responsive Interfaces:** Mobile-optimized layout and browser-based desktop layout powered by React Expo.
9. **SQL Database with AWS RDS Connectivity:** Backend persistence to AWS RDS.

#### Proposed Features (Require Mentor Confirmation)
- **User Authentication & Session Management:** User login and token-based session handling *(Proposed — requires confirmation)*.
- **Administrator and Employee Roles:** Access control separating full administrative capabilities from standard read access *(Proposed — requires confirmation)*.
- **Employee Self-Service:** Ability for standard employees to log in and update their own contact details *(Proposed — requires confirmation)*.
- **Department Management CRUD:** Full administrative CRUD for departments *(Proposed — requires confirmation; fallback is a pre-seeded department list)*.

### 4.3 Features Explicitly Excluded
The following features are **strictly out of scope** for this project to maintain student feasibility and prevent scope creep:
- **Payroll & Compensation Management:** Excluded.
- **Time Tracking & Biometric Attendance:** Excluded.
- **Automated Email / SMS Notifications:** Excluded.
- **Document / Resume File Uploads:** Excluded.
- **Complex Analytics & PDF Report Engines:** Excluded.

---

## 5. Proposed User Roles and Permissions (Pending Confirmation)

> **Note on Scope:** Distinct user roles, authentication, and employee self-service are proposed features that require mentor confirmation before implementation. If the mentor approves a single-tier administrative scope without login walls, the application will operate in direct Administrator mode.

| Feature / Action | Administrator *(Proposed)* | Employee / Self-Service *(Proposed - Pending Confirmation)* |
| :--- | :---: | :---: |
| Authenticate / Log in | Yes | Yes (if self-service approved) |
| View Personal Profile | Yes | Yes (if self-service approved) |
| Update Personal Contact Info | Yes | Pending Confirmation |
| View Employee Directory | Yes | Read-Only |
| Add New Employee Record | Yes | No |
| Edit Any Employee Record | Yes | No |
| Deactivate / Reactivate Employee | Yes | No |
| View Basic Employee Statistics | Yes | No |
| Department CRUD (if approved) | Yes | No |

---

## 6. Functional Requirements

### 6.1 Authentication & Authorization (AUTH) *(Proposed Feature — Pending Confirmation)*
- **FR-AUTH-01:** *[Proposed]* If authentication is approved, the system shall allow users to log in securely using their identifier (email/username) and password.
- **FR-AUTH-02:** *[Proposed]* If authentication is approved, the system shall issue a secure token (JWT or session token) upon successful authentication to authorize subsequent API requests.
- **FR-AUTH-03:** *[Proposed]* If role-based access is approved, the system shall restrict administrative endpoints and UI management actions to authenticated Administrator users.
- **FR-AUTH-04:** *[Proposed]* If authentication is approved, the system shall allow users to log out securely, invalidating the client-side authentication state.
- **FR-AUTH-05:** *[Proposed]* If authentication is approved, the system shall display meaningful error feedback on invalid credentials without exposing whether the identifier or password was incorrect.

### 6.2 Core Employee Record Management (EMP) *(Primary Scope)*
- **FR-EMP-01:** The system shall allow adding a new employee record with all mandatory fields validated.
- **FR-EMP-02:** The system shall prevent the creation of employee records with duplicate email addresses or duplicate Employee IDs.
- **FR-EMP-03:** The system shall display a list of employee records showing key summary details (Full Name, Job Title, Department, Status, Employee Code).
- **FR-EMP-04:** The system shall allow viewing the full details of an individual employee record.
- **FR-EMP-05:** The system shall allow updating editable fields of an existing employee record.
- **FR-EMP-06:** The system shall allow deactivating (soft-deleting) an employee record rather than permanently deleting historical data.
- **FR-EMP-07:** The system shall allow reactivating a previously deactivated employee record.

### 6.3 Search, Filtering & Statistics (SRCH & STAT) *(Primary Scope)*
- **FR-SRCH-01:** The system shall provide search capabilities allowing users to find records by employee name, employee code/ID, or email.
- **FR-SRCH-02:** The system shall support filtering employee records by department and employment status (Active/Inactive).
- **FR-STAT-01:** The system shall display basic employee summary statistics on the main view/dashboard, including: Total Employees, Active Employees, Inactive Employees, and count per department.

### 6.4 Department Management (DEPT) *(Proposed Feature — Pending Confirmation)*
- **FR-DEPT-01:** *[Proposed]* If dedicated department management is approved, the system shall allow an Administrator to create, list, and update department records.
- **FR-DEPT-02:** *[Proposed]* If approved, employee records shall link to a department entity via a foreign key relationship; if not approved, departments shall be selected from a fixed pre-seeded set.

---

## 7. Initial Employee Data Fields

| Field Name | Data Type | Mandatory | Description / Validation Rules |
| :--- | :--- | :---: | :--- |
| `id` | Integer / UUID | Yes | Primary key, auto-generated |
| `employee_code` | String (20) | Yes | Unique corporate employee identifier (e.g., `EMP-1001`) |
| `first_name` | String (50) | Yes | Alphabetic characters, min 2 chars |
| `last_name` | String (50) | Yes | Alphabetic characters, min 2 chars |
| `email` | String (100) | Yes | Valid email format, unique across system |
| `phone_number` | String (20) | No | Standardized telephone format |
| `job_title` | String (100) | Yes | Position title (e.g., Software Engineer) |
| `department_id` | Integer / String | Yes | Department reference (FK to department table or fixed enum) |
| `date_of_joining`| Date | Yes | Valid date (cannot be future date) |
| `employment_status` | Enum / String | Yes | `ACTIVE`, `INACTIVE` (defaults to `ACTIVE`) |
| `created_at` | Timestamp | Yes | Auto-populated creation timestamp |
| `updated_at` | Timestamp | Yes | Auto-updating timestamp |

---

## 8. Proposed Database Entities and Relationships

```
+------------------------------------+            +----------------------------------+
|      departments (Proposed)        |            |            employees             |
+------------------------------------+            +----------------------------------+
| id (PK)                            | 1        * | id (PK)                          |
| name (Unique)                      |<-----------| employee_code (Unique)           |
| code (Unique)                      |            | first_name                       |
| description                        |            | last_name                        |
| created_at                         |            | email (Unique)                   |
+------------------------------------+            | phone_number                     |
                                                  | job_title                        |
                                                  | department_id (FK / Enum)        |
                                                  | date_of_joining                  |
+------------------------------------+            | employment_status                |
|         users (Proposed)           |            | created_at                       |
+------------------------------------+            | updated_at                       |
| id (PK)                            |            +----------------------------------+
| username (Unique)                  |                             | 1
| email (Unique)                     |                             |
| password_hash                      |                             | 0..1 (optional link)
| role (ADMIN/EMPLOYEE)              |-----------------------------+
| employee_id (FK)                   |
| is_active                          |
| created_at                         |
+------------------------------------+
```

*Note: The `users` and `departments` tables are marked as proposed components. If user authentication or dynamic department CRUD is not approved, the core system requires only the `employees` table with pre-seeded departmental identifiers.*

---

## 9. Non-Functional Requirements (NFR)

- **NFR-REL-01 (Reliability):** The backend API service shall gracefully handle database disconnection exceptions and return standard HTTP 5xx responses with structured error payloads.
- **NFR-PERF-01 (Performance):** Standard employee CRUD operations should respond within 500ms under typical network conditions.
- **NFR-MAINT-01 (Maintainability):** Code must follow standard Python (PEP 8) and React modular conventions. Functions and modules must be small, explicit, and free of over-engineered abstractions so a student can independently explain, debug, and modify them.
- **NFR-PORT-01 (Portability):** The frontend codebase must run on mobile viewports and desktop browser viewports using React Expo.

---

## 10. Security Requirements
- **SEC-01 (Password Security):** If authentication is approved, credentials must never be stored in plain text; passwords must be salted and hashed using modern algorithms (e.g., bcrypt).
- **SEC-02 (Token Security):** If token authentication is approved, tokens must be transmitted via HTTP headers (`Authorization: Bearer <token>`) with an expiration policy.
- **SEC-03 (SQL Injection Prevention):** All database operations must utilize parameterized queries or ORM mapping to prevent SQL injection vulnerabilities.
- **SEC-04 (Environment Secrets):** Database connection strings, AWS RDS endpoint credentials, and secret keys must be isolated in environment configuration files (`.env`) and never committed to GitHub.
- **SEC-05 (CORS Policy):** The backend API must configure Cross-Origin Resource Sharing (CORS) explicitly for approved client origins.

---

## 11. Mobile and Desktop Interface Requirements

### 11.1 Proposed Cross-Platform Architecture via React Expo
- **Mobile View:** An Expo-based mobile application interface designed for mobile screen dimensions and touch interactions (tested via Expo Go / mobile simulator). Employs stacked forms, touch targets, and mobile-friendly lists.
- **Desktop View:** A browser-based desktop interface rendered via Expo web support (`react-native-web`) running in standard modern web browsers (Chrome, Firefox, Edge, Safari). Employs wide multi-column data views, responsive sidebars, and desktop modal dialogues.
- **Architectural Clarification:** A standalone desktop executable (e.g., Electron or native desktop installer) is **not** assumed or required. Using Expo Web support provides a browser-based desktop interface from the same unified React Expo codebase, keeping development maintainable for a student.

---

## 12. AWS RDS Connectivity Requirements

- **Mandated Scope:** Cloud relational database connectivity using Amazon Web Services (AWS RDS).
- **Database Engine *(Proposed — Pending Confirmation)*:** MySQL 8.0 on AWS RDS is proposed; PostgreSQL is a secondary option. The specific engine requires confirmation before provisioning.
- **Hosting Architecture *(Pending Confirmation)*:** The database is hosted on AWS RDS. Whether the Python backend will run locally (connecting to RDS over the internet) or also be hosted on an AWS compute service (e.g., EC2) requires confirmation before provisioning.
- **Security Group Configuration:** The AWS RDS security group must restrict inbound traffic on the database port exclusively to authorized IP addresses.
- **Pricing & Cost Assumptions *(Must Be Confirmed Before Provisioning)*:**
  - **No guarantee of free resources:** While AWS provides an introductory Free Tier for eligible accounts and specific instance types (e.g., `db.t3.micro` or `db.t4g.micro`), Free Tier eligibility depends on account age, region, and usage thresholds. Free resources are **not guaranteed**.
  - All cloud hosting architecture and pricing assumptions must be reviewed and confirmed before any AWS cloud resources are provisioned to avoid unexpected billing.

---

## 13. Testing Requirements
- **Backend Testing:** Test cases (using `pytest`) covering:
  - Employee CRUD endpoints (successful creation, validation rejection, duplicate detection).
  - Authentication flow (if approved).
- **Frontend Validation Testing:** Verifying client-side error states on empty or invalid inputs.
- **Cloud Database Connectivity Testing:** Verification that the backend establishes a connection to AWS RDS and executes read/write queries.

---

## 14. Acceptance Criteria
1. The student can demonstrate adding, viewing, updating, and deactivating employee records from both the browser-based desktop interface and the mobile view.
2. The user can search employee records and view basic employee statistics.
3. Changes made in the client interface persist to and are retrieved from the SQL database connected through AWS RDS.
4. Input validation prevents invalid entries (e.g., duplicate emails, missing mandatory fields) and displays useful error messages.
5. All source code and documentation are maintained in a clean GitHub repository free of committed secrets.
6. The student can explain, walk through, debug, and modify the code without relying on over-engineered abstractions.

---

## 15. Assumptions
- The mentor accepts a single React Expo codebase delivering both an Expo mobile application view and a browser-based desktop interface via Expo Web.
- AWS credentials and cloud access are available for RDS provisioning, with pricing and resource limits confirmed before provisioning.
- Stable internet connectivity is available during development and demonstration for AWS RDS communication.

---

## 16. Unresolved Decisions Requiring Confirmation

Before implementation or AWS provisioning begins, the following decisions must be formally confirmed with the mentor:

1. **Desktop Deliverable Confirmation:** Confirm that a browser-based desktop interface using Expo Web support satisfies the "desktop view" requirement, with no standalone desktop executable required.
2. **Authentication & Roles Scope:** Confirm whether user authentication, separate Administrator/Employee roles, and employee self-service are required for project evaluation, or if single-tier administrative access is acceptable.
3. **Department Management Scope:** Confirm whether dedicated Department CRUD is required, or if a fixed pre-seeded department list is sufficient.
4. **Python Backend Framework:** Confirm whether **FastAPI** is approved (proposed choice).
5. **SQL Database Engine:** Confirm whether **MySQL** on AWS RDS is approved (proposed choice).
6. **AWS Architecture & Cost Confirmation:** Confirm whether the backend runs locally connecting to AWS RDS or requires AWS compute hosting (e.g., EC2), and verify cloud pricing/cost assumptions before provisioning resources.
7. **Evaluation Criteria & Submission Format:** Confirm final grading artifacts (e.g., GitHub repository, demo video, written report).
