from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Sequence


DB_PATH = Path(__file__).with_name("exercises.db")

GOALS = (
    "muscle_building",
    "weight_loss",
    "strength_increase",
    "endurance_increase",
)


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create a connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Create tables to store exercises and per-goal recommendations."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            performed_at TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workout_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            FOREIGN KEY (workout_id) REFERENCES workouts (id) ON DELETE CASCADE
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT,
            short_description TEXT NOT NULL,
            required_equipment TEXT NOT NULL,
            target_muscle_group TEXT NOT NULL
        );
        """
    )
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS goal_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            goal TEXT NOT NULL CHECK (goal IN {GOALS}),
            suitability_rating INTEGER NOT NULL CHECK (suitability_rating BETWEEN 1 AND 10),
            recommended_sets INTEGER,
            recommended_reps_per_set INTEGER,
            recommended_time_seconds INTEGER,
            UNIQUE (exercise_id, goal),
            FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()


def seed_sample_data(conn: sqlite3.Connection) -> None:
    """
    Seed a handful of exercises with per-goal recommendations.

    The seed step is skipped when rows are already present so reruns remain safe.
    """
    existing = conn.execute("SELECT COUNT(*) FROM exercises;").fetchone()[0]
    if existing:
        return

    exercises = [
        {
            "name": "Push-Up",
            "icon": "push_up",
            "short_description": "Bodyweight push for chest, shoulders, and triceps.",
            "required_equipment": "Bodyweight (mat optional)",
            "target_muscle_group": "Chest, shoulders, triceps",
            "recommendations": {
                "muscle_building": {
                    "suitability_rating": 8,
                    "recommended_sets": 4,
                    "recommended_reps_per_set": 10,
                    "recommended_time_seconds": None,
                },
                "weight_loss": {
                    "suitability_rating": 7,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": 15,
                    "recommended_time_seconds": None,
                },
                "strength_increase": {
                    "suitability_rating": 8,
                    "recommended_sets": 5,
                    "recommended_reps_per_set": 6,
                    "recommended_time_seconds": None,
                },
                "endurance_increase": {
                    "suitability_rating": 6,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": 20,
                    "recommended_time_seconds": None,
                },
            },
        },
        {
            "name": "Barbell Deadlift",
            "icon": "barbell_deadlift",
            "short_description": "Compound lift targeting the posterior chain and grip strength.",
            "required_equipment": "Barbell, plates",
            "target_muscle_group": "Posterior chain",
            "recommendations": {
                "muscle_building": {
                    "suitability_rating": 9,
                    "recommended_sets": 4,
                    "recommended_reps_per_set": 8,
                    "recommended_time_seconds": None,
                },
                "weight_loss": {
                    "suitability_rating": 6,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": 12,
                    "recommended_time_seconds": None,
                },
                "strength_increase": {
                    "suitability_rating": 10,
                    "recommended_sets": 5,
                    "recommended_reps_per_set": 5,
                    "recommended_time_seconds": None,
                },
                "endurance_increase": {
                    "suitability_rating": 5,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": 10,
                    "recommended_time_seconds": None,
                },
            },
        },
        {
            "name": "Plank",
            "icon": "plank",
            "short_description": "Isometric core hold improving trunk stability.",
            "required_equipment": "Mat (optional)",
            "target_muscle_group": "Core",
            "recommendations": {
                "muscle_building": {
                    "suitability_rating": 6,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": None,
                    "recommended_time_seconds": 45,
                },
                "weight_loss": {
                    "suitability_rating": 7,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": None,
                    "recommended_time_seconds": 60,
                },
                "strength_increase": {
                    "suitability_rating": 5,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": None,
                    "recommended_time_seconds": 30,
                },
                "endurance_increase": {
                    "suitability_rating": 9,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": None,
                    "recommended_time_seconds": 90,
                },
            },
        },
        {
            "name": "Jump Rope",
            "icon": "jump_rope",
            "short_description": "Rhythmic skipping for cardio conditioning and calf endurance.",
            "required_equipment": "Jump rope",
            "target_muscle_group": "Full body with calves focus",
            "recommendations": {
                "muscle_building": {
                    "suitability_rating": 5,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": None,
                    "recommended_time_seconds": 60,
                },
                "weight_loss": {
                    "suitability_rating": 9,
                    "recommended_sets": 5,
                    "recommended_reps_per_set": None,
                    "recommended_time_seconds": 90,
                },
                "strength_increase": {
                    "suitability_rating": 4,
                    "recommended_sets": 3,
                    "recommended_reps_per_set": None,
                    "recommended_time_seconds": 60,
                },
                "endurance_increase": {
                    "suitability_rating": 10,
                    "recommended_sets": 4,
                    "recommended_reps_per_set": None,
                    "recommended_time_seconds": 120,
                },
            },
        },
    ]

    exercise_stmt = """
        INSERT INTO exercises (
            name, icon, short_description, required_equipment, target_muscle_group
        )
        VALUES (?, ?, ?, ?, ?);
    """
    recommendation_stmt = """
        INSERT INTO goal_recommendations (
            exercise_id,
            goal,
            suitability_rating,
            recommended_sets,
            recommended_reps_per_set,
            recommended_time_seconds
        )
        VALUES (?, ?, ?, ?, ?, ?);
    """

    for exercise in exercises:
        cursor = conn.execute(
            exercise_stmt,
            (
                exercise["name"],
                exercise["icon"],
                exercise["short_description"],
                exercise["required_equipment"],
                exercise["target_muscle_group"],
            ),
        )
        exercise_id = cursor.lastrowid

        for goal, recommendation in exercise["recommendations"].items():
            conn.execute(
                recommendation_stmt,
                (
                    exercise_id,
                    goal,
                    recommendation["suitability_rating"],
                    recommendation.get("recommended_sets"),
                    recommendation.get("recommended_reps_per_set"),
                    recommendation.get("recommended_time_seconds"),
                ),
            )

    conn.commit()


def initialize_database(db_path: Optional[Path] = None) -> Path:
    """Create the SQLite database file with schema and seed data."""
    target_path = db_path or DB_PATH
    with get_connection(target_path) as conn:
        create_schema(conn)
        seed_sample_data(conn)
    return target_path


def fetch_all(conn: sqlite3.Connection) -> list[tuple]:
    """Helper for quick manual inspection when debugging."""
    return conn.execute(
        """
        SELECT e.name, e.icon, e.short_description, e.required_equipment, e.target_muscle_group,
               r.goal, r.suitability_rating, r.recommended_sets,
               r.recommended_reps_per_set, r.recommended_time_seconds
        FROM exercises e
        JOIN goal_recommendations r ON e.id = r.exercise_id
        ORDER BY e.name, r.goal;
        """
    ).fetchall()


def add_exercise(
    *,
    name: str,
    short_description: str,
    required_equipment: str,
    target_muscle_group: str,
    goal: str,
    suitability_rating: int,
    recommended_sets: Optional[int] = None,
    recommended_reps_per_set: Optional[int] = None,
    recommended_time_seconds: Optional[int] = None,
    icon: str = "",
    db_path: Path = DB_PATH,
) -> int:
    """
    Insert a new exercise and a single goal recommendation. Returns new exercise id.

    The database constraints enforce goal membership and rating range.
    """
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO exercises (name, icon, short_description, required_equipment, target_muscle_group)
            VALUES (?, ?, ?, ?, ?);
            """,
            (name, icon, short_description, required_equipment, target_muscle_group),
        )
        exercise_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO goal_recommendations (
                exercise_id,
                goal,
                suitability_rating,
                recommended_sets,
                recommended_reps_per_set,
                recommended_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                exercise_id,
                goal,
                suitability_rating,
                recommended_sets,
                recommended_reps_per_set,
                recommended_time_seconds,
            ),
        )
        conn.commit()
        return exercise_id


def add_user(username: str, *, db_path: Path = DB_PATH) -> int:
    """Register a new user and return the user id."""
    username = username.strip()
    if not username:
        raise ValueError("Username is required.")
    with get_connection(db_path) as conn:
        cursor = conn.execute("INSERT INTO users (username) VALUES (?);", (username,))
        conn.commit()
        return cursor.lastrowid


def fetch_users(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    """Return a list of user ids and usernames."""
    return conn.execute("SELECT id, username FROM users ORDER BY username;").fetchall()


def log_workout(
    *,
    user_id: int,
    performed_at: str,
    duration_minutes: int,
    exercises: Sequence[str],
    db_path: Path = DB_PATH,
) -> int:
    """Persist a completed workout for a user and return the workout id."""
    if duration_minutes <= 0:
        raise ValueError("Duration must be positive.")
    cleaned_exercises = [ex.strip() for ex in exercises if ex.strip()]
    if not cleaned_exercises:
        raise ValueError("At least one exercise is required.")

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO workouts (user_id, performed_at, duration_minutes)
            VALUES (?, ?, ?);
            """,
            (user_id, performed_at, duration_minutes),
        )
        workout_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO workout_exercises (workout_id, exercise_name) VALUES (?, ?);",
            [(workout_id, ex) for ex in cleaned_exercises],
        )
        conn.commit()
        return workout_id


def fetch_workout_history(
    user_id: int,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> list[dict[str, object]]:
    """
    Return workouts for a user with exercises aggregated per session.

    Dates are compared using SQLite's date() to respect YYYY-MM-DD strings.
    """
    query = """
        SELECT w.id, w.performed_at, w.duration_minutes, we.exercise_name
        FROM workouts w
        LEFT JOIN workout_exercises we ON w.id = we.workout_id
        WHERE w.user_id = ?
    """
    params: list[object] = [user_id]
    if start_date:
        query += " AND date(w.performed_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(w.performed_at) <= date(?)"
        params.append(end_date)
    query += " ORDER BY w.performed_at DESC, w.id DESC;"

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

    grouped: dict[int, dict[str, object]] = {}
    for workout_id, performed_at, duration_minutes, exercise_name in rows:
        entry = grouped.setdefault(
            workout_id,
            {
                "workout_id": workout_id,
                "performed_at": performed_at,
                "duration_minutes": duration_minutes,
                "exercises": [],
            },
        )
        if exercise_name:
            entry["exercises"].append(exercise_name)
    return list(grouped.values())


def fetch_workout_stats(
    user_id: int,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> dict[str, object]:
    """Aggregate stats for a user's workouts."""
    stats = {
        "total_workouts": 0,
        "total_minutes": 0,
        "top_exercise": None,
        "top_exercise_count": 0,
    }

    filters = ["user_id = ?"]
    params: list[object] = [user_id]
    if start_date:
        filters.append("date(performed_at) >= date(?)")
        params.append(start_date)
    if end_date:
        filters.append("date(performed_at) <= date(?)")
        params.append(end_date)
    filter_clause = " AND ".join(filters)

    with get_connection(db_path) as conn:
        total_row = conn.execute(
            f"""
            SELECT COUNT(*), COALESCE(SUM(duration_minutes), 0)
            FROM workouts
            WHERE {filter_clause};
            """,
            params,
        ).fetchone()
        stats["total_workouts"] = total_row[0]
        stats["total_minutes"] = total_row[1]

        top_row = conn.execute(
            f"""
            SELECT we.exercise_name, COUNT(*) AS cnt
            FROM workouts w
            JOIN workout_exercises we ON w.id = we.workout_id
            WHERE {filter_clause}
            GROUP BY we.exercise_name
            ORDER BY cnt DESC, we.exercise_name ASC
            LIMIT 1;
            """,
            params,
        ).fetchone()
        if top_row:
            stats["top_exercise"] = top_row[0]
            stats["top_exercise_count"] = top_row[1]
    return stats


def fetch_recent_exercise_usage(
    user_id: int,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    db_path: Path = DB_PATH,
) -> list[tuple[str, str]]:
    """
    Return a list of (exercise_name, performed_at) sorted from newest to oldest.

    Used to bias recommendations toward less recently performed movements.
    """
    filters = ["w.user_id = ?"]
    params: list[object] = [user_id]
    if start_date:
        filters.append("date(w.performed_at) >= date(?)")
        params.append(start_date)
    if end_date:
        filters.append("date(w.performed_at) <= date(?)")
        params.append(end_date)
    filter_clause = " AND ".join(filters)

    with get_connection(db_path) as conn:
        rows = conn.execute(
            f"""
            SELECT we.exercise_name, w.performed_at
            FROM workouts w
            JOIN workout_exercises we ON w.id = we.workout_id
            WHERE {filter_clause}
            ORDER BY w.performed_at DESC
            LIMIT ?;
            """,
            (*params, limit),
        ).fetchall()
    return rows


if __name__ == "__main__":
    path = initialize_database()
    print(f"Database ready at {path.resolve()}")
