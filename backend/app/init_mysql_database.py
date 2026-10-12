"""Secure Terminal-Based MySQL Database and Application User Initialization Script

Prompts for the MySQL root password through a standard, visible, masked terminal prompt.
1. Connects as root to create the dedicated 'ems_db' database.
2. Auto-generates a secure credential for the least-privileged user 'ems_user'@'localhost'.
3. Grants privileges strictly on 'ems_db'.* to 'ems_user'.
4. Securely writes backend/.env (never prints or exposes passwords).
5. Migrates the six canonical employee records from SQLite into MySQL.
"""

import getpass
import secrets
import string
import sys
import os
from pathlib import Path
import pymysql

backend_dir = Path(__file__).resolve().parent.parent
env_file_path = backend_dir / ".env"


def generate_secure_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def setup_mysql():
    print("=" * 60)
    print("EMS: Secure Local MySQL Database Setup & Migration")
    print("=" * 60)

    # 1. Normal, visible, masked terminal prompt
    root_password = getpass.getpass("Enter MySQL root password: ")
    if not root_password:
        print("❌ Error: Password cannot be empty. Aborting.")
        return False

    # 2. Auto-generate secure password for application user
    app_user_password = generate_secure_password()
    print("✓ Secure random credential generated for application user 'ems_user'.")

    # 3. Connect as root to configure database and user
    print("\nConnecting to MySQL Server (localhost:3306) as root...")
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password=root_password,
            port=3306,
            autocommit=True,
        )
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

    try:
        with connection.cursor() as cursor:
            # Create dedicated EMS database
            print("1. Creating database 'ems_db' (if not exists)...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS `ems_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")

            # Create least-privileged application user
            print("2. Configuring user 'ems_user'@'localhost'...")
            cursor.execute("CREATE USER IF NOT EXISTS 'ems_user'@'localhost' IDENTIFIED BY %s;", (app_user_password,))
            cursor.execute("ALTER USER 'ems_user'@'localhost' IDENTIFIED BY %s;", (app_user_password,))

            # Grant privileges strictly on ems_db.*
            print("3. Granting privileges on 'ems_db.*' to 'ems_user'...")
            cursor.execute("GRANT ALL PRIVILEGES ON `ems_db`.* TO 'ems_user'@'localhost';")
            cursor.execute("FLUSH PRIVILEGES;")

        print("✓ Dedicated database and least-privileged user configured successfully.")
    finally:
        connection.close()

    # 4. Write backend/.env securely
    print("\n4. Writing database configuration to backend/.env...")
    mysql_url = f"mysql+pymysql://ems_user:{app_user_password}@localhost:3306/ems_db"
    env_content = f"""# Employee Management System - Environment Configuration
APP_NAME="Employee Management System API"
APP_VERSION="1.0.0"

DATABASE_URL="{mysql_url}"
"""
    with open(env_file_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    print("✓ backend/.env written successfully (excluded from Git).")

    # 5. Run data migration from SQLite to MySQL
    print("\n5. Migrating six canonical employee records from SQLite to MySQL...")
    from app.migrate_to_mysql import run_migration
    migration_success = run_migration(mysql_url)

    if migration_success:
        print("\n" + "=" * 60)
        print("✅ SUCCESS: MySQL database and records migrated cleanly!")
        print("=" * 60)
        return True
    else:
        print("\n❌ Data migration failed.")
        return False


if __name__ == "__main__":
    success = setup_mysql()
    sys.exit(0 if success else 1)
