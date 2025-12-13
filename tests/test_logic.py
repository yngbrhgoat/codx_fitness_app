import os
import tempfile
import unittest
from pathlib import Path

# Keep Kivy quiet and headless during logic tests before importing Kivy modules.
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_WINDOW", "mock")
os.environ.setdefault("KIVY_NO_FILELOG", "1")

import exercise_database
from main import RootWidget


class RecommendationLogicTests(unittest.TestCase):
    def test_score_recommendation_recency_bonus(self) -> None:
        dummy = object()
        cases = [
            (None, 7.0),
            (20, 6.0),
            (10, 5.5),
            (2, 4.0),
            (5, 5.0),
        ]
        for recency, expected in cases:
            score = RootWidget._score_recommendation(dummy, {"rating": 5}, recency)  # type: ignore[arg-type]
            self.assertEqual(score, expected)

    def test_estimate_minutes_prefers_time_then_volume(self) -> None:
        dummy = object()
        time_first = RootWidget._estimate_minutes(dummy, {"time_seconds": 125, "sets": 2, "reps": 10})
        volume_based = RootWidget._estimate_minutes(dummy, {"sets": 3, "reps": 10})
        sets_only = RootWidget._estimate_minutes(dummy, {"sets": 3})
        fallback = RootWidget._estimate_minutes(dummy, {})

        self.assertEqual(time_first, 3)  # ceil(125s)
        self.assertEqual(volume_based, 2)  # 3*10*4 = 120s
        self.assertEqual(sets_only, 2)  # 3*30s default
        self.assertEqual(fallback, 5)

    def test_completion_percentage_clamped_and_rounded(self) -> None:
        dummy = object()
        self.assertEqual(RootWidget._compute_completion_percentage(dummy, 0, 4), 0.0)
        self.assertEqual(RootWidget._compute_completion_percentage(dummy, 3, 4), 75.0)
        self.assertEqual(RootWidget._compute_completion_percentage(dummy, 6, 4), 100.0)  # capped at 100%

    def test_tempo_hint_for_reps_rest_and_hold(self) -> None:
        # Build a lightweight stub that satisfies _update_tempo_hint requirements.
        class TempoStub:
            pass

        stub = TempoStub()
        stub.live_exercises = [{"name": "Push-Up", "reps": 10}]
        stub._live_current_index = 0
        stub._live_set_target_seconds = 40
        stub._live_set_elapsed = 12
        stub._live_phase = "set"
        stub.live_tempo_hint = ""

        def current_exercise():
            if 0 <= stub._live_current_index < len(stub.live_exercises):
                return stub.live_exercises[stub._live_current_index]
            return None

        stub._current_live_exercise = current_exercise
        RootWidget._update_tempo_hint(stub)
        self.assertIn("repetition 4", stub.live_tempo_hint)

        # Rest phase
        stub._live_phase = "rest"
        RootWidget._update_tempo_hint(stub)
        self.assertIn("Rest and breathe", stub.live_tempo_hint)

        # Time-based hold
        stub.live_exercises = [{"name": "Plank", "time_seconds": 30}]
        stub._live_phase = "set"
        stub._live_set_target_seconds = 30
        stub._live_set_elapsed = 10
        RootWidget._update_tempo_hint(stub)
        self.assertIn("10s of 30s", stub.live_tempo_hint)


class HistoryAndStatsTests(unittest.TestCase):
    def test_history_filtering_by_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            exercise_database.initialize_database(db_path)
            user_id = exercise_database.add_user("alice", db_path=db_path)
            exercise_database.log_workout(
                user_id=user_id,
                performed_at="2024-01-01",
                duration_minutes=30,
                exercises=["Push-Up"],
                db_path=db_path,
            )
            exercise_database.log_workout(
                user_id=user_id,
                performed_at="2024-02-15",
                duration_minutes=40,
                exercises=["Squat"],
                db_path=db_path,
            )

            jan_entries = exercise_database.fetch_workout_history(
                user_id,
                end_date="2024-01-31",
                db_path=db_path,
            )
            feb_entries = exercise_database.fetch_workout_history(
                user_id,
                start_date="2024-02-01",
                db_path=db_path,
            )

            self.assertEqual(len(jan_entries), 1)
            self.assertEqual(jan_entries[0]["performed_at"], "2024-01-01")
            self.assertEqual(len(feb_entries), 1)
            self.assertEqual(feb_entries[0]["performed_at"], "2024-02-15")

    def test_stats_aggregate_and_top_exercise(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            exercise_database.initialize_database(db_path)
            user_id = exercise_database.add_user("bob", db_path=db_path)
            exercise_database.log_workout(
                user_id=user_id,
                performed_at="2024-03-01",
                duration_minutes=20,
                exercises=["Jump Rope", "Push-Up"],
                db_path=db_path,
            )
            exercise_database.log_workout(
                user_id=user_id,
                performed_at="2024-03-02",
                duration_minutes=25,
                exercises=["Jump Rope"],
                db_path=db_path,
            )

            stats = exercise_database.fetch_workout_stats(user_id, db_path=db_path)
            self.assertEqual(stats["total_workouts"], 2)
            self.assertEqual(stats["total_minutes"], 45)
            self.assertEqual(stats["top_exercise"], "Jump Rope")
            self.assertEqual(stats["top_exercise_count"], 2)


if __name__ == "__main__":
    unittest.main()
