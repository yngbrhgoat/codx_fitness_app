from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


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


if __name__ == "__main__":
    path = initialize_database()
    print(f"Database ready at {path.resolve()}")
