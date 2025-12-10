from __future__ import annotations

from typing import Any

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

import exercise_database

KV = """
#:import dp kivy.metrics.dp

<FilterLabel@Label>:
    color: 0.2, 0.2, 0.25, 1
    font_size: "13sp"
    size_hint_y: None
    height: dp(18)
    text_size: self.size
    valign: "middle"

<ExerciseCard>:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(6)
    size_hint_y: None
    height: self.minimum_height
    canvas.before:
        Color:
            rgba: 0.96, 0.97, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8,]
    Label:
        text: root.name
        font_size: "18sp"
        bold: True
        color: 0.1, 0.12, 0.2, 1
        text_size: self.width, None
        halign: "left"
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: root.description
        color: 0.2, 0.2, 0.24, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: "Goal suitability: {} ({})".format(root.goal_label, root.suitability_display)
        color: 0.2, 0.2, 0.3, 1
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
    BoxLayout:
        spacing: dp(10)
        size_hint_y: None
        height: dp(22)
        Label:
            text: "Muscle: {}".format(root.muscle_group)
            color: 0.15, 0.15, 0.2, 1
        Label:
            text: "Equipment: {}".format(root.equipment)
            color: 0.15, 0.15, 0.2, 1
    Label:
        text: "Recommendation: {}".format(root.recommendation)
        color: 0.2, 0.2, 0.28, 1
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None

<RootWidget>:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.98, 0.98, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(70)
        spacing: dp(12)
        GridLayout:
            cols: 3
            spacing: dp(8)
            row_default_height: dp(26)
            size_hint_y: None
            height: self.minimum_height
            FilterLabel:
                text: "Target suitability"
            FilterLabel:
                text: "Muscle group"
            FilterLabel:
                text: "Required equipment"
            Spinner:
                id: goal_spinner
                text: root.goal_spinner_text
                values: root.goal_options
                on_text: root.on_goal_change(self.text)
                size_hint_x: 1
            Spinner:
                id: muscle_spinner
                text: root.muscle_spinner_text
                values: root.muscle_options
                on_text: root.on_muscle_change(self.text)
            Spinner:
                id: equipment_spinner
                text: root.equipment_spinner_text
                values: root.equipment_options
                on_text: root.on_equipment_change(self.text)
    RecycleView:
        id: exercise_list
        viewclass: "ExerciseCard"
        bar_width: dp(6)
        scroll_type: ['bars', 'content']
        RecycleBoxLayout:
            default_size: None, dp(170)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: "vertical"
            spacing: dp(10)
"""


class ExerciseCard(BoxLayout):
    name = StringProperty()
    description = StringProperty()
    goal_label = StringProperty()
    muscle_group = StringProperty()
    equipment = StringProperty()
    suitability_display = StringProperty()
    recommendation = StringProperty()


class RootWidget(BoxLayout):
    goal_options = ListProperty()
    muscle_options = ListProperty()
    equipment_options = ListProperty()

    goal_spinner_text = StringProperty("All goals")
    muscle_spinner_text = StringProperty("All muscle groups")
    equipment_spinner_text = StringProperty("All equipment")

    filter_goal = StringProperty("All")
    filter_muscle_group = StringProperty("All")
    filter_equipment = StringProperty("All")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.records = []
        self._goal_label_map = {self._pretty_goal(goal): goal for goal in exercise_database.GOALS}
        Clock.schedule_once(self._bootstrap_data, 0)

    def _pretty_goal(self, goal: str) -> str:
        return goal.replace("_", " ").title()

    def _bootstrap_data(self, *_: Any) -> None:
        self.records = self._load_records()
        self.goal_options = ["All goals"] + list(self._goal_label_map.keys())
        self.muscle_options = ["All muscle groups"] + sorted({r["muscle_group"] for r in self.records})
        self.equipment_options = ["All equipment"] + sorted({r["equipment"] for r in self.records})
        self.apply_filters()

    def _load_records(self):
        with exercise_database.get_connection() as conn:
            rows = exercise_database.fetch_all(conn)
        records = []
        for (
            name,
            icon,
            description,
            equipment,
            muscle_group,
            goal,
            rating,
            sets,
            reps,
            time_seconds,
        ) in rows:
            recommendation_parts = []
            if sets is not None and reps is not None:
                recommendation_parts.append(f"{sets} sets x {reps} reps")
            elif sets is not None:
                recommendation_parts.append(f"{sets} sets")
            if time_seconds is not None:
                recommendation_parts.append(f"{time_seconds}s hold")
            recommendation = " • ".join(recommendation_parts) if recommendation_parts else "Adjust volume to preference"
            records.append(
                {
                    "name": name,
                    "description": description,
                    "equipment": equipment,
                    "muscle_group": muscle_group,
                    "goal": goal,
                    "goal_label": self._pretty_goal(goal),
                    "suitability_display": f"{rating}/10",
                    "recommendation": recommendation,
                }
            )
        return records

    def on_goal_change(self, value: str) -> None:
        self.filter_goal = "All" if value == "All goals" else self._goal_label_map.get(value, "All")
        self.goal_spinner_text = value
        self.apply_filters()

    def on_muscle_change(self, value: str) -> None:
        self.filter_muscle_group = "All" if value == "All muscle groups" else value
        self.muscle_spinner_text = value
        self.apply_filters()

    def on_equipment_change(self, value: str) -> None:
        self.filter_equipment = "All" if value == "All equipment" else value
        self.equipment_spinner_text = value
        self.apply_filters()

    def apply_filters(self) -> None:
        filtered = []
        for record in self.records:
            if self.filter_goal != "All" and record["goal"] != self.filter_goal:
                continue
            if self.filter_muscle_group != "All" and record["muscle_group"] != self.filter_muscle_group:
                continue
            if self.filter_equipment != "All" and record["equipment"] != self.filter_equipment:
                continue
            filtered.append(
                {
                    "name": record["name"],
                    "description": record["description"],
                    "goal_label": record["goal_label"],
                    "muscle_group": record["muscle_group"],
                    "equipment": record["equipment"],
                    "suitability_display": record["suitability_display"],
                    "recommendation": record["recommendation"],
                }
            )
        self.ids.exercise_list.data = filtered


class ExerciseApp(App):
    def build(self):
        exercise_database.initialize_database()
        Builder.load_string(KV)
        return RootWidget()


if __name__ == "__main__":
    ExerciseApp().run()
