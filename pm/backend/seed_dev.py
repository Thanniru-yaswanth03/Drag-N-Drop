"""Explicit Developer Seeding Script.

Run this script manually ONLY when you want to seed development mock data:
    python pm/backend/seed_dev.py

This script is NEVER executed during production startup.
"""
from pathlib import Path
import sys

# Add current dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import database

def seed():
    print("Initializing database schema...")
    database.init_db()

    demo_users = [
        ("user", "password"),
        ("yash", "password"),
        ("alice", "password123"),
        ("bob", "password123"),
    ]

    for username, password in demo_users:
        print(f"Registering demo user: {username}...")
        res = database.register_user(username, password)
        if not res.get("success"):
            print(f"  User {username} already exists or error: {res.get('error')}")
        else:
            print(f"  User {username} created with initial board.")

    print("\nDev seeding complete.")

if __name__ == "__main__":
    seed()
