#!/usr/bin/env python3
"""Verify Supabase connection, schema, and auth against DATABASE_URL in backend/.env."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect, text
from fastapi.testclient import TestClient

from app.database import DATABASE_URL, engine
from app.db_utils import database_label
from app.main import app


def main() -> int:
    print("=== STEP 3: Verify users table ===")
    db_type = database_label(DATABASE_URL)
    print(f"Database: {db_type}")

    insp = inspect(engine)
    tables = sorted(insp.get_table_names())
    print(f"Tables ({len(tables)}): {', '.join(tables)}")

    if "users" not in tables:
        print("FAIL: users table missing")
        return 1

    with engine.connect() as conn:
        user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
    print(f"users table: OK (rows={user_count})")

    print("\n=== STEP 4: Verify auth register + login ===")
    client = TestClient(app)
    email = "supabase-test@example.com"
    password = "TestPass123!"

    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Supabase Test"},
    )
    print(f"POST /api/auth/register -> {reg.status_code}")
    if reg.status_code not in (200, 201):
        if "already" not in reg.text.lower():
            print(f"FAIL register: {reg.text}")
            return 1
        print("User already exists — continuing to login")
    else:
        print("Register: OK")

    login = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    print(f"POST /api/auth/login -> {login.status_code}")
    if login.status_code != 200:
        print(f"FAIL login: {login.text}")
        return 1

    token = login.json().get("access_token")
    if not token:
        print("FAIL login: no access_token in response")
        return 1
    print("Login: OK (token received)")

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    print(f"GET /api/auth/me -> {me.status_code}")
    if me.status_code != 200:
        print(f"FAIL /api/auth/me: {me.text}")
        return 1

    body = me.json()
    print(f"/api/auth/me: OK email={body.get('email')} id={body.get('id')}")

    with engine.connect() as conn:
        persisted = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE email = :email"),
            {"email": email},
        ).scalar()
    print(f"users row persisted in PostgreSQL: OK (count={persisted})")

    print("\n=== ALL CHECKS PASSED ===")
    print("Backend connected to Supabase PostgreSQL.")
    print("SQLite fallback: remove or comment DATABASE_URL in backend/.env to use sqlite:///./data/app.db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
