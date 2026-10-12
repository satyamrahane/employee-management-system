from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("DELETE FROM employees WHERE employee_code LIKE 'TEST-%'"))
    conn.commit()
    rows = conn.execute(text("SELECT employee_code, first_name, last_name, department, employment_status FROM employees ORDER BY employee_code")).fetchall()
    print(f"Total employees: {len(rows)}")
    for r in rows:
        print(f"  {r[0]}: {r[1]} {r[2]} | {r[3]} | {r[4]}")
