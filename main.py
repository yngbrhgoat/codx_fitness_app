from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Any, Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp

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
    GridLayout:
        cols: 3
        spacing: dp(6)
        size_hint_y: None
        row_default_height: dp(22)
        height: self.minimum_height
        col_force_default: True
        col_default_width: self.width / 3
        Label:
            text: "Suitability: {}".format(root.suitability_display)
            color: 0.2, 0.2, 0.3, 1
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

<WorkoutCard>:
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
        text: root.date_display
        font_size: "17sp"
        bold: True
        color: 0.1, 0.12, 0.2, 1
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: "Duration: {} min".format(root.duration_display)
        color: 0.18, 0.18, 0.22, 1
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: "Goal: {}".format(root.goal_display)
        color: 0.16, 0.18, 0.24, 1
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: "Completed sets: {}".format(root.sets_display)
        color: 0.16, 0.18, 0.24, 1
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: root.exercises_display
        color: 0.2, 0.2, 0.28, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: root.attempts_display
        color: 0.18, 0.18, 0.24, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1]

<RecommendationCard>:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(6)
    size_hint_y: None
    height: self.minimum_height
    canvas.before:
        Color:
            rgba: 0.9, 0.95, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8,]
    Label:
        text: root.name
        font_size: "17sp"
        bold: True
        color: 0.1, 0.12, 0.2, 1
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: root.description if root.show_details else ""
        color: 0.1, 0.12, 0.18, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] if root.show_details else 0
        opacity: 1 if root.show_details else 0
    Label:
        text: "Muscle: {} | Equipment: {}".format(root.muscle_group, root.equipment)
        color: 0.2, 0.2, 0.3, 1
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: "Suitability: {} | Est. time: {} min".format(root.suitability, root.estimated_minutes)
        color: 0.2, 0.2, 0.3, 1
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: "Recommendation score: {}".format(root.score_display)
        color: 0.16, 0.16, 0.22, 1
        size_hint_y: None
        height: self.texture_size[1]
    Label:
        text: root.recommendation
        color: 0.18, 0.18, 0.24, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1]
    BoxLayout:
        size_hint_y: None
        height: dp(36)
        spacing: dp(8)
        Button:
            text: "Add to plan"
            on_release: app.root.add_recommendation_to_plan(root.name)
        Button:
            text: "Details"
            on_release: app.root.toggle_recommendation_details(root.name)

<PlanItem>:
    orientation: "horizontal"
    padding: dp(8)
    spacing: dp(8)
    size_hint_y: None
    height: dp(60)
    canvas.before:
        Color:
            rgba: 0.9, 0.95, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [6,]
    Label:
        text: root.display
        color: 0.18, 0.18, 0.24, 1
        text_size: self.width, None
        halign: "left"
        valign: "middle"
    Button:
        text: "Up"
        size_hint_x: None
        width: dp(70)
        on_release: app.root.move_plan_item(root.name, -1)
    Button:
        text: "Down"
        size_hint_x: None
        width: dp(70)
        on_release: app.root.move_plan_item(root.name, 1)
    Button:
        text: "Remove"
        size_hint_x: None
        width: dp(90)
        on_release: app.root.remove_plan_item(root.name)

<LiveScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(14)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 0.96, 0.99, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        GridLayout:
            cols: 2
            spacing: dp(8)
            size_hint_y: None
            row_default_height: dp(30)
            height: self.minimum_height
            Label:
                text: app.root.live_progress_display
                bold: True
                color: 0.1, 0.12, 0.2, 1
            Label:
                text: app.root.live_state_display
                color: 0.16, 0.2, 0.35, 1
        BoxLayout:
            orientation: "vertical"
            padding: dp(10)
            spacing: dp(6)
            size_hint_y: None
            height: dp(150)
            canvas.before:
                Color:
                    rgba: 0.92, 0.97, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10,]
            Label:
                text: app.root.live_exercise_title
                font_size: "22sp"
                bold: True
                color: 0.08, 0.12, 0.22, 1
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                text: app.root.live_icon_display
                color: 0.18, 0.2, 0.32, 1
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                text: "Target: {} | Equipment: {}".format(app.root.live_muscle_display, app.root.live_equipment_display)
                color: 0.18, 0.18, 0.24, 1
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                text: app.root.live_recommendation_display
                color: 0.16, 0.2, 0.3, 1
                size_hint_y: None
                height: self.texture_size[1]
        GridLayout:
            cols: 3
            spacing: dp(8)
            size_hint_y: None
            height: dp(90)
            canvas.before:
                Color:
                    rgba: 0.94, 0.97, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [8,]
            BoxLayout:
                orientation: "vertical"
                padding: dp(6)
                Label:
                    text: "Exercise time"
                    color: 0.16, 0.18, 0.24, 1
                    size_hint_y: None
                    height: dp(20)
                Label:
                    text: app.root.live_exercise_timer
                    font_size: "20sp"
                    bold: True
                    color: 0.08, 0.12, 0.22, 1
            BoxLayout:
                orientation: "vertical"
                padding: dp(6)
                Label:
                    text: "Set time"
                    color: 0.16, 0.18, 0.24, 1
                    size_hint_y: None
                    height: dp(20)
                Label:
                    text: app.root.live_set_timer
                    font_size: "20sp"
                    bold: True
                    color: 0.08, 0.12, 0.22, 1
            BoxLayout:
                orientation: "vertical"
                padding: dp(6)
                Label:
                    text: "Break timer"
                    color: 0.16, 0.18, 0.24, 1
                    size_hint_y: None
                    height: dp(20)
                Label:
                    text: app.root.live_rest_timer
                    font_size: "20sp"
                    bold: True
                    color: 0.08, 0.12, 0.22, 1
        Label:
            text: app.root.live_current_set_display
            color: 0.14, 0.16, 0.24, 1
            size_hint_y: None
            height: dp(22)
        Label:
            text: app.root.live_instruction
            color: 0.14, 0.16, 0.26, 1
            size_hint_y: None
            height: dp(22)
        Label:
            text: app.root.live_tempo_hint
            color: 0.12, 0.18, 0.34, 1
            size_hint_y: None
            height: dp(22)
        Label:
            text: app.root.live_hint_text
            color: app.root.live_hint_color
            bold: True
            size_hint_y: None
            height: dp(24)
        Label:
            text: "Upcoming: {}".format(app.root.live_upcoming_display)
            color: 0.16, 0.16, 0.22, 1
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
        GridLayout:
            cols: 3
            spacing: dp(8)
            row_default_height: dp(44)
            size_hint_y: None
            height: self.minimum_height
            Button:
                text: "Pause" if not app.root.live_paused else "Resume"
                on_release: app.root.toggle_live_pause()
            Button:
                text: "Complete set"
                on_release: app.root.manual_complete_set()
            Button:
                text: "Skip exercise"
                on_release: app.root.skip_current_exercise()
            Button:
                text: "Next exercise"
                on_release: app.root.manual_next_exercise()
            Button:
                text: "End workout"
                on_release: app.root.end_live_session(early=True)
            Button:
                text: "Back to plan"
                on_release: app.root.go_recommend()

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
        Label:
            text: "Live Mode: build a plan under Recommend, then press Start."
            font_size: "18sp"
            bold: True
            color: 0.16, 0.16, 0.22, 1
            size_hint_y: None
            height: dp(26)
            text_size: self.width, None
            halign: "center"
        AnchorLayout:
            anchor_y: "center"
            BoxLayout:
                orientation: "vertical"
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                GridLayout:
                    cols: 3
                    spacing: dp(12)
                    row_default_height: dp(70)
                    size_hint_y: None
                    height: self.minimum_height
                    Button:
                        text: "Browse"
                        font_size: "26sp"
                        bold: True
                        background_normal: ""
                        background_color: 0.18, 0.4, 0.85, 1
                        color: 1, 1, 1, 1
                        on_release: app.root.go_browse()
                    Button:
                        text: "Add"
                        font_size: "26sp"
                        bold: True
                        background_normal: ""
                        background_color: 0.18, 0.4, 0.85, 1
                        color: 1, 1, 1, 1
                        on_release: app.root.go_add()
                    Button:
                        text: "Users"
                        font_size: "26sp"
                        bold: True
                        background_normal: ""
                        background_color: 0.18, 0.4, 0.85, 1
                        color: 1, 1, 1, 1
                        on_release: app.root.go_users()
                AnchorLayout:
                    anchor_x: "center"
                    size_hint_y: None
                    height: dp(70)
                    BoxLayout:
                        size_hint_y: None
                        height: dp(70)
                        size_hint_x: None
                        width: self.minimum_width
                        spacing: dp(12)
                        Button:
                            text: "History"
                            font_size: "26sp"
                            bold: True
                            background_normal: ""
                            background_color: 0.18, 0.4, 0.85, 1
                            color: 1, 1, 1, 1
                            size_hint_x: None
                            width: dp(200)
                            on_release: app.root.go_history()
                        Button:
                            text: "Recommend"
                            font_size: "26sp"
                            bold: True
                            background_normal: ""
                            background_color: 0.18, 0.4, 0.85, 1
                            color: 1, 1, 1, 1
                            size_hint_x: None
                            width: dp(200)
                            on_release: app.root.go_recommend()

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
                default_size: None, None
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

<UserScreen>:
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
        AnchorLayout:
            anchor_y: "center"
            size_hint_y: 0.55
            BoxLayout:
                orientation: "vertical"
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "Select user"
                    font_size: "18sp"
                    bold: True
                    color: 0.12, 0.14, 0.22, 1
                    size_hint_y: None
                    height: dp(26)
                Label:
                    text: "Choose an existing user to continue."
                    color: 0.2, 0.2, 0.3, 1
                    size_hint_y: None
                    height: dp(20)
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(8)
                    Spinner:
                        id: user_spinner
                        text: app.root.user_spinner_text
                        values: app.root.user_options
                        on_text: app.root.on_user_selected(self.text)
                    Button:
                        text: "Open history"
                        size_hint_x: None
                        width: dp(140)
                        on_release: app.root.go_history()
                Label:
                    text: "Current user: {}".format(app.root.current_user_display)
                    color: 0.2, 0.2, 0.3, 1
                    size_hint_y: None
                    height: dp(22)
                Label:
                    text: ""
                    size_hint_y: None
                    height: dp(4)
        AnchorLayout:
            anchor_y: "bottom"
            size_hint_y: 0.45
            BoxLayout:
                orientation: "vertical"
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "Create a new user"
                    font_size: "17sp"
                    bold: True
                    color: 0.12, 0.14, 0.22, 1
                    size_hint_y: None
                    height: dp(24)
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(8)
                    TextInput:
                        id: username_input
                        hint_text: "New username"
                        multiline: False
                    Button:
                        text: "Register"
                        size_hint_x: None
                        width: dp(120)
                        on_release: app.root.handle_register_user()
                Label:
                    text: app.root.user_status_text
                    color: app.root.user_status_color
                    size_hint_y: None
                    height: dp(20)

<HistoryScreen>:
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            padding: dp(12)
            spacing: dp(10)
            size_hint_y: None
            height: self.minimum_height
            canvas.before:
                Color:
                    rgba: 0.98, 0.98, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "Workout history"
                font_size: "18sp"
                bold: True
                color: 0.12, 0.14, 0.22, 1
                size_hint_y: None
                height: dp(26)
            Label:
                text: "Current user: {}".format(app.root.current_user_display)
                color: 0.2, 0.2, 0.3, 1
                size_hint_y: None
                height: dp(22)
            GridLayout:
                cols: 2
                spacing: dp(8)
                row_default_height: dp(34)
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "Start date (YYYY-MM-DD)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: start_date_input
                    multiline: False
                    hint_text: "optional"
                Label:
                    text: "End date (YYYY-MM-DD)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: end_date_input
                    multiline: False
                    hint_text: "optional"
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(8)
                Button:
                    text: "Apply filter"
                    on_release: app.root.apply_history_filter()
                Button:
                    text: "Clear filter"
                    on_release: app.root.clear_history_filter()
            Label:
                text: "Log a completed workout"
                bold: True
                color: 0.14, 0.16, 0.24, 1
                size_hint_y: None
                height: dp(22)
            BoxLayout:
                size_hint_y: None
                height: dp(70)
                spacing: dp(12)
                BoxLayout:
                    orientation: "vertical"
                    spacing: dp(4)
                    Label:
                        text: "Stats"
                        bold: True
                        color: 0.12, 0.14, 0.22, 1
                        size_hint_y: None
                        height: dp(20)
                    Label:
                        text: "Total workouts: {}".format(app.root.stats_total_workouts)
                        color: 0.18, 0.18, 0.24, 1
                        size_hint_y: None
                        height: dp(18)
                    Label:
                        text: "Total time: {} min".format(app.root.stats_total_minutes)
                        color: 0.18, 0.18, 0.24, 1
                        size_hint_y: None
                        height: dp(18)
                    Label:
                        text: "Top exercise: {}".format(app.root.stats_top_exercise)
                        color: 0.18, 0.18, 0.24, 1
                        size_hint_y: None
                        height: dp(18)
            GridLayout:
                cols: 2
                spacing: dp(8)
                row_default_height: dp(34)
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "Workout date (YYYY-MM-DD)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: workout_date_input
                    multiline: False
                    hint_text: "e.g. 2025-12-10"
                Label:
                    text: "Duration (minutes)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: duration_input
                    multiline: False
                    input_filter: "int"
                    hint_text: "e.g. 45"
                Label:
                    text: "Exercises (comma or newline separated)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: exercises_input
                    multiline: True
                    size_hint_y: None
                    height: dp(80)
                    hint_text: "Push-Up, Plank, Jump Rope"
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(8)
                Button:
                    text: "Save workout"
                    on_release: app.root.handle_add_workout()
                Button:
                    text: "Refresh history"
                    on_release: app.root._load_history()
            Label:
                text: app.root.history_status_text
                color: app.root.history_status_color
                size_hint_y: None
                height: dp(20)
            RecycleView:
                id: history_list
                viewclass: "WorkoutCard"
                bar_width: dp(6)
                scroll_type: ['bars', 'content']
                size_hint_y: None
                height: dp(400)
                RecycleBoxLayout:
                    default_size: None, dp(120)
                    default_size_hint: 1, None
                    size_hint_y: None
                    height: self.minimum_height
                    orientation: "vertical"
                    spacing: dp(10)

<RecommendationScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 0.96, 0.99, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        GridLayout:
            cols: 2
            spacing: dp(8)
            row_default_height: dp(34)
            size_hint_y: None
            height: self.minimum_height
            Label:
                text: "Goal"
                color: 0.18, 0.18, 0.22, 1
            Spinner:
                id: rec_goal_spinner
                text: app.root.rec_goal_spinner_text
                values: app.root.goal_choice_options
                on_text: app.root.rec_goal_spinner_text = self.text
            Label:
                text: "Max time (minutes)"
                color: 0.18, 0.18, 0.22, 1
            TextInput:
                id: rec_max_time
                text: app.root.rec_max_minutes_text
                multiline: False
                input_filter: "int"
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Button:
                text: "Generate recommendations"
                on_release: app.root.handle_generate_recommendations()
            Button:
                text: "Clear plan"
                on_release: app.root.clear_recommendation_plan()
        Label:
            text: app.root.rec_status_text
            color: app.root.rec_status_color
            size_hint_y: None
            height: dp(20)
        Label:
            text: "Recommended exercises"
            bold: True
            color: 0.12, 0.14, 0.22, 1
            size_hint_y: None
            height: dp(22)
        RecycleView:
            id: rec_list
            viewclass: "RecommendationCard"
            bar_width: dp(6)
            scroll_type: ['bars', 'content']
            size_hint_y: None
            height: dp(320)
            RecycleGridLayout:
                cols: 2
                default_size: None, dp(200)
                default_size_hint: 0.5, None
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
        Label:
            text: "Your training plan (reorder with Up/Down)"
            bold: True
            color: 0.12, 0.14, 0.22, 1
            size_hint_y: None
            height: dp(22)
        RecycleView:
            id: rec_plan_list
            viewclass: "PlanItem"
            bar_width: dp(6)
            scroll_type: ['bars', 'content']
            size_hint_y: 0.35
            RecycleBoxLayout:
                default_size: None, dp(70)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: "vertical"
                spacing: dp(6)
        BoxLayout:
            size_hint_y: None
            height: dp(36)
            spacing: dp(8)
            Label:
                text: "Total time: {} / {} min".format(app.root.rec_total_minutes, app.root.rec_max_minutes_text or "0")
                color: 0.18, 0.18, 0.24, 1
            Button:
                text: "Start training"
                on_release: app.root.handle_start_training()

<SummaryScreen>:
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            padding: dp(14)
            spacing: dp(10)
            size_hint_y: None
            height: self.minimum_height
            canvas.before:
                Color:
                    rgba: 0.97, 0.98, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "Workout summary"
                font_size: "20sp"
                bold: True
                color: 0.1, 0.12, 0.2, 1
                size_hint_y: None
                height: dp(28)
            GridLayout:
                cols: 2
                spacing: dp(8)
                row_default_height: dp(26)
                size_hint_y: None
                height: self.minimum_height
                Label:
                    text: "Finished at"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.summary_performed_at_display
                    color: 0.16, 0.2, 0.3, 1
                    text_size: self.width, None
                    halign: "left"
                Label:
                    text: "Goal"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.summary_goal_display
                    color: 0.16, 0.2, 0.3, 1
                Label:
                    text: "Total duration"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.summary_duration_display
                    color: 0.16, 0.2, 0.3, 1
                Label:
                    text: "Completed sets"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.summary_sets_display
                    color: 0.16, 0.2, 0.3, 1
            Label:
                text: "Completed exercises: {}".format(app.root.summary_completed_display)
                color: 0.15, 0.18, 0.26, 1
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                text: "Skipped exercises: {}".format(app.root.summary_skipped_display)
                color: 0.2, 0.16, 0.18, 1
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
            Label:
                text: "Attempted exercises with status:"
                bold: True
                color: 0.12, 0.14, 0.22, 1
                size_hint_y: None
                height: dp(22)
            Label:
                text: app.root.summary_attempts_display
                color: 0.16, 0.2, 0.3, 1
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
            BoxLayout:
                size_hint_y: None
                height: dp(44)
                spacing: dp(10)
                Button:
                    text: "Return to main menu"
                    on_release: app.root.go_home()
                Button:
                    text: "Start a new training session"
                    on_release: app.root.start_new_session()
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
        Button:
            text: "Users"
            size_hint_x: None
            width: dp(90)
            on_release: root.go_users()
        Button:
            text: "History"
            size_hint_x: None
            width: dp(90)
            on_release: root.go_history()
        Button:
            text: "Recommend"
            size_hint_x: None
            width: dp(110)
            on_release: root.go_recommend()
        Button:
            text: "Live"
            size_hint_x: None
            width: dp(90)
            disabled: not app.root.live_active
            on_release: root.go_live()

    ScreenManager:
        id: screen_manager
        HomeScreen:
            name: "home"
        BrowseScreen:
            name: "browse"
        AddScreen:
            name: "add"
        UserScreen:
            name: "user"
        HistoryScreen:
            name: "history"
        RecommendationScreen:
            name: "recommend"
        LiveScreen:
            name: "live"
        SummaryScreen:
            name: "summary"
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


class UserScreen(Screen):
    pass


class HistoryScreen(Screen):
    pass


class WorkoutCard(BoxLayout):
    date_display = StringProperty()
    duration_display = StringProperty()
    exercises_display = StringProperty()
    goal_display = StringProperty()
    sets_display = StringProperty()
    attempts_display = StringProperty()


class RecommendationScreen(Screen):
    pass


class LiveScreen(Screen):
    pass


class SummaryScreen(Screen):
    pass


class PlanItem(BoxLayout):
    name = StringProperty()
    display = StringProperty()
    index = StringProperty()
    pass


class RecommendationCard(BoxLayout):
    name = StringProperty()
    description = StringProperty()
    muscle_group = StringProperty()
    equipment = StringProperty()
    suitability = StringProperty()
    estimated_minutes = StringProperty()
    score_display = StringProperty()
    recommendation = StringProperty()
    show_details = StringProperty("0")


class RootWidget(BoxLayout):
    goal_options = ListProperty()
    goal_choice_options = ListProperty()
    muscle_choice_options = ListProperty()
    equipment_choice_options = ListProperty()
    muscle_options = ListProperty()
    equipment_options = ListProperty()
    user_options = ListProperty()

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
    user_spinner_text = StringProperty("Select user")
    current_user_display = StringProperty("No user selected")
    user_status_text = StringProperty("")
    user_status_color = ListProperty((0.14, 0.4, 0.2, 1))
    history_status_text = StringProperty("")
    history_status_color = ListProperty((0.14, 0.4, 0.2, 1))
    stats_total_workouts = StringProperty("0")
    stats_total_minutes = StringProperty("0")
    stats_top_exercise = StringProperty("—")
    rec_status_text = StringProperty("")
    rec_status_color = ListProperty((0.14, 0.4, 0.2, 1))
    rec_goal_spinner_text = StringProperty("")
    rec_max_minutes_text = StringProperty("30")
    rec_recommendations = ListProperty()
    rec_plan = ListProperty()
    rec_total_minutes = StringProperty("0")
    live_active = BooleanProperty(False)
    live_paused = BooleanProperty(False)
    live_exercises = ListProperty()
    live_progress_display = StringProperty("No session")
    live_state_display = StringProperty("Not started")
    live_exercise_title = StringProperty("No exercise running")
    live_icon_display = StringProperty("")
    live_muscle_display = StringProperty("")
    live_equipment_display = StringProperty("")
    live_recommendation_display = StringProperty("")
    live_exercise_timer = StringProperty("00:00")
    live_set_timer = StringProperty("00:00")
    live_rest_timer = StringProperty("—")
    live_current_set_display = StringProperty("")
    live_instruction = StringProperty("")
    live_tempo_hint = StringProperty("")
    live_hint_text = StringProperty("")
    live_hint_color = ListProperty((0.14, 0.4, 0.2, 1))
    live_upcoming_display = StringProperty("None")
    summary_duration_display = StringProperty("00:00")
    summary_sets_display = StringProperty("0")
    summary_completed_display = StringProperty("None")
    summary_skipped_display = StringProperty("None")
    summary_attempts_display = StringProperty("")
    summary_goal_display = StringProperty("—")
    summary_performed_at_display = StringProperty("")

    def __init__(self, **kwargs):
        app = App.get_running_app()
        # Ensure app.root is available during KV evaluation to avoid NoneType errors.
        if app and app.root is None:
            app.root = self
        super().__init__(**kwargs)
        self.records: list[dict[str, Any]] = []
        self._users: list[dict[str, Any]] = []
        self.current_user_id: Optional[int] = None
        self.history_start: Optional[str] = None
        self.history_end: Optional[str] = None
        self._goal_label_map = {self._pretty_goal(goal): goal for goal in exercise_database.GOALS}
        self._live_clock = None
        self._live_current_index = 0
        self._live_current_set = 1
        self._live_set_elapsed = 0.0
        self._live_exercise_elapsed = 0.0
        self._live_rest_remaining = 0.0
        self._live_set_target_seconds = 0.0
        self._live_session_started_at: Optional[datetime] = None
        self._live_completed: list[str] = []
        self._live_skipped: list[str] = []
        self._live_attempt_log: list[dict[str, str]] = []
        self._live_goal_label: str = ""
        self._live_total_sets_completed = 0
        self._live_current_logged = False
        self.live_rest_seconds = 30
        self._live_phase = "idle"
        Clock.schedule_once(self._bootstrap_data, 0)

    def _pretty_goal(self, goal: str) -> str:
        return goal.replace("_", " ").title()

    def _preferred_goal_label(self) -> str:
        """
        Pick a default goal label for forms:
        - Current recommendation goal if chosen
        - Else "Muscle Building" (most common)
        - Else first available goal.
        """
        if self.rec_goal_spinner_text:
            return self.rec_goal_spinner_text
        muscle_label = self._pretty_goal("muscle_building")
        if muscle_label in self.goal_choice_options:
            return muscle_label
        if self.goal_choice_options:
            return self.goal_choice_options[0]
        return ""

    def _bootstrap_data(self, *_: Any) -> None:
        self.records = self._load_records()
        self.goal_choice_options = list(self._goal_label_map.keys())
        if not self.add_goal_spinner_text and self.goal_choice_options:
            self.add_goal_spinner_text = self._preferred_goal_label()
        self._update_filter_options()
        self.apply_filters()
        self._load_users()
        self._prefill_workout_date()
        # Start on the user screen so a user is chosen or created immediately.
        try:
            self.ids.screen_manager.current = "user"
        except Exception:
            pass
        if self.goal_choice_options and not self.rec_goal_spinner_text:
            self.rec_goal_spinner_text = self.goal_choice_options[0]

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
            if not name or not description:
                continue
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
                    "icon": icon or "",
                    "description": description,
                    "equipment": equipment,
                    "muscle_group": muscle_group,
                    "goal": goal,
                    "goal_label": self._pretty_goal(goal),
                    "suitability_display": f"{rating}/10",
                    "rating": rating,
                    "sets": sets,
                    "reps": reps,
                    "time_seconds": time_seconds,
                    "recommendation": recommendation,
                }
            )
        return records

    def _update_filter_options(self) -> None:
        muscle_choices = sorted({r["muscle_group"] for r in self.records})
        equipment_choices = sorted({r["equipment"] for r in self.records})
        if "Dumbbells" not in equipment_choices:
            equipment_choices.append("Dumbbells")
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
        if self.goal_choice_options and self.add_goal_spinner_text not in self.goal_choice_options:
            self.add_goal_spinner_text = self._preferred_goal_label()

    def _browse_screen(self) -> BrowseScreen:
        return self.ids.screen_manager.get_screen("browse")

    def _add_screen(self) -> AddScreen:
        return self.ids.screen_manager.get_screen("add")

    def _user_screen(self) -> UserScreen:
        return self.ids.screen_manager.get_screen("user")

    def _history_screen(self) -> HistoryScreen:
        return self.ids.screen_manager.get_screen("history")

    def _recommend_screen(self) -> RecommendationScreen:
        return self.ids.screen_manager.get_screen("recommend")

    def _prefill_workout_date(self) -> None:
        """Populate the workout date field with today's date if available."""
        try:
            history_screen = self._history_screen()
        except Exception:
            return
        date_field = history_screen.ids.get("workout_date_input")
        if date_field and not date_field.text:
            date_field.text = date.today().isoformat()

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
        filtered: list[dict[str, str]] = []
        for record in self.records:
            if not record.get("name") or not record.get("description"):
                continue
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
        exercise_list = self._browse_screen().ids.exercise_list
        # Clear first to avoid stale/blank items from previous data set.
        exercise_list.data = []
        exercise_list.refresh_from_data()
        exercise_list.data = filtered
        exercise_list.refresh_from_data()

    def _load_users(self) -> None:
        with exercise_database.get_connection() as conn:
            rows = exercise_database.fetch_users(conn)
        self._users = [{"id": user_id, "username": username} for user_id, username in rows]
        self.user_options = [u["username"] for u in self._users]

        if self.current_user_id and not any(u["id"] == self.current_user_id for u in self._users):
            self.current_user_id = None

        if self.current_user_id:
            current = next((u for u in self._users if u["id"] == self.current_user_id), None)
            if current:
                self.current_user_display = current["username"]
                self.user_spinner_text = current["username"]
        if not self.current_user_id:
            self.current_user_display = "No user selected"
            self.user_spinner_text = "Select user"

        self._load_history()

    def _set_user_status(self, message: str, *, error: bool = False) -> None:
        self.user_status_text = message
        self.user_status_color = (0.65, 0.16, 0.16, 1) if error else (0.14, 0.4, 0.2, 1)

    def _require_user(self) -> bool:
        if not self.current_user_id:
            self._set_user_status("Select or create a user to continue.", error=True)
            try:
                self.ids.screen_manager.current = "user"
            except Exception:
                pass
            return False
        return True

    def handle_register_user(self) -> None:
        ids = self._user_screen().ids
        username = ids.username_input.text.strip()
        if not username:
            self._set_user_status("Username is required.", error=True)
            return

        try:
            new_user_id = exercise_database.add_user(username=username)
        except ValueError as exc:
            self._set_user_status(str(exc), error=True)
            return
        except sqlite3.IntegrityError:
            self._set_user_status("Username already exists. Choose another.", error=True)
            return
        except sqlite3.DatabaseError as exc:
            self._set_user_status(f"Database error: {exc}", error=True)
            return

        ids.username_input.text = ""
        self.current_user_id = new_user_id
        self.current_user_display = username
        self.user_spinner_text = username
        self._set_user_status(f"User '{username}' registered.")
        self._load_users()
        self.go_home()

    def on_user_selected(self, username: str) -> None:
        selected = next((u for u in self._users if u["username"] == username), None)
        if not selected:
            return
        self.current_user_id = selected["id"]
        self.current_user_display = selected["username"]
        self.user_spinner_text = selected["username"]
        self._set_user_status(f"User '{username}' selected.")
        self._load_history()
        self.go_home()

    def _split_exercises(self, raw: str) -> list[str]:
        normalized = raw.replace("\n", ",")
        return [part.strip() for part in normalized.split(",") if part.strip()]

    def _parse_date_value(self, value: str, *, allow_empty: bool = False) -> Optional[str]:
        value = value.strip()
        if not value:
            if allow_empty:
                return None
            raise ValueError("Date is required (YYYY-MM-DD).")
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError("Use YYYY-MM-DD format.")
        return parsed.isoformat()

    def _set_history_status(self, message: str, *, error: bool = False) -> None:
        self.history_status_text = message
        self.history_status_color = (0.65, 0.16, 0.16, 1) if error else (0.14, 0.4, 0.2, 1)

    def _load_history(self, *_: Any) -> None:
        try:
            history_screen = self._history_screen()
        except Exception:
            return

        if not self.current_user_id:
            history_screen.ids.history_list.data = []
            self._set_history_status("Select or register a user to see history.", error=False)
            self._load_stats(clear=True)
            return

        try:
            history_entries = exercise_database.fetch_workout_history(
                self.current_user_id,
                start_date=self.history_start,
                end_date=self.history_end,
            )
        except sqlite3.DatabaseError as exc:
            self._set_history_status(f"Database error: {exc}", error=True)
            return

        data = []
        for entry in history_entries:
            exercises_display = ", ".join(entry.get("exercises", [])) if entry.get("exercises") else "No exercises recorded"
            attempts = entry.get("exercise_attempts") or []
            attempts_display = (
                "Attempts: "
                + ", ".join(
                    f"{att.get('name', 'Exercise')} ({att.get('status', 'completed').title()})" for att in attempts
                )
                if attempts
                else "Attempts: none recorded"
            )
            goal_display = entry.get("goal") or "—"
            sets_display = str(entry.get("total_sets_completed") or 0)
            duration_minutes = entry.get("duration_minutes") or 0
            duration_seconds = entry.get("duration_seconds")
            if duration_seconds:
                duration_display = f"{duration_minutes} min ({duration_seconds}s)"
            else:
                duration_display = str(duration_minutes)
            data.append(
                {
                    "date_display": entry["performed_at"],
                    "duration_display": duration_display,
                    "exercises_display": exercises_display,
                    "goal_display": goal_display,
                    "sets_display": sets_display,
                    "attempts_display": attempts_display,
                }
            )
        history_screen.ids.history_list.data = data
        if data:
            self._set_history_status(f"{len(data)} workout(s) loaded.")
        else:
            self._set_history_status("No workouts in this date range.", error=False)
        self._load_stats()

    def apply_history_filter(self) -> None:
        ids = self._history_screen().ids
        try:
            self.history_start = self._parse_date_value(ids.start_date_input.text, allow_empty=True)
            self.history_end = self._parse_date_value(ids.end_date_input.text, allow_empty=True)
        except ValueError as exc:
            self._set_history_status(str(exc), error=True)
            return
        self._load_history()

    def clear_history_filter(self) -> None:
        ids = self._history_screen().ids
        ids.start_date_input.text = ""
        ids.end_date_input.text = ""
        self.history_start = None
        self.history_end = None
        self._set_history_status("Filters cleared.")
        self._load_history()

    def handle_add_workout(self) -> None:
        if not self.current_user_id:
            self._set_history_status("Select or register a user first.", error=True)
            return

        ids = self._history_screen().ids
        try:
            workout_date = self._parse_date_value(ids.workout_date_input.text, allow_empty=False)
        except ValueError as exc:
            self._set_history_status(str(exc), error=True)
            return

        duration_raw = ids.duration_input.text.strip()
        try:
            duration_minutes = int(duration_raw)
            if duration_minutes <= 0:
                raise ValueError
        except ValueError:
            self._set_history_status("Duration must be a positive number of minutes.", error=True)
            return

        exercises = self._split_exercises(ids.exercises_input.text)
        if not exercises:
            self._set_history_status("Add at least one exercise.", error=True)
            return

        try:
            exercise_database.log_workout(
                user_id=self.current_user_id,
                performed_at=workout_date,
                duration_minutes=duration_minutes,
                exercises=exercises,
            )
        except (ValueError, sqlite3.DatabaseError) as exc:
            self._set_history_status(str(exc), error=True)
            return

        self._set_history_status("Workout saved.")
        ids.duration_input.text = ""
        ids.exercises_input.text = ""
        self._prefill_workout_date()
        self._load_history()

    def _load_stats(self, *, clear: bool = False) -> None:
        if clear or not self.current_user_id:
            self.stats_total_workouts = "0"
            self.stats_total_minutes = "0"
            self.stats_top_exercise = "—"
            return
        try:
            stats = exercise_database.fetch_workout_stats(
                self.current_user_id,
                start_date=self.history_start,
                end_date=self.history_end,
            )
        except sqlite3.DatabaseError as exc:
            self._set_history_status(f"Database error while loading stats: {exc}", error=True)
            return

        self.stats_total_workouts = str(stats.get("total_workouts", 0))
        self.stats_total_minutes = str(stats.get("total_minutes", 0))
        top = stats.get("top_exercise")
        if top:
            count = stats.get("top_exercise_count", 0)
            self.stats_top_exercise = f"{top} ({count}x)"
        else:
            self.stats_top_exercise = "—"

    # --- Recommendation system ---
    def _set_rec_status(self, message: str, *, error: bool = False) -> None:
        self.rec_status_text = message
        self.rec_status_color = (0.65, 0.16, 0.16, 1) if error else (0.14, 0.4, 0.2, 1)

    def _estimate_minutes(self, record: dict[str, Any]) -> int:
        """
        Estimate training time for an exercise.

        Scoring logic (documented for transparency):
        - If recommended_time_seconds is available, convert to minutes (ceil).
        - Else, assume each rep ~4 seconds; time = sets * reps * 4 sec, then convert to minutes (ceil).
        - Fallback to 5 minutes if no volume info exists.
        """
        try:
            time_seconds = record.get("time_seconds")
            sets = record.get("sets")
            reps = record.get("reps")
            if time_seconds:
                return max(1, (time_seconds + 59) // 60)
            if sets and reps:
                seconds = sets * reps * 4
                return max(1, (seconds + 59) // 60)
            if sets:
                seconds = sets * 30
                return max(1, (seconds + 59) // 60)
        except Exception:
            pass
        return 5

    def _recency_days_map(self) -> dict[str, int]:
        """Return a mapping of exercise name to days since last performed for current user."""
        if not self.current_user_id:
            return {}
        rows = exercise_database.fetch_recent_exercise_usage(self.current_user_id, limit=200)
        recency: dict[str, int] = {}
        today = date.today()
        for name, performed_at in rows:
            if name in recency:
                continue
            try:
                performed_date = date.fromisoformat(performed_at)
                recency[name] = (today - performed_date).days
            except Exception:
                continue
        return recency

    def _score_recommendation(self, record: dict[str, Any], recency_days: Optional[int]) -> float:
        """
        Recommendation score formula (documented per requirement):
        score = suitability_rating
                + recency_bonus
        where:
            recency_bonus = +2.0 if never done
                           +1.0 if >14 days ago
                           +0.5 if between 7-14 days
                           -1.0 if done within last 3 days
                           0 otherwise
        """
        base = float(record.get("rating", 0))
        if recency_days is None:
            recency_bonus = 2.0
        elif recency_days > 14:
            recency_bonus = 1.0
        elif recency_days >= 7:
            recency_bonus = 0.5
        elif recency_days <= 3:
            recency_bonus = -1.0
        else:
            recency_bonus = 0.0
        return round(base + recency_bonus, 2)

    def handle_generate_recommendations(self) -> None:
        if not self._require_user():
            return
        if not self.rec_goal_spinner_text:
            self._set_rec_status("Choose a goal.", error=True)
            return
        try:
            max_minutes = int(self._recommend_screen().ids.rec_max_time.text.strip() or "0")
            if max_minutes <= 0:
                raise ValueError
        except ValueError:
            self._set_rec_status("Enter a positive max time (minutes).", error=True)
            return

        self.rec_max_minutes_text = str(max_minutes)
        goal_code = self._goal_label_map.get(self.rec_goal_spinner_text)
        if not goal_code:
            self._set_rec_status("Unknown goal selection.", error=True)
            return

        recency_map = self._recency_days_map()
        recommendations = []
        for record in self.records:
            if record["goal"] != goal_code:
                continue
            if any(item["name"] == record["name"] for item in self.rec_plan):
                continue
            est_minutes = self._estimate_minutes(record)
            recency_days = recency_map.get(record["name"])
            score = self._score_recommendation(
                {"rating": float(record.get("rating", 0))}, recency_days
            )
            recommendations.append(
                {
                    "name": record["name"],
                    "icon": record.get("icon", ""),
                    "description": record["description"],
                    "muscle_group": record["muscle_group"],
                    "equipment": record["equipment"],
                    "suitability": record["suitability_display"],
                    "recommendation": record["recommendation"],
                    "sets": record.get("sets"),
                    "reps": record.get("reps"),
                    "time_seconds": record.get("time_seconds"),
                    "estimated_minutes": str(est_minutes),
                    "score": score,
                    "score_display": str(score),
                }
            )

        recommendations.sort(key=lambda r: (-r["score"], r["name"]))
        self.rec_recommendations = recommendations
        self._recommend_screen().ids.rec_list.data = recommendations
        self._set_rec_status(f"{len(recommendations)} exercises recommended.")
        # Reset plan if goal changes
        self._reset_plan(silent=True)

    def _find_recommendation(self, name: str) -> Optional[dict[str, Any]]:
        return next((rec for rec in self.rec_recommendations if rec["name"] == name), None)

    def toggle_recommendation_details(self, name: str) -> None:
        rec = self._find_recommendation(name)
        if not rec:
            return
        # flip detail visibility for this item
        current = rec.get("show_details") == "1"
        for r in self.rec_recommendations:
            if r["name"] == name:
                r["show_details"] = "0" if current else "1"
            else:
                r["show_details"] = r.get("show_details", "0")
        self._recommend_screen().ids.rec_list.data = self.rec_recommendations
        self._set_rec_status("Details toggled.")

    def add_recommendation_to_plan(self, name: str) -> None:
        rec = self._find_recommendation(name)
        if not rec:
            return
        if any(item["name"] == name for item in self.rec_plan):
            self._set_rec_status(f"{name} is already in the plan.", error=True)
            return
        plan_item = {
            "name": rec["name"],
            "icon": rec.get("icon", ""),
            "muscle_group": rec.get("muscle_group", ""),
            "equipment": rec.get("equipment", ""),
            "sets": rec.get("sets"),
            "reps": rec.get("reps"),
            "time_seconds": rec.get("time_seconds"),
            "recommendation": rec.get("recommendation", ""),
            "estimated_minutes": rec["estimated_minutes"],
            "display": f'{rec["name"]} ({rec["estimated_minutes"]} min)',
        }
        self.rec_plan.append(plan_item)
        self._refresh_recommendation_view()
        self._set_rec_status(f"Added {name} to plan.")
        # Remove from recommendations list when selected.
        self.rec_recommendations = [r for r in self.rec_recommendations if r["name"] != name]
        self._recommend_screen().ids.rec_list.data = self.rec_recommendations

    def _refresh_recommendation_view(self) -> None:
        rv = self._recommend_screen().ids.rec_plan_list
        rv.data = [
            {
                "name": item["name"],
                "display": f'{item["name"]} ({item["estimated_minutes"]} min)',
                "index": str(idx),
            }
            for idx, item in enumerate(self.rec_plan)
        ]
        total_minutes = sum(int(item["estimated_minutes"]) for item in self.rec_plan)
        self.rec_total_minutes = str(total_minutes)
        self._validate_plan_time()
        rv.refresh_from_data()

    def move_plan_item(self, name: str, direction: int) -> None:
        for idx, item in enumerate(self.rec_plan):
            if item["name"] == name:
                new_idx = max(0, min(len(self.rec_plan) - 1, idx + direction))
                if new_idx != idx:
                    self.rec_plan.insert(new_idx, self.rec_plan.pop(idx))
                    self._set_rec_status(f"Moved {name}.")
                    self._refresh_recommendation_view()
                return

    def remove_plan_item(self, name: str) -> None:
        self.rec_plan = [item for item in self.rec_plan if item["name"] != name]
        self._set_rec_status(f"Removed {name} from plan.")
        self._refresh_recommendation_view()
        # Return the exercise to recommendations list in sorted order if it fits the current goal.
        if self.rec_goal_spinner_text:
            goal_code = self._goal_label_map.get(self.rec_goal_spinner_text)
            match = next((r for r in self.records if r["name"] == name and r["goal"] == goal_code), None)
            if match:
                est_minutes = self._estimate_minutes(match)
                recency_map = self._recency_days_map()
                recency_days = recency_map.get(match["name"])
                score = self._score_recommendation({"rating": float(match.get("rating", 0))}, recency_days)
                self.rec_recommendations.append(
                    {
                        "name": match["name"],
                        "description": match["description"],
                        "muscle_group": match["muscle_group"],
                        "equipment": match["equipment"],
                        "icon": match.get("icon", ""),
                        "suitability": match["suitability_display"],
                        "recommendation": match["recommendation"],
                        "sets": match.get("sets"),
                        "reps": match.get("reps"),
                        "time_seconds": match.get("time_seconds"),
                        "estimated_minutes": str(est_minutes),
                        "score": score,
                        "score_display": str(score),
                        "show_details": "0",
                    }
                )
                self.rec_recommendations.sort(key=lambda r: (-r["score"], r["name"]))
                self._recommend_screen().ids.rec_list.data = self.rec_recommendations

    def _reset_plan(self, *, silent: bool = False) -> None:
        self.rec_plan = []
        self.rec_total_minutes = "0"
        rv = self._recommend_screen().ids.rec_plan_list
        rv.data = []
        rv.refresh_from_data()
        if not silent:
            self._set_rec_status("Plan cleared.")

    def clear_recommendation_plan(self) -> None:
        self._reset_plan(silent=False)

    def _validate_plan_time(self) -> None:
        try:
            limit = int(self.rec_max_minutes_text or "0")
        except ValueError:
            limit = 0
        try:
            total = int(self.rec_total_minutes or "0")
        except ValueError:
            total = 0
        if limit and total > int(limit * 1.1):
            self._set_rec_status(
                f"Plan time {total} min exceeds limit {limit} min (10% buffer). Remove or reorder.",
                error=True,
            )
        elif not self.rec_status_text or "exceeds limit" in self.rec_status_text.lower():
            self._set_rec_status("Plan ready.")

    def handle_start_training(self) -> None:
        if not self._require_user():
            return
        if not self.rec_plan:
            self._set_rec_status("Add at least one exercise to the plan.", error=True)
            return
        self._validate_plan_time()
        try:
            limit = int(self.rec_max_minutes_text or "0")
        except ValueError:
            limit = 0
        total = int(self.rec_total_minutes or "0")
        if limit and total > int(limit * 1.1):
            return
        session_plan: list[dict[str, Any]] = []
        missing: list[str] = []
        name_to_record = {r["name"]: r for r in self.records}
        for item in self.rec_plan:
            record = name_to_record.get(item["name"])
            if not record:
                missing.append(item["name"])
                continue
            session_plan.append(
                {
                    "name": record["name"],
                    "icon": record.get("icon", ""),
                    "muscle_group": record.get("muscle_group", ""),
                    "equipment": record.get("equipment", ""),
                    "sets": record.get("sets") or item.get("sets") or 3,
                    "reps": record.get("reps") or item.get("reps"),
                    "time_seconds": record.get("time_seconds") or item.get("time_seconds"),
                    "recommendation": record.get("recommendation", ""),
                    "estimated_minutes": item.get("estimated_minutes", "0"),
                }
            )
        if missing:
            self._set_rec_status(f"Missing data for: {', '.join(missing)}", error=True)
            return
        if not session_plan:
            self._set_rec_status("Could not start live mode. Add exercises again.", error=True)
            return
        self._begin_live_session(session_plan)
        try:
            self.ids.screen_manager.current = "live"
        except Exception:
            pass
        self._set_rec_status(f"Live mode started with {len(session_plan)} exercise(s).", error=False)

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
        if not self._require_user():
            return
        self.ids.screen_manager.current = "home"

    def go_browse(self) -> None:
        if not self._require_user():
            return
        self.ids.screen_manager.current = "browse"

    def go_add(self) -> None:
        if not self._require_user():
            return
        if self.goal_choice_options:
            self.add_goal_spinner_text = self._preferred_goal_label()
        self.ids.screen_manager.current = "add"

    def go_users(self) -> None:
        self.ids.screen_manager.current = "user"

    def go_history(self) -> None:
        if not self._require_user():
            return
        self.ids.screen_manager.current = "history"
        self._prefill_workout_date()
        self._load_history()

    def go_recommend(self) -> None:
        if not self._require_user():
            return
        self.ids.screen_manager.current = "recommend"
        if not self.rec_goal_spinner_text and self.goal_choice_options:
            self.rec_goal_spinner_text = self.goal_choice_options[0]
        try:
            rec_screen = self._recommend_screen()
            rec_screen.ids.rec_goal_spinner.text = self.rec_goal_spinner_text or ""
            rec_screen.ids.rec_max_time.text = self.rec_max_minutes_text
            rec_screen.ids.rec_list.data = self.rec_recommendations
        except Exception:
            pass
        self._refresh_recommendation_view()

    def go_live(self) -> None:
        if not self.live_active:
            self._set_rec_status("Start a session from Recommend first.", error=True)
            return
        try:
            self.ids.screen_manager.current = "live"
        except Exception:
            pass

    def go_summary(self) -> None:
        try:
            self.ids.screen_manager.current = "summary"
        except Exception:
            pass

    def start_new_session(self) -> None:
        self.live_active = False
        self.live_paused = False
        self.go_recommend()

    # --- Live mode helpers ---
    def _format_time(self, seconds: float) -> str:
        total = int(max(0, round(seconds)))
        minutes, secs = divmod(total, 60)
        return f"{minutes:02d}:{secs:02d}"

    def _current_live_exercise(self) -> Optional[dict[str, Any]]:
        if 0 <= self._live_current_index < len(self.live_exercises):
            return self.live_exercises[self._live_current_index]
        return None

    def _compute_set_target_seconds(self, exercise: Optional[dict[str, Any]]) -> float:
        if not exercise:
            return 30.0
        time_seconds = exercise.get("time_seconds")
        reps = exercise.get("reps")
        if time_seconds:
            return float(max(10, time_seconds))
        if reps:
            return float(max(20, reps * 4))
        return 30.0

    def _set_hint(self, message: str, *, color: tuple = (0.14, 0.4, 0.2, 1), clear_after: float = 3.0) -> None:
        self.live_hint_text = message
        self.live_hint_color = color
        if clear_after > 0:
            Clock.schedule_once(lambda *_: self._clear_hint(message), clear_after)

    def _clear_hint(self, expected: str) -> None:
        if self.live_hint_text == expected:
            self.live_hint_text = ""

    def _record_attempt(self, status: str) -> None:
        """Record the current exercise with a completion status once per exercise."""
        if self._live_current_logged:
            return
        exercise = self._current_live_exercise()
        if not exercise:
            return
        normalized_status = "skipped" if status == "skipped" else "completed"
        name = exercise.get("name", "Exercise")
        self._live_attempt_log.append({"name": name, "status": normalized_status})
        if normalized_status == "skipped":
            self._live_skipped.append(name)
        else:
            self._live_completed.append(name)
        self._live_current_logged = True

    def _update_live_upcoming(self) -> None:
        upcoming = [ex["name"] for ex in self.live_exercises[self._live_current_index + 1 :]]
        self.live_upcoming_display = ", ".join(upcoming) if upcoming else "None"

    def _update_live_labels(self) -> None:
        exercise = self._current_live_exercise()
        total_exercises = len(self.live_exercises)
        if not exercise:
            self.live_progress_display = "No session running"
            self.live_exercise_title = "No exercise running"
            self.live_icon_display = ""
            self.live_muscle_display = ""
            self.live_equipment_display = ""
            self.live_recommendation_display = ""
            self.live_instruction = ""
            self.live_current_set_display = ""
            self.live_state_display = "Not started"
            self.live_upcoming_display = "None"
            return
        total_sets = exercise.get("sets") or 1
        self._live_total_sets = total_sets
        self.live_progress_display = f"Exercise {self._live_current_index + 1}/{total_exercises} – {exercise.get('name', '')}"
        self.live_exercise_title = exercise.get("name", "Exercise")
        self.live_icon_display = f"Icon: {exercise.get('icon')}" if exercise.get("icon") else "No icon available"
        self.live_muscle_display = exercise.get("muscle_group", "")
        self.live_equipment_display = exercise.get("equipment", "")
        self.live_recommendation_display = exercise.get("recommendation", "")
        self.live_current_set_display = f"Set {self._live_current_set} of {total_sets}"
        self.live_instruction = self._build_instruction(exercise)
        self.live_state_display = f"{'Resting' if self._live_phase == 'rest' else 'In set'} (Set {self._live_current_set}/{total_sets})"
        self.live_exercise_timer = self._format_time(self._live_exercise_elapsed)
        self.live_set_timer = self._format_time(self._live_set_elapsed)
        self.live_rest_timer = self._format_time(self._live_rest_remaining) if self._live_phase == "rest" else "—"
        self._update_live_upcoming()
        self._update_tempo_hint()

    def _build_instruction(self, exercise: dict[str, Any]) -> str:
        reps = exercise.get("reps")
        time_seconds = exercise.get("time_seconds")
        set_prefix = f"Set {self._live_current_set}/{exercise.get('sets') or 1}: "
        if reps and time_seconds:
            return set_prefix + f"Target {reps} reps in ~{time_seconds}s"
        if reps:
            return set_prefix + f"Perform {reps} controlled reps"
        if time_seconds:
            return set_prefix + f"Hold for {time_seconds} seconds"
        return set_prefix + "Move with control and good form."

    def _start_live_clock(self) -> None:
        self._stop_live_clock()
        self._live_clock = Clock.schedule_interval(self._tick_live, 1.0)

    def _stop_live_clock(self) -> None:
        if self._live_clock is not None:
            try:
                self._live_clock.cancel()
            except Exception:
                pass
        self._live_clock = None

    def _begin_live_session(self, exercises: list[dict[str, Any]]) -> None:
        self.live_exercises = exercises
        self._live_current_index = 0
        self._live_current_set = 1
        self._live_set_elapsed = 0.0
        self._live_exercise_elapsed = 0.0
        self._live_rest_remaining = 0.0
        self._live_phase = "set"
        self._live_set_target_seconds = self._compute_set_target_seconds(self._current_live_exercise())
        self._live_completed = []
        self._live_skipped = []
        self._live_attempt_log = []
        self._live_goal_label = self.rec_goal_spinner_text or ""
        self._live_total_sets_completed = 0
        self._live_current_logged = False
        self.live_paused = False
        self.live_active = True
        self._live_session_started_at = datetime.now()
        self._update_live_labels()
        self._set_hint("Session started. Begin your first set!", color=(0.18, 0.4, 0.2, 1))
        self._start_live_clock()

    def _update_tempo_hint(self) -> None:
        exercise = self._current_live_exercise()
        if not exercise:
            self.live_tempo_hint = ""
            return
        reps = exercise.get("reps")
        if self._live_phase == "rest":
            self.live_tempo_hint = "Rest and breathe. Next set starts soon."
            return
        if reps:
            duration = self._live_set_target_seconds or max(1, reps * 4)
            per_rep = duration / max(reps, 1)
            expected_rep = min(reps, max(1, int(self._live_set_elapsed // max(per_rep, 1) + 1)))
            self.live_tempo_hint = f"You should be at repetition {expected_rep} now."
        else:
            target = int(exercise.get("time_seconds") or self._live_set_target_seconds or 0)
            if target:
                self.live_tempo_hint = f"Hold steady: {int(self._live_set_elapsed)}s of {target}s"
            else:
                self.live_tempo_hint = "Stay controlled and keep breathing."

    def _compute_completion_percentage(self, completed: int, total: int) -> float:
        """Return 0-100 completion percentage based on completed vs total planned items."""
        if total <= 0 or completed <= 0:
            return 0.0
        ratio = completed / total
        ratio = min(max(ratio, 0.0), 1.0)
        return round(ratio * 100, 2)

    def _tick_live(self, dt: float) -> None:
        if not self.live_active or self.live_paused:
            return
        exercise = self._current_live_exercise()
        if not exercise:
            return
        if self._live_phase == "rest":
            self._live_rest_remaining = max(0.0, self._live_rest_remaining - dt)
            self._live_exercise_elapsed += dt
            self.live_rest_timer = self._format_time(self._live_rest_remaining)
            self.live_exercise_timer = self._format_time(self._live_exercise_elapsed)
            if self._live_rest_remaining <= 0:
                self._start_next_set()
            return
        self._live_exercise_elapsed += dt
        self._live_set_elapsed += dt
        self.live_exercise_timer = self._format_time(self._live_exercise_elapsed)
        self.live_set_timer = self._format_time(self._live_set_elapsed)
        self._update_tempo_hint()
        if self._live_set_target_seconds and self._live_set_elapsed >= self._live_set_target_seconds:
            self._complete_current_set(auto=True)

    def _start_next_set(self) -> None:
        exercise = self._current_live_exercise()
        if not exercise:
            return
        total_sets = exercise.get("sets") or 1
        if self._live_current_set >= total_sets:
            self._advance_exercise()
            return
        self._live_phase = "set"
        self._live_current_set += 1
        self._live_set_elapsed = 0.0
        self._live_rest_remaining = 0.0
        self._live_set_target_seconds = self._compute_set_target_seconds(exercise)
        self.live_current_set_display = f"Set {self._live_current_set} of {total_sets}"
        self.live_state_display = "In set"
        self.live_rest_timer = "—"
        self._set_hint(f"Set {self._live_current_set} started", color=(0.16, 0.32, 0.6, 1))
        self._update_tempo_hint()
        self._update_live_labels()

    def _complete_current_set(self, *, auto: bool) -> None:
        exercise = self._current_live_exercise()
        if not exercise or not self.live_active:
            return
        self._live_total_sets_completed += 1
        total_sets = exercise.get("sets") or 1
        if self._live_current_set >= total_sets:
            self._advance_exercise()
            return
        self._live_phase = "rest"
        self._live_rest_remaining = float(self.live_rest_seconds)
        self.live_state_display = "Resting"
        self.live_rest_timer = self._format_time(self._live_rest_remaining)
        self._set_hint("Rest now – next set will start automatically.", color=(0.18, 0.4, 0.2, 1))
        self._update_tempo_hint()
        self._update_live_labels()

    def _advance_exercise(self, *, skipped: bool = False) -> None:
        self._record_attempt("skipped" if skipped else "completed")
        if self._live_current_index >= len(self.live_exercises) - 1:
            self.end_live_session(early=skipped)
            return
        self._live_current_index += 1
        self._live_current_logged = False
        self._live_current_set = 1
        self._live_set_elapsed = 0.0
        self._live_exercise_elapsed = 0.0
        self._live_rest_remaining = 0.0
        self._live_phase = "set"
        self._live_set_target_seconds = self._compute_set_target_seconds(self._current_live_exercise())
        self._update_live_labels()
        verb = "Skipped" if skipped else "Next exercise"
        self._set_hint(f"{verb}: {self.live_exercise_title}", color=(0.25, 0.32, 0.65, 1))

    def skip_current_exercise(self) -> None:
        if not self.live_active:
            return
        self._advance_exercise(skipped=True)

    def manual_next_exercise(self) -> None:
        if not self.live_active:
            return
        self._advance_exercise(skipped=False)

    def manual_complete_set(self) -> None:
        if not self.live_active or self._live_phase == "rest":
            return
        self._complete_current_set(auto=False)

    def toggle_live_pause(self) -> None:
        if not self.live_active:
            return
        self.live_paused = not self.live_paused
        if self.live_paused:
            self.live_state_display = "Paused"
            self._set_hint("Paused – timers stopped.", color=(0.65, 0.3, 0.18, 1))
        else:
            self.live_state_display = "Resting" if self._live_phase == "rest" else "In set"
            self._set_hint("Resumed.", color=(0.18, 0.4, 0.2, 1))

    def end_live_session(self, *, early: bool = False) -> None:
        if not self.live_active:
            return
        if self._current_live_exercise() and not self._live_current_logged:
            self._record_attempt("skipped" if early else "completed")
        now = datetime.now()
        if self._live_session_started_at:
            duration_seconds = int(max(1, (now - self._live_session_started_at).total_seconds()))
        else:
            duration_seconds = 0
        performed_at = now.isoformat(timespec="seconds")
        self.live_active = False
        self.live_paused = False
        self._live_phase = "idle"
        self._live_rest_remaining = 0.0
        self._stop_live_clock()
        self.live_rest_timer = "—"
        self.live_set_timer = self._format_time(self._live_set_elapsed)
        self.live_exercise_timer = self._format_time(self._live_exercise_elapsed)
        self.live_upcoming_display = "Session ended"
        attempts = self._collect_attempts(mark_unattempted_skipped=early)
        completed_count = sum(1 for att in attempts if att.get("status") == "completed")
        skipped_count = sum(1 for att in attempts if att.get("status") == "skipped")
        status = "Workout finished" if not early else "Workout ended early"
        summary = f"{status}. Completed {completed_count}, skipped {skipped_count}."
        self.live_state_display = status
        self.live_progress_display = summary
        self._set_hint(summary, color=(0.18, 0.4, 0.2, 1), clear_after=0)
        self._prepare_summary(duration_seconds, performed_at, attempts)
        self._log_live_workout(duration_seconds, performed_at, attempts)
        try:
            self.ids.screen_manager.current = "summary"
        except Exception:
            pass

    def _collect_attempts(self, *, mark_unattempted_skipped: bool) -> list[dict[str, str]]:
        """
        Return a full attempt list, optionally filling unattempted items as skipped when ending early.
        """
        attempts = list(self._live_attempt_log)
        attempt_counts: dict[str, int] = {}
        for att in attempts:
            name = att.get("name", "Exercise")
            attempt_counts[name] = attempt_counts.get(name, 0) + 1

        new_skips: list[dict[str, str]] = []
        if mark_unattempted_skipped:
            seen_counts: dict[str, int] = {}
            for ex in self.live_exercises:
                name = ex.get("name", "Exercise")
                seen_counts[name] = seen_counts.get(name, 0) + 1
                already_attempted = attempt_counts.get(name, 0)
                # If this occurrence has no matching attempt, mark it as skipped.
                if seen_counts[name] > already_attempted:
                    new_skips.append({"name": name, "status": "skipped"})
                    self._live_skipped.append(name)
                    attempt_counts[name] = attempt_counts.get(name, 0) + 1

        if not attempts and not new_skips:
            for ex in self.live_exercises:
                name = ex.get("name", "Exercise")
                new_skips.append({"name": name, "status": "skipped"})
                self._live_skipped.append(name)

        attempts.extend(new_skips)
        return attempts

    def _prepare_summary(self, duration_seconds: int, performed_at: str, attempts: list[dict[str, str]]) -> None:
        self.summary_duration_display = self._format_time(duration_seconds or 0)
        self.summary_sets_display = str(self._live_total_sets_completed)
        completed = [att.get("name", "Exercise") for att in attempts if att.get("status") == "completed"]
        skipped = [att.get("name", "Exercise") for att in attempts if att.get("status") == "skipped"]
        self.summary_completed_display = ", ".join(completed) if completed else "None"
        self.summary_skipped_display = ", ".join(skipped) if skipped else "None"
        attempts_lines = [
            f"{att.get('name', 'Exercise')}: {'Completed' if att.get('status') == 'completed' else 'Skipped'}"
            for att in attempts
        ]
        self.summary_attempts_display = "\n".join(attempts_lines) if attempts_lines else "No exercises attempted."
        self.summary_goal_display = self._live_goal_label or "—"
        self.summary_performed_at_display = performed_at

    def _log_live_workout(self, duration_seconds: int, performed_at: str, attempts: list[dict[str, str]]) -> None:
        if not self.current_user_id:
            return
        exercise_names = [att.get("name", "Exercise") for att in attempts]
        duration_minutes = int(max(1, (duration_seconds + 59) // 60)) if duration_seconds else 1
        try:
            exercise_database.log_workout(
                user_id=self.current_user_id,
                performed_at=performed_at,
                duration_minutes=duration_minutes,
                exercises=exercise_names,
                goal=self._live_goal_label or "",
                duration_seconds=duration_seconds or duration_minutes * 60,
                total_sets_completed=self._live_total_sets_completed,
                exercise_statuses=[(att.get("name", "Exercise"), att.get("status", "completed")) for att in attempts],
            )
        except (ValueError, sqlite3.DatabaseError) as exc:
            self._set_history_status(f"Could not log workout: {exc}", error=True)
            return
        self._set_history_status("Workout logged from live session.")
        self._load_history()


class ExerciseApp(App):
    def build(self):
        exercise_database.initialize_database()
        Builder.load_string(KV)
        return RootWidget()


if __name__ == "__main__":
    ExerciseApp().run()
