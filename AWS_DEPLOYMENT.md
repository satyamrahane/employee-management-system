# AWS Cloud Deployment Guide
## Employee Management System (EMS)

**Document Version:** 1.0  
**Target Audience:** Project Mentor, Student Developer, Academic Evaluators  
**Scope:** Provisioning AWS RDS for MySQL, configuring security groups, deploying the Python FastAPI backend, hosting the React Expo Web frontend on AWS S3/CloudFront, and establishing secure database connectivity.

---

## 1. Cloud Architecture Overview

The Employee Management System cloud deployment decouples the frontend, backend application server, and managed database into discrete, scalable, and secure AWS tiers:

```
+-----------------------------------------------------------------------------------+
|                                CLIENTS / USERS                                    |
|              Desktop Web Browser               Mobile Browser / Expo Go           |
+-----------------------------------------------------------------------------------+
                                          |
                                          | HTTPS (Port 443)
                                          v
+-----------------------------------------------------------------------------------+
|                        PRESENTATION TIER (STATIC HOSTING)                         |
|   AWS CloudFront (CDN + SSL) ------> AWS S3 Bucket (Static Website Hosting)      |
|   Domain: https://ems-portal.cloudfront.net                                       |
|   Build: React Expo Web (dist/ folder export)                                     |
+-----------------------------------------------------------------------------------+
                                          |
                                          | REST API Requests (JSON / HTTPS)
                                          v
+-----------------------------------------------------------------------------------+
|                        APPLICATION TIER (PYTHON BACKEND)                          |
|   AWS EC2 or Elastic Beanstalk (Linux)                                            |
|   - Uvicorn ASGI Server on port 8000 / Nginx Reverse Proxy                        |
|   - FastAPI Application + Pydantic v2 + SQLAlchemy ORM                            |
|   - Managed VPC Security Group: sg-ems-backend                                    |
+-----------------------------------------------------------------------------------+
                                          |
                                          | SQL over TLS/SSL (Port 3306)
                                          v
+-----------------------------------------------------------------------------------+
|                        DATA PERSISTENCE TIER (MANAGED SQL)                        |
|   Amazon RDS for MySQL 8.0                                                        |
|   - Instance Class: db.t3.micro or db.t4g.micro (AWS Free Tier Eligible)          |
|   - Database: ems_db                                                              |
|   - Least-Privilege App User: ems_user                                            |
|   - Managed VPC Security Group: sg-ems-rds (Port 3306 strictly restricted)        |
+-----------------------------------------------------------------------------------+
```

---

## 2. Prerequisites & AWS Account Setup

Before starting the deployment, ensure you have:
1. An active **AWS Account** with administrative or appropriate IAM permissions (`AmazonRDSFullAccess`, `AmazonEC2FullAccess`, `AmazonS3FullAccess`).
2. **AWS Free Tier status** (recommended for student projects to avoid unexpected charges).
3. **AWS CLI** installed locally (optional, but helpful for programmatic deployments).
4. Local terminal access with Python 3.10+ and Node.js 18+.

---

## 3. Provisioning Amazon RDS for MySQL (Step-by-Step)

Amazon Relational Database Service (RDS) provides managed MySQL instances with automated backups, monitoring, and failover capabilities.

### Step 3.1: Navigate to RDS in AWS Management Console
1. Log in to the [AWS Management Console](https://console.aws.amazon.com/).
2. In the top search bar, type **RDS** and select **RDS (Managed Relational Database Service)**.
3. Ensure your region is set to your preferred low-latency region (e.g., `us-east-1` (N. Virginia), `ap-south-1` (Mumbai), or `eu-west-1` (Ireland)).
4. Click **Create database**.

### Step 3.2: Choose Database Creation Method & Engine
1. **Database creation method:** Select **Standard create**.
2. **Engine options:** Select **MySQL**.
3. **Engine Version:** Select **MySQL 8.0.35** (or the latest available 8.0.x version).
4. **Templates:** Select **Free tier**.  
   *(Selecting "Free tier" automatically disables high-cost features like Multi-AZ and selects eligible instance sizes).*

### Step 3.3: Configure Settings & Credentials
1. **DB instance identifier:** `ems-mysql-production`
2. **Master username:** `admin` (or `ems_admin`)
3. **Master password:**
   - Choose **Self managed**.
   - Enter a strong password (minimum 16 characters with letters, numbers, and symbols).
   - Confirm the password and record it securely in your password manager.

### Step 3.4: Instance Configuration & Storage
1. **DB instance class:** **db.t3.micro** (2 vCPUs, 1 GiB RAM) or **db.t4g.micro**.
2. **Storage:**
   - **Storage type:** General Purpose SSD (gp2 or gp3).
   - **Allocated storage:** `20 GiB` (minimum required, covered under Free Tier).
   - **Enable storage autoscaling:** Uncheck or set maximum to `25 GiB` to prevent runaway scaling charges.

### Step 3.5: Connectivity & Network Configuration
1. **Virtual Private Cloud (VPC):** Select **Default VPC** (or your custom project VPC).
2. **Subnet group:** Default.
3. **Public access:**
   - **Yes** (if developing locally and connecting to RDS directly over the internet from your machine).
   - **No** (if the backend is deployed on an EC2 instance in the same VPC — the most secure production architecture).
4. **VPC security group:** Select **Create new**:
   - **New VPC security group name:** `sg-ems-rds`
5. **Availability Zone:** No preference.
6. **Database port:** `3306` (standard MySQL port).

### Step 3.6: Additional Configuration
1. Expand **Additional configuration**:
   - **Initial database name:** `ems_db` *(ensures the database is created immediately)*.
   - **DB parameter group:** default.mysql8.0.
   - **Automated backups:** Enable automated backups (retention period: 1 to 7 days).
   - **Encryption:** Enable encryption (uses AWS KMS default key `aws/rds`).
   - **Deletion protection:** Enable (recommended to avoid accidental database deletion).
2. Click **Create database**.  
   *(Provisioning typically takes 5–10 minutes while AWS initializes the VM and storage volume).*

---

## 4. Configuring Security Groups for RDS Access

Security groups act as a virtual firewall controlling inbound and outbound network traffic.

### Step 4.1: If Connecting from Localhost (Development / Evaluation Mode)
If your Python FastAPI backend runs locally and connects to the RDS instance in AWS:
1. Open the **EC2 Console** -> **Security Groups** -> select `sg-ems-rds`.
2. Under the **Inbound rules** tab, click **Edit inbound rules**.
3. Add a rule:
   - **Type:** MySQL/Aurora (`3306`)
   - **Protocol:** TCP
   - **Port range:** `3306`
   - **Source:** Select **My IP** (e.g., `203.0.113.50/32`).  
     *(Never use `0.0.0.0/0` in production; restricting to your public IP blocks unauthorized scanners).*
4. Click **Save rules**.

### Step 4.2: If Connecting from AWS EC2 / Elastic Beanstalk (Production Cloud Mode)
If your Python FastAPI backend runs on an AWS EC2 instance:
1. Identify the backend's security group: `sg-ems-backend`.
2. In `sg-ems-rds`, add an inbound rule:
   - **Type:** MySQL/Aurora (`3306`)
   - **Source:** Select **Custom** and enter the security group ID of the backend: `sg-ems-backend`.
3. This creates a zero-trust network boundary: only the backend application server can communicate with the RDS database.

---

## 5. Initializing Database Schema & Least-Privilege Application User

It is a security best practice never to use the administrative `admin` account for regular application runtime operations. We create a dedicated application user `ems_user`.

### Step 5.1: Retrieve the RDS Endpoint
1. In the AWS RDS Console, click **Databases** -> click `ems-mysql-production`.
2. Under **Connectivity & security**, copy the **Endpoint**:
   - Example: `ems-mysql-production.c123456789.us-east-1.rds.amazonaws.com`

### Step 5.2: Create the Dedicated Application User
Connect to the RDS instance using the master credentials from your terminal or MySQL Workbench:

```bash
mysql -h ems-mysql-production.c123456789.us-east-1.rds.amazonaws.com \
      -P 3306 \
      -u admin \
      -p
```

Execute the user setup and least-privilege grant statements:

```sql
-- Ensure database exists
CREATE DATABASE IF NOT EXISTS ems_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create application user with strong password
CREATE USER IF NOT EXISTS 'ems_user'@'%' IDENTIFIED BY 'REPLACE_WITH_SECURE_PASSWORD';

-- Grant least-privilege access strictly on ems_db
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER
  ON ems_db.* TO 'ems_user'@'%';

-- Enforce TLS/SSL for this user (AWS RDS supports encrypted in-transit traffic)
ALTER USER 'ems_user'@'%' REQUIRE SSL;

-- Flush privilege cache
FLUSH PRIVILEGES;

-- Verify user creation
SELECT user, host FROM mysql.user WHERE user = 'ems_user';
```

---

## 6. Configuring the Python Backend for RDS

Update the backend configuration to target the RDS instance.

### Step 6.1: Update `backend/.env`
In `backend/.env`, set the `DATABASE_URL` connection string:

```ini
APP_NAME="Employee Management System API"
APP_VERSION="1.0.0"

# Amazon RDS MySQL Connection String
DATABASE_URL="mysql+pymysql://<db_user>:<db_password>@ems-mysql-production.c123456789.us-east-1.rds.amazonaws.com:3306/ems_db?ssl_mode=PREFERRED"
```

### Step 6.2: Cloud Connection Pool Tuning
In `backend/app/database.py`, the SQLAlchemy connection pool is configured with cloud resilience settings:

```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Verifies connection health before checkout; prevents stale socket drops
    pool_recycle=300,         # Recycles connections every 5 minutes to avoid AWS NAT gateway timeouts
    pool_size=10,             # Maintains a pool of 10 connections
    max_overflow=20           # Allows temporary bursts up to 20 additional connections
)
```

### Step 6.3: Schema and data safety

Production application startup does not create tables or seed employee data.
Alembic is the only supported mechanism for schema changes. This project has
an existing employees table and no recorded Alembic baseline; adopting the
baseline and applying authentication revisions requires a separate, backed-up
schema comparison and explicit approval. Do not run `create_all()` or the
fresh-database baseline against an existing RDS database.

Do not seed demo employees in RDS or production. Demo data is available only
through the explicit SQLite development command documented in `README.md`; the
command rejects MySQL and production configuration.

---

## 7. Backend Deployment on AWS (Two Approaches)

Depending on your mentor's deployment guidelines, deploy the Python backend using either **AWS Elastic Beanstalk** (PaaS) or an **AWS EC2 Ubuntu Instance** (IaaS).

### Approach A: AWS Elastic Beanstalk (Recommended for Fast Student Setup)
Elastic Beanstalk handles provisioning, load balancing, auto-scaling, and health monitoring automatically.

1. Create a `Procfile` in `backend/`:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port 5000
   ```
2. Initialize Elastic Beanstalk application using the EB CLI:
   ```bash
   eb init -p python-3.11 ems-backend-app
   ```
3. Create the environment:
   ```bash
   eb create ems-backend-env --instance-type t3.micro
   ```
4. Set environment variables securely in Beanstalk:
   ```bash
   eb setenv DATABASE_URL="mysql+pymysql://<db_user>:<db_password>@<rds-endpoint>:3306/ems_db?ssl_mode=PREFERRED"
   ```
5. Deploy updates:
   ```bash
   eb deploy
   ```
6. Get the backend public URL:
   ```bash
   eb status
   # e.g., http://ems-backend-env.eba-xxxxxx.us-east-1.elasticbeanstalk.com
   ```

### Approach B: AWS EC2 Ubuntu 24.04 LTS (Complete Hands-on Control)
1. **Launch EC2 Instance:**
   - AMI: Ubuntu Server 24.04 LTS
   - Instance Type: `t3.micro` or `t2.micro` (Free Tier)
   - Security Group: Allow HTTP (80), HTTPS (443), and SSH (22 from your IP)
2. **Connect via SSH:**
   ```bash
   ssh -i your-key.pem ubuntu@<ec2-public-ip>
   ```
3. **Install Dependencies:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3-pip python3-venv nginx git
   ```
4. **Clone Repository & Setup Environment:**
   ```bash
   git clone https://github.com/<your-username>/employment-management.git /var/www/ems
   cd /var/www/ems/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Create Systemd Service (`/etc/systemd/system/ems.service`):**
   ```ini
   [Unit]
   Description=EMS FastAPI Application Service
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/var/www/ems/backend
   EnvironmentFile=/var/www/ems/backend/.env
   ExecStart=/var/www/ems/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
6. **Start and Enable Service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start ems
   sudo systemctl enable ems
   ```
7. **Configure Nginx as Reverse Proxy (`/etc/nginx/sites-available/ems`):**
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com <ec2-public-ip>;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
8. **Enable Nginx Configuration:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/ems /etc/nginx/sites-enabled/
   sudo rm /etc/nginx/sites-enabled/default
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## 8. Frontend Deployment on AWS (S3 + CloudFront)

React Expo Web produces a static single-page application (SPA) bundle that can be hosted on AWS S3 with global CDN caching via CloudFront.

### Step 8.1: Point Frontend to Production API URL
Before building the production bundle, update `frontend/src/services/api.ts`:

```typescript
// Replace localhost with your production Elastic Beanstalk or EC2 URL
export const API_BASE_URL = 'https://api.yourdomain.com/api'; 
// Or: 'http://ems-backend-env.eba-xxxxxx.us-east-1.elasticbeanstalk.com/api'
```

### Step 8.2: Build Static Production Assets
In the `frontend` directory:

```bash
cd "employment management/frontend"
npx expo export --platform web
```
This generates the optimized production build in `frontend/dist/` containing `index.html`, bundled JavaScript, styles, and assets.

### Step 8.3: Create and Configure S3 Bucket
1. Open the **Amazon S3 Console** -> click **Create bucket**.
2. **Bucket name:** `ems-web-portal-<your-name>` (must be globally unique).
3. **Region:** Same as your backend/RDS region.
4. **Object Ownership:** ACLs disabled (recommended).
5. **Block Public Access:** Check "Block all public access" if using CloudFront Origin Access Control (OAC), or uncheck if using public S3 static website hosting.
6. Click **Create bucket**.

### Step 8.4: Upload Dist Files to S3
Using the AWS CLI:
```bash
aws s3 sync ./dist s3://ems-web-portal-<your-name> --delete
```
Or manually drag and drop all files from `frontend/dist/` into the S3 bucket via the AWS S3 Console.

### Step 8.5: Set Up CloudFront Distribution (HTTPS & CDN)
1. In the AWS Console, navigate to **CloudFront** -> **Create distribution**.
2. **Origin domain:** Select your S3 bucket `ems-web-portal-<your-name>.s3.amazonaws.com`.
3. **Origin access:** Select **Origin Access Control (OAC)** -> Create control setting.
4. **Viewer protocol policy:** Select **Redirect HTTP to HTTPS**.
5. **Allowed HTTP methods:** GET, HEAD, OPTIONS.
6. **Default root object:** `index.html`.
7. **Error pages (SPA Routing Support):**
   - Click **Create custom error response**.
   - **HTTP error code:** `403: Forbidden` and `404: Not Found`.
   - **Customize error response:** Yes.
   - **Response page path:** `/index.html`.
   - **HTTP response code:** `200: OK`.
8. Click **Create distribution**.
9. CloudFront will provide your live secure HTTPS distribution domain:
   - Example: `https://d1234abcd5678.cloudfront.net`

---

## 9. CORS Configuration for Cloud Deployment

When the frontend is hosted on CloudFront (`https://d1234abcd5678.cloudfront.net`) and the backend is hosted on EC2 / Elastic Beanstalk, browser Cross-Origin Resource Sharing (CORS) must be configured in `backend/app/config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "https://d1234abcd5678.cloudfront.net",   # CloudFront distribution domain
    "https://ems-portal.yourdomain.com"       # Custom domain if applicable
]
```

Restart the backend service after updating `CORS_ORIGINS`.

---

## 10. Post-Deployment Verification Checklist

Execute these checks to verify end-to-end cloud operational integrity:

| Check # | Verification Step | Expected Result | Pass / Fail |
| :---: | :--- | :--- | :---: |
| 1 | `curl https://api.yourdomain.com/api/health` | Returns HTTP 200 with `status: "healthy"` and `database_driver: "pymysql"` | [ ] |
| 2 | `curl https://api.yourdomain.com/api/dashboard/stats` | Returns real-time metrics queried from AWS RDS | [ ] |
| 3 | Load CloudFront frontend URL in desktop browser | Desktop dashboard and table render with RDS data | [ ] |
| 4 | Load CloudFront frontend URL in mobile browser | Mobile card list and bottom navigation render cleanly | [ ] |
| 5 | Create new employee via frontend UI form | Employee saved in AWS RDS; appears immediately on dashboard | [ ] |
| 6 | Edit employee contact / department | Changes persist to AWS RDS and refresh in list | [ ] |
| 7 | Toggle employee status to Inactive | Status badge turns yellow; inactive counter increments | [ ] |
| 8 | CloudWatch RDS CPU & Memory Metrics | Instance utilization remains below 20% | [ ] |

---

## 11. Cost Control & Free Tier Guardrails

To ensure zero unwanted cloud expenses:

1. **RDS Instance Sizing:** Keep database at `db.t3.micro` or `db.t4g.micro` (750 hours/month included in AWS Free Tier).
2. **Storage Limit:** Keep storage at `20 GiB` General Purpose SSD.
3. **AWS Budgets:**
   - Open **AWS Billing and Cost Management** -> **Budgets**.
   - Create a monthly budget of **$1.00 USD**.
   - Set alert email to notify you if forecasted spend exceeds 80% ($0.80).
4. **Temporary Shutdown:** If not actively demonstrating or grading, you can **Stop** the RDS database from the RDS Console (stops compute charges while preserving database data).
5. **Final Project Teardown (Post-Grading):**
   - Delete CloudFront distribution.
   - Delete S3 bucket.
   - Terminate EC2 instance / Elastic Beanstalk environment.
   - Delete RDS database instance (take a final DB snapshot if you wish to archive the data).

---

## 12. Troubleshooting Common Cloud Issues

### Issue 1: Backend Hangs or Times Out Connecting to RDS
- **Cause:** VPC Security Group is blocking inbound traffic on port 3306.
- **Fix:** Verify `sg-ems-rds` allows port 3306 from your public IP (if local) or from `sg-ems-backend` (if EC2).
- **Check:** Ensure the RDS instance has **Publicly Accessible: Yes** if connecting from outside AWS.

### Issue 2: `Access denied for user 'ems_user'@'%'`
- **Cause:** Incorrect password or missing host wildcard in MySQL grant.
- **Fix:** Log in as RDS `admin` and re-run:
  ```sql
  ALTER USER 'ems_user'@'%' IDENTIFIED BY 'NEW_STRONG_PASSWORD';
  FLUSH PRIVILEGES;
  ```

### Issue 3: Frontend Shows "Network Error / Failed to fetch"
- **Cause:** CORS headers rejected by browser or incorrect `API_BASE_URL` in `frontend/src/services/api.ts`.
- **Fix:** Ensure backend `CORS_ORIGINS` includes the exact CloudFront HTTPS URL (including protocol, without trailing slash).

### Issue 4: Page Refresh on CloudFront Returns 404
- **Cause:** Single Page App routing requires routing all non-asset requests to `index.html`.
- **Fix:** In CloudFront Custom Error Pages, map HTTP 403 and 404 to `/index.html` with HTTP 200 response code.
