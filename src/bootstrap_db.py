"""Utility script to initialize or reset the SQLite database."""

from pathlib import Path
import sqlite3

from app import DB_PATH, INITIAL_ACTIVITIES, initialize_database


def reset_database() -> None:
    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()

    initialize_database()


def print_summary() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        activities = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
        participants = conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0]

    print(f"Database ready at: {DB_PATH}")
    print(f"Seeded activities: {activities} (expected {len(INITIAL_ACTIVITIES)})")
    print(f"Seeded participants: {participants}")


if __name__ == "__main__":
    reset_database()
    print_summary()
