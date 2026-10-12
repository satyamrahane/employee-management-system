# Technology Stack Architecture
## Employee Management System (EMS)

**Document Status:** Draft — Awaiting Mentor Review & Confirmation  
**Version:** 1.0  
**Target Audience:** Project Mentor, Student Developer, Academic Evaluators  

---

## 1. Overview of Technology Classification

To maintain project compliance and clear technical boundaries, the technologies for the Employee Management System are divided into **Mentor-Mandated Technologies** (fixed requirements) and **Proposed Implementation Technologies** (recommended choices requiring mentor confirmation).

```
+-----------------------------------------------------------------------------------+
|                            EMPLOYEE MANAGEMENT SYSTEM                             |
+-----------------------------------------------------------------------------------+
|  [PRESENTATION LAYER]       React Expo (Mobile & Desktop View) *Mandated*         |
|                             React Native for Web & Native Mobile *Proposed*       |
+-----------------------------------------------------------------------------------+
                                         | JSON over HTTP / REST API
+-----------------------------------------------------------------------------------+
|  [APPLICATION LAYER]        Python *Mandated*                                     |
|                             FastAPI Framework + Pydantic + Uvicorn *Proposed*     |
+-----------------------------------------------------------------------------------+
                                         | SQLAlchemy ORM Connection Pool
+-----------------------------------------------------------------------------------+
|  [PERSISTENCE LAYER]        SQL Database *Mandated* | AWS RDS Connectivity *Mandated*|
|                             MySQL Engine + AWS RDS MySQL Instance *Proposed*      |
+-----------------------------------------------------------------------------------+
|  [SOURCE CONTROL & INFRA]   GitHub Repository *Mandated* | AWS Cloud *Mandated*    |
+-----------------------------------------------------------------------------------+
```

---

## 2. Technology Comparison Matrix

| Component Layer | Mentor-Mandated Technology | Proposed Technology Choice | Status | Reason / Justification |
| :--- | :--- | :--- | :---: | :--- |
| **Frontend Framework** | React Expo | React Expo SDK (cross-platform) | Confirmed Mandate | Single codebase serving mobile and web viewports. |
| **User Viewports** | Mobile view & Desktop view | Responsive Web + Native Mobile targets | Confirmed Mandate | Satisfies dual viewport accessibility via responsive design. |
| **Backend Language** | Python | Python 3.10+ | Confirmed Mandate | Reliable, readable, student-friendly syntax. |
| **Backend Framework** | Not Specified (Python) | FastAPI | **Pending Confirmation** | Fast, modern, clear async support, built-in Swagger docs. |
| **Database Type** | SQL Database | MySQL 8.0 | **Pending Confirmation** | Industry-standard relational DB, native RDS support. |
| **ORM / DB Connectivity** | SQL Connectivity | SQLAlchemy | **Pending Confirmation** | Python standard ORM; safe against SQL injection; clean models. |
| **Cloud Hosting** | AWS (RDS Connectivity) | AWS RDS (MySQL Free Tier) | Confirmed Mandate (RDS) | Managed backups, high availability, zero server maintenance. |
| **Backend Hosting** | AWS | Localhost / AWS EC2 *(TBD)* | **Pending Confirmation** | Depending on whether mentor requires cloud backend hosting. |
| **Version Control** | GitHub Repository | Git + GitHub | Confirmed Mandate | Version tracking, collaboration, project submission. |

---

## 3. Detailed Component Descriptions

### 3.1 Presentation Layer: React Expo (Mandated)
- **Role:** Deliver both the desktop view and mobile view from a single maintainable codebase.
- **Proposed Framework Package:** Expo SDK with React Native Web support.
- **Key Advantages:**
  - Fast development iteration using Expo tooling.
  - Native performance on mobile devices with seamless HTML5 canvas/DOM rendering on desktop browsers.
  - Built-in primitives (`View`, `Text`, `Pressable`, `FlatList`) that map cleanly across platforms.

### 3.2 Application Layer: Python with FastAPI (Proposed)
- **Role:** Central API gateway handling business logic, validation, authentication, and database orchestration.
- **Why FastAPI is Proposed:**
  - **Student Maintainability:** Explicit typing via Pydantic makes request/response structures intuitive to understand and debug.
  - **Automatic Interactive Docs:** Generates Swagger UI (`/docs`) out of the box, simplifying API testing before frontend integration.
  - **Performance:** Lightweight, asynchronous architecture with minimal boilerplate compared to heavier alternatives like Django.

### 3.3 Persistence Layer: SQL with MySQL & SQLAlchemy (Proposed)
- **Role:** Relational data persistence with strict foreign key constraints and transactional integrity.
- **Why MySQL & SQLAlchemy are Proposed:**
  - **MySQL:** Native, first-class support in AWS RDS; predictable behavior and simple local development tooling.
  - **SQLAlchemy:** Abstracts raw SQL connection handling, provides connection pooling for cloud latency, and prevents SQL injection via parameterized object-relational mapping.

### 3.4 Cloud Database: AWS RDS (Mandated)
- **Role:** Cloud-hosted, managed SQL database accessible by the application backend.
- **Tier:** AWS Free Tier (`db.t3.micro` or `db.t4g.micro`, 20 GB Storage).
- **Security:** AWS VPC Security Group restricting inbound port access to authorized development/application IPs.

### 3.5 Version Control: GitHub (Mandated)
- **Role:** Single source of truth for all source code, migration scripts, and documentation.
- **Rules:** Clear `.gitignore` enforcing zero storage of `.env` files, API keys, or database credentials.

---

## 4. System Communication Architecture

```
+---------------------------------------------------------------+
|                        Client Layer                           |
|       [Expo Desktop Web View]      [Expo Mobile Native View]  |
+---------------------------------------------------------------+
                 |                               |
                 | HTTP / HTTPS (REST API)       |
                 v                               v
+---------------------------------------------------------------+
|                       API Service Layer                       |
|                      Python (FastAPI App)                     |
|                                                               |
|  - CORS Middleware             - Auth Dependency (JWT/Bearer) |
|  - Route Handlers (/employees) - Pydantic Request Validation  |
|  - Error Handlers              - Response Serialization       |
+---------------------------------------------------------------+
                                 |
                                 | TCP Port 3306 (SSL/TLS)
                                 | SQLAlchemy Connection Pool
                                 v
+---------------------------------------------------------------+
|                       Cloud Data Layer                        |
|                  AWS RDS (MySQL SQL Engine)                   |
|                                                               |
|  - users table                 - employees table              |
|  - departments table           - Indexes & Constraints        |
+---------------------------------------------------------------+
```

### Communication Protocols:
1. **Frontend to Backend:**
   - Stateless HTTP/HTTPS requests exchanging JSON payloads.
   - Authentication tokens passed in standard HTTP headers (`Authorization: Bearer <token>`).
   - CORS middleware enabled on the Python backend to accept requests from web origins.
2. **Backend to AWS RDS:**
   - Standard MySQL protocol over port 3306 with SSL encryption.
   - Managed connection pool with automatic keepalive/reconnect logic to guard against cloud idle disconnections.

---

## 5. Expo Cross-Platform Compatibility Considerations

Building a dual-view (desktop + mobile) application using React Expo requires careful architectural choices:

| Consideration | Mobile Application View | Desktop Web View | Architectural Strategy |
| :--- | :--- | :--- | :--- |
| **Navigation** | Stack navigator + Bottom tabs | Sidebar navigation + Wide view | Responsive container that conditionally renders a Sidebar (desktop) or Bottom Tabs (mobile). |
| **Data Display** | Compact cards / List items (`FlatList`) | Multi-column tabular grid | Component abstraction: `<EmployeeRecordView>` renders table row on wide screen, card on mobile. |
| **Viewport Detection** | Screen dimensions fixed to portrait | Variable width browser resizing | Use `useWindowDimensions()` hook with a 768px breakpoint boundary. |
| **Platform Libraries** | Native gestures, mobile camera/photo | Standard web events, file upload | Rely strictly on cross-platform Expo universal packages (`expo-status-bar`, etc.). |
| **Form Inputs** | Touch-friendly inputs, virtual keyboard offset | Standard mouse/keyboard inputs | Encapsulate forms with responsive max-width containers and keyboard-aware views. |

---

## 6. Technologies Requiring Mentor Confirmation
Before development begins, the student must secure explicit confirmation on the following proposed components:
1. **Python Framework:** Confirm whether **FastAPI** is approved, or if the mentor specifically requires **Flask** or **Django**.
2. **SQL Engine:** Confirm whether **MySQL** on RDS is approved, or if **PostgreSQL** is preferred.
3. **ORM Library:** Confirm whether **SQLAlchemy** is approved.
4. **Cloud Scope:** Confirm whether AWS usage is strictly limited to **AWS RDS**, or if the Python backend is also expected to be deployed on an AWS service (e.g., AWS EC2, Elastic Beanstalk, or AWS App Runner).
