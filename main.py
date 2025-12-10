from __future__ import annotations

import sqlite3
from typing import Any, Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

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

<HomeScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(20)
        spacing: dp(16)
        Label:
            text: "Welcome to the Exercise Manager"
            font_size: "20sp"
            bold: True
            color: 0.12, 0.14, 0.22, 1
            size_hint_y: None
            height: dp(30)
        Label:
            text: "Choose what you want to do"
            color: 0.2, 0.2, 0.3, 1
            size_hint_y: None
            height: dp(22)
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            spacing: dp(12)
            Button:
                text: "Browse exercises"
                on_release: app.root.go_browse()
            Button:
                text: "Add a new exercise"
                on_release: app.root.go_add()

<BrowseScreen>:
    BoxLayout:
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
                    text: app.root.goal_spinner_text
                    values: app.root.goal_options
                    on_text: app.root.on_goal_change(self.text)
                    size_hint_x: 1
                Spinner:
                    id: muscle_spinner
                    text: app.root.muscle_spinner_text
                    values: app.root.muscle_options
                    on_text: app.root.on_muscle_change(self.text)
                Spinner:
                    id: equipment_spinner
                    text: app.root.equipment_spinner_text
                    values: app.root.equipment_options
                    on_text: app.root.on_equipment_change(self.text)
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

<AddScreen>:
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            padding: dp(12)
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height
            canvas.before:
                Color:
                    rgba: 0.98, 0.98, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "Add a new exercise"
                bold: True
                color: 0.12, 0.14, 0.25, 1
                size_hint_y: None
                height: dp(22)
            Label:
                text: "Defaults: rating 5. Optional fields default to empty."
                color: 0.2, 0.2, 0.28, 1
                size_hint_y: None
                height: dp(20)
            GridLayout:
                cols: 2
                spacing: dp(8)
                row_default_height: dp(34)
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "Name"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: name_input
                    multiline: False
                    hint_text: "e.g. Bulgarian Split Squat"
                Label:
                    text: "Description"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: description_input
                    multiline: True
                    size_hint_y: None
                    height: dp(64)
                    hint_text: "Short overview"
                Label:
                    text: "Muscle group (choose known)"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: muscle_add_spinner
                    text: app.root.add_muscle_spinner_text
                    values: app.root.muscle_choice_options
                    on_text: app.root.add_muscle_spinner_text = self.text
                Label:
                    text: "Allowed muscle groups"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.muscle_choice_display
                    color: 0.2, 0.2, 0.28, 1
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]
                Label:
                    text: "Required equipment"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: equipment_add_spinner
                    text: app.root.add_equipment_spinner_text
                    values: app.root.equipment_choice_options
                    on_text: app.root.add_equipment_spinner_text = self.text
                Label:
                    text: "Allowed equipment"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.equipment_choice_display
                    color: 0.2, 0.2, 0.28, 1
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]
                Label:
                    text: "Equipment default"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.add_equipment_spinner_text or "Bodyweight"
                    color: 0.2, 0.2, 0.28, 1
                    size_hint_y: None
                    height: dp(18)
                Label:
                    text: "Target suitability goal"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: goal_add_spinner
                    text: app.root.add_goal_spinner_text
                    values: app.root.goal_choice_options
                    on_text: app.root.add_goal_spinner_text = self.text
                Label:
                    text: "Suitability rating (1-10, default 5)"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: rating_spinner
                    text: app.root.rating_spinner_text
                    values: ("1","2","3","4","5","6","7","8","9","10")
                Label:
                    text: "Recommended sets (optional)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: sets_input
                    multiline: False
                    input_filter: "int"
                    hint_text: "blank -> stored as NULL"
                Label:
                    text: "Recommended reps (optional)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: reps_input
                    multiline: False
                    input_filter: "int"
                    hint_text: "blank -> stored as NULL"
                Label:
                    text: "Recommended time (sec, optional)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: time_input
                    multiline: False
                    input_filter: "int"
                    hint_text: "blank -> stored as NULL"
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(10)
                Button:
                    text: "Add Exercise"
                    on_press: app.root.handle_add_exercise()
            Label:
                text: app.root.status_text
                color: app.root.status_color
                size_hint_y: None
                height: dp(18)

<RootWidget>:
    orientation: "vertical"
    canvas.before:
        Color:
            rgba: 0.98, 0.98, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        padding: dp(10), dp(6)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 0.94, 0.95, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "Exercise Manager"
            font_size: "18sp"
            bold: True
            color: 0.1, 0.12, 0.2, 1
        Widget:
        Button:
            text: "Home"
            size_hint_x: None
            width: dp(90)
            on_release: root.go_home()
        Button:
            text: "Browse"
            size_hint_x: None
            width: dp(90)
            on_release: root.go_browse()
        Button:
            text: "Add"
            size_hint_x: None
            width: dp(90)
            on_release: root.go_add()

    ScreenManager:
        id: screen_manager
        HomeScreen:
            name: "home"
        BrowseScreen:
            name: "browse"
        AddScreen:
            name: "add"
"""


class ExerciseCard(BoxLayout):
    name = StringProperty()
    description = StringProperty()
    goal_label = StringProperty()
    muscle_group = StringProperty()
    equipment = StringProperty()
    suitability_display = StringProperty()
    recommendation = StringProperty()


class HomeScreen(Screen):
    pass


class BrowseScreen(Screen):
    pass


class AddScreen(Screen):
    pass


class RootWidget(BoxLayout):
    goal_options = ListProperty()
    goal_choice_options = ListProperty()
    muscle_choice_options = ListProperty()
    equipment_choice_options = ListProperty()
    muscle_options = ListProperty()
    equipment_options = ListProperty()

    goal_spinner_text = StringProperty("All goals")
    muscle_spinner_text = StringProperty("All muscle groups")
    equipment_spinner_text = StringProperty("All equipment")
    add_goal_spinner_text = StringProperty("")
    add_muscle_spinner_text = StringProperty("")
    add_equipment_spinner_text = StringProperty("")
    rating_spinner_text = StringProperty("5")

    filter_goal = StringProperty("All")
    filter_muscle_group = StringProperty("All")
    filter_equipment = StringProperty("All")
    status_text = StringProperty("")
    status_color = ListProperty((0.14, 0.4, 0.2, 1))
    muscle_choice_display = StringProperty("")
    equipment_choice_display = StringProperty("")

    def __init__(self, **kwargs):
        app = App.get_running_app()
        # Ensure app.root is available during KV evaluation to avoid NoneType errors.
        if app and app.root is None:
            app.root = self
        super().__init__(**kwargs)
        self.records: list[dict[str, Any]] = []
        self._goal_label_map = {self._pretty_goal(goal): goal for goal in exercise_database.GOALS}
        Clock.schedule_once(self._bootstrap_data, 0)

    def _pretty_goal(self, goal: str) -> str:
        return goal.replace("_", " ").title()

    def _bootstrap_data(self, *_: Any) -> None:
        self.records = self._load_records()
        self.goal_choice_options = list(self._goal_label_map.keys())
        if not self.add_goal_spinner_text and self.goal_choice_options:
            self.add_goal_spinner_text = self.goal_choice_options[0]
        self._update_filter_options()
        self.apply_filters()

    def _load_records(self) -> list[dict[str, Any]]:
        with exercise_database.get_connection() as conn:
            rows = exercise_database.fetch_all(conn)
        records: list[dict[str, Any]] = []
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

    def _update_filter_options(self) -> None:
        muscle_choices = sorted({r["muscle_group"] for r in self.records})
        equipment_choices = sorted({r["equipment"] for r in self.records})
        self.muscle_choice_options = muscle_choices
        self.muscle_choice_display = ", ".join(muscle_choices) if muscle_choices else "No known groups yet."
        if not self.add_muscle_spinner_text and muscle_choices:
            self.add_muscle_spinner_text = muscle_choices[0]
        if muscle_choices and self.add_muscle_spinner_text not in muscle_choices:
            self.add_muscle_spinner_text = muscle_choices[0]

        self.equipment_choice_options = equipment_choices if equipment_choices else ["Bodyweight"]
        self.equipment_choice_display = ", ".join(self.equipment_choice_options) if self.equipment_choice_options else ""
        if not self.add_equipment_spinner_text:
            if "Bodyweight" in self.equipment_choice_options:
                self.add_equipment_spinner_text = "Bodyweight"
            elif self.equipment_choice_options:
                self.add_equipment_spinner_text = self.equipment_choice_options[0]
        elif self.add_equipment_spinner_text not in self.equipment_choice_options:
            if "Bodyweight" in self.equipment_choice_options:
                self.add_equipment_spinner_text = "Bodyweight"
            else:
                self.add_equipment_spinner_text = self.equipment_choice_options[0]

        self.goal_options = ["All goals"] + self.goal_choice_options
        muscle_options = ["All muscle groups"] + muscle_choices
        equipment_options = ["All equipment"] + equipment_choices
        if self.muscle_spinner_text not in muscle_options:
            self.muscle_spinner_text = "All muscle groups"
            self.filter_muscle_group = "All"
        if self.equipment_spinner_text not in equipment_options:
            self.equipment_spinner_text = "All equipment"
            self.filter_equipment = "All"
        self.muscle_options = muscle_options
        self.equipment_options = equipment_options

    def _browse_screen(self) -> BrowseScreen:
        return self.ids.screen_manager.get_screen("browse")

    def _add_screen(self) -> AddScreen:
        return self.ids.screen_manager.get_screen("add")

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
        self._browse_screen().ids.exercise_list.data = filtered

    def _parse_optional_int(self, value: str) -> Optional[int]:
        value = value.strip()
        if not value:
            return None
        try:
            parsed = int(value)
            if parsed <= 0:
                raise ValueError
            return parsed
        except ValueError:
            raise ValueError("Enter positive numbers only.")

    def _set_status(self, message: str, *, error: bool = False) -> None:
        self.status_text = message
        self.status_color = (0.65, 0.16, 0.16, 1) if error else (0.14, 0.4, 0.2, 1)

    def _refresh_records(self) -> None:
        self.records = self._load_records()
        self._update_filter_options()
        self.apply_filters()

    def _reset_form(self) -> None:
        ids = self._add_screen().ids
        ids.name_input.text = ""
        ids.description_input.text = ""
        ids.sets_input.text = ""
        ids.reps_input.text = ""
        ids.time_input.text = ""
        if self.goal_choice_options:
            self.add_goal_spinner_text = self.goal_choice_options[0]
        if self.muscle_choice_options:
            self.add_muscle_spinner_text = self.muscle_choice_options[0]
        if self.equipment_choice_options:
            self.add_equipment_spinner_text = self.equipment_choice_options[0]
        self.rating_spinner_text = "5"

    def handle_add_exercise(self) -> None:
        ids = self._add_screen().ids
        name = ids.name_input.text.strip()
        description = ids.description_input.text.strip()
        equipment = ids.equipment_add_spinner.text.strip() or "Bodyweight"
        goal_label = ids.goal_add_spinner.text
        goal = self._goal_label_map.get(goal_label)
        muscle_group = ids.muscle_add_spinner.text.strip()

        if not (name and description and muscle_group and goal and equipment):
            self._set_status("Name, description, muscle group, equipment, and goal are required.", error=True)
            return

        if muscle_group not in self.muscle_choice_options:
            self._set_status("Choose a muscle group from the known list.", error=True)
            return

        if equipment not in self.equipment_choice_options:
            self._set_status("Choose equipment from the known list.", error=True)
            return

        if any(r["name"].lower() == name.lower() for r in self.records):
            self._set_status("Exercise name already exists. Choose another name.", error=True)
            return

        try:
            rating = int(ids.rating_spinner.text)
            if rating < 1 or rating > 10:
                raise ValueError
        except ValueError:
            self._set_status("Rating must be 1-10.", error=True)
            return

        try:
            sets = self._parse_optional_int(ids.sets_input.text)
            reps = self._parse_optional_int(ids.reps_input.text)
            time_seconds = self._parse_optional_int(ids.time_input.text)
        except ValueError as exc:
            self._set_status(str(exc), error=True)
            return

        try:
            exercise_database.add_exercise(
                name=name,
                short_description=description,
                required_equipment=equipment,
                target_muscle_group=muscle_group,
                goal=goal,
                suitability_rating=rating,
                recommended_sets=sets,
                recommended_reps_per_set=reps,
                recommended_time_seconds=time_seconds,
            )
        except sqlite3.IntegrityError:
            self._set_status("Exercise name already exists. Choose another name.", error=True)
            return
        except sqlite3.DatabaseError as exc:
            self._set_status(f"Database error: {exc}", error=True)
            return

        self._set_status("Exercise added.")
        self._refresh_records()
        self._reset_form()

    def go_home(self) -> None:
        self.ids.screen_manager.current = "home"

    def go_browse(self) -> None:
        self.ids.screen_manager.current = "browse"

    def go_add(self) -> None:
        self.ids.screen_manager.current = "add"


class ExerciseApp(App):
    def build(self):
        exercise_database.initialize_database()
        Builder.load_string(KV)
        return RootWidget()


if __name__ == "__main__":
    ExerciseApp().run()
