# Questions for Project Mentor
## Employee Management System (EMS)

**Document Status:** Pending Mentor Review  
**Date Prepared:** October 10, 2026  
**Purpose:** Clarify project scope, technology selections, and submission expectations before proceeding to design and code implementation.

---

### Question 1: Desktop View Deliverable Format
- **Context:** The requirement specifies both a mobile view and a desktop view using React Expo.
- **Question:** Should the desktop deliverable be implemented as a responsive web application running in a desktop browser via Expo Web, or is an installed desktop application wrapper (e.g., Electron) expected?
- **Proposed Default:** A responsive web application served via Expo Web from the same single codebase.

---

### Question 2: Expo Platform Targets & Scope
- **Context:** React Expo supports running on Web browsers as well as native mobile devices (Android / iOS).
- **Question:** Is a single responsive cross-platform codebase supporting both Web and mobile simulators acceptable, or are distinct native mobile app builds (e.g., Android APK) required for evaluation?
- **Proposed Default:** A unified React Expo codebase tested for native mobile layouts (via Expo Go / mobile simulator) and desktop browser viewports (via Expo Web).

---

### Question 3: Preferred Python Backend Framework
- **Context:** The requirement specifies Python for the backend service without specifying a framework.
- **Question:** Is **FastAPI** approved for the backend API, or does the curriculum/grading require **Flask** or **Django**?
- **Proposed Default:** FastAPI with Pydantic, due to its simplicity, modern typing, and built-in interactive Swagger API documentation.

---

### Question 4: Preferred SQL Database Engine
- **Context:** The requirement specifies an SQL database with AWS RDS connectivity.
- **Question:** Is **MySQL** approved as the SQL engine on AWS RDS, or is **PostgreSQL** preferred?
- **Proposed Default:** MySQL 8.0 on AWS RDS, accessed via SQLAlchemy ORM.

---

### Question 5: Scope of AWS Cloud Hosting
- **Context:** The requirement mandates an SQL database with RDS connectivity and AWS.
- **Question:** Is AWS usage expected solely for the cloud database (AWS RDS), with the Python backend running locally during development/evaluation? Or is the Python backend also required to be deployed on an AWS compute service (e.g., AWS EC2, Elastic Beanstalk, or AWS App Runner)?
- **Proposed Default:** AWS RDS for MySQL hosting the database in the cloud, while the Python API server and Expo development server run locally connected to RDS, minimizing cloud cost and configuration complexity for the student.

---

### Question 6: Mandatory vs. Optional Employee Management Features
- **Context:** The proposed scope includes Employee CRUD (Add, View, Update, Deactivate), search/filtering, and summary dashboard statistics.
- **Question:** Are there specific mandatory features required for evaluation (e.g., profile photo uploads, document attachments, salary/compensation history), or is standard text/data record management sufficient?
- **Proposed Default:** Standard employee profile data (name, code, email, phone, job title, department, join date, status) without file/document attachments.

---

### Question 7: User Authentication and Roles
- **Context:** An administrative system typically requires credential-based access control.
- **Question:** Is user authentication with separate roles (e.g., Administrator vs. standard Employee) a mandatory evaluation requirement, or should development focus purely on administrative employee management without login walls?
- **Proposed Default:** Lightweight JWT authentication with two roles: Administrator (full CRUD access) and Employee (read-only directory and personal profile access).

---

### Question 8: Department Management and Reporting Scope
- **Context:** Employees are categorized by departments, and management dashboards often summarize departmental headcounts.
- **Question:** Is a dedicated Department CRUD management module (creating/editing departments) required, or is a pre-seeded, fixed departmental dropdown sufficient? Are formal exportable reports (PDF/CSV) required?
- **Proposed Default:** Fixed pre-seeded departments and on-screen summary cards (no PDF/CSV export engine).

---

### Question 9: Evaluation and Submission Deliverables
- **Context:** Preparing project artifacts for grading.
- **Question:** What are the exact final deliverables required for submission?
  - Public/private GitHub repository link?
  - Live hosted web application URL?
  - Recorded video demonstration showing mobile and desktop workflows?
  - Written technical project report or presentation slides?
- **Proposed Default:** GitHub repository containing source code, comprehensive README setup instructions, and a recorded video demonstration of desktop and mobile views connected to AWS RDS.
