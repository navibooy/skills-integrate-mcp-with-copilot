"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

DB_PATH = current_dir / "activities.db"

INITIAL_ACTIVITIES = [
    {
        "name": "Chess Club",
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    {
        "name": "Programming Class",
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    {
        "name": "Gym Class",
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    {
        "name": "Soccer Team",
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    {
        "name": "Basketball Team",
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    {
        "name": "Art Club",
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    {
        "name": "Drama Club",
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    {
        "name": "Math Club",
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    {
        "name": "Debate Team",
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                UNIQUE(activity_id, email),
                FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE
            )
            """
        )

        existing_count = conn.execute(
            "SELECT COUNT(*) AS count FROM activities"
        ).fetchone()["count"]

        if existing_count == 0:
            for activity in INITIAL_ACTIVITIES:
                cursor = conn.execute(
                    """
                    INSERT INTO activities (name, description, schedule, max_participants)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        activity["name"],
                        activity["description"],
                        activity["schedule"],
                        activity["max_participants"],
                    ),
                )
                activity_id = cursor.lastrowid

                for email in activity["participants"]:
                    conn.execute(
                        "INSERT INTO participants (activity_id, email) VALUES (?, ?)",
                        (activity_id, email),
                    )


def get_activity_by_name(conn: sqlite3.Connection, activity_name: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, name, description, schedule, max_participants FROM activities WHERE name = ?",
        (activity_name,),
    ).fetchone()


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with get_connection() as conn:
        activity_rows = conn.execute(
            "SELECT id, name, description, schedule, max_participants FROM activities ORDER BY id"
        ).fetchall()

        activities = {
            row["name"]: {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": [],
            }
            for row in activity_rows
        }

        participant_rows = conn.execute(
            """
            SELECT a.name, p.email
            FROM participants p
            JOIN activities a ON a.id = p.activity_id
            ORDER BY p.id
            """
        ).fetchall()

        for row in participant_rows:
            activities[row["name"]]["participants"].append(row["email"])

        return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with get_connection() as conn:
        activity = get_activity_by_name(conn, activity_name)
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        existing = conn.execute(
            "SELECT 1 FROM participants WHERE activity_id = ? AND email = ?",
            (activity["id"], email),
        ).fetchone()
        if existing is not None:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        conn.execute(
            "INSERT INTO participants (activity_id, email) VALUES (?, ?)",
            (activity["id"], email),
        )

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with get_connection() as conn:
        activity = get_activity_by_name(conn, activity_name)
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        cursor = conn.execute(
            "DELETE FROM participants WHERE activity_id = ? AND email = ?",
            (activity["id"], email),
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity",
            )

    return {"message": f"Unregistered {email} from {activity_name}"}
