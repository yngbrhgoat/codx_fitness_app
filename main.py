from __future__ import annotations

import calendar
import sqlite3
from datetime import date, datetime
from functools import partial
from pathlib import Path
from typing import Any, Optional

from kivy.config import Config

# Avoid probing input devices via xinput under Xwayland.
Config.remove_option("input", "%(name)s")

from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.metrics import dp

import exercise_database

KV = """
#:import dp kivy.metrics.dp

<Button>:
    background_normal: ""
    background_down: ""
    background_color: 0.18, 0.4, 0.85, 1
    color: 1, 1, 1, 1

<AppSpinnerOption@SpinnerOption>:
    background_normal: ""
    background_down: ""
    background_color: 0.92, 0.96, 1, 1
    color: 0, 0, 0, 1

<Spinner>:
    option_cls: "AppSpinnerOption"
    on_text: app.root.confirm_value_input(self)

<TextInput>:
    on_focus: app.root.confirm_value_input(self) if not self.focus else None

<FilterLabel@Label>:
    color: 0.2, 0.2, 0.25, 1
    font_size: "13sp"
    size_hint_y: None
    height: dp(18)
    text_size: self.size
    valign: "middle"

<WrapLabel@Label>:
    text_size: self.width, None
    size_hint_y: None
    height: self.texture_size[1]
    halign: "left"
    valign: "middle"

<InstructionBadge@Label>:
    text_size: self.width - dp(20), None
    size_hint_y: None
    height: self.texture_size[1] + dp(14)
    padding: dp(10), dp(6)
    font_size: "20sp"
    bold: True
    color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: 0.2, 0.45, 0.8, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]

<ProgressRing>:
    canvas:
        Color:
            rgba: root.background_color
        Line:
            width: root.thickness
            circle: (self.center_x, self.center_y, min(self.width, self.height) / 2 - root.thickness / 2)
        Color:
            rgba: root.color
        Line:
            width: root.thickness
            cap: "round"
            circle: (self.center_x, self.center_y, min(self.width, self.height) / 2 - root.thickness / 2, 0, -360 * root.progress)

<GridInfoLabel@Label>:
    text_size: self.size
    halign: "left"
    valign: "middle"
    shorten: True
    shorten_from: "right"

<NavButton@Button>:
    background_normal: ""
    background_down: ""
    background_color: 0.22, 0.32, 0.45, 1
    color: 1, 1, 1, 1
    font_size: "14sp"

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
    BoxLayout:
        orientation: "horizontal"
        spacing: dp(10)
        size_hint_y: None
        height: self.minimum_height
        Image:
            source: root.icon_source
            size_hint: None, None
            size: (dp(64), dp(64)) if root.icon_source else (0, 0)
            fit_mode: "contain"
            opacity: 1 if root.icon_source else 0
        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
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
        GridInfoLabel:
            text: "Suitability: {}".format(root.suitability_display)
            color: 0.2, 0.2, 0.3, 1
        GridInfoLabel:
            text: "Muscle: {}".format(root.muscle_group)
            color: 0.15, 0.15, 0.2, 1
        GridInfoLabel:
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
        text: "Duration: {}".format(root.duration_display)
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
    height: dp(240)
    canvas.before:
        Color:
            rgba: 0.9, 0.95, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8,]
    BoxLayout:
        orientation: "horizontal"
        spacing: dp(8)
        size_hint_y: None
        height: self.minimum_height
        Image:
            source: root.icon_source
            size_hint: None, None
            size: (dp(42), dp(42)) if root.icon_source else (0, 0)
            fit_mode: "contain"
            opacity: 1 if root.icon_source else 0
        Label:
            text: root.name
            font_size: "17sp"
            bold: True
            color: 0.1, 0.12, 0.2, 1
            size_hint_y: None
            height: self.texture_size[1]
    WrapLabel:
        text: root.description
        color: 0.1, 0.12, 0.18, 1
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1]
    WrapLabel:
        text: "Muscle: {} | Equipment: {}".format(root.muscle_group, root.equipment)
        color: 0.2, 0.2, 0.3, 1
        size_hint_y: None
        height: self.texture_size[1]
    WrapLabel:
        text: "Suitability: {} | Est. time: {} min".format(root.suitability, root.estimated_minutes)
        color: 0.2, 0.2, 0.3, 1
        size_hint_y: None
        height: self.texture_size[1]
    WrapLabel:
        text: "Recommendation score: {}".format(root.score_display)
        color: 0.16, 0.16, 0.22, 1
        size_hint_y: None
        height: self.texture_size[1]
    WrapLabel:
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
            on_release: app.root.open_recommendation_details(root.name)

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
    Image:
        source: root.icon_source
        size_hint: None, None
        size: (dp(42), dp(42)) if root.icon_source else (0, 0)
        fit_mode: "contain"
        opacity: 1 if root.icon_source else 0
    Label:
        text: root.display
        color: 0.18, 0.18, 0.24, 1
        text_size: self.width, self.height
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

<DatePickerPopup>:
    size_hint: None, None
    size: dp(360), dp(450)
    auto_dismiss: False
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]
        BoxLayout:
            size_hint_y: None
            height: dp(26)
            spacing: dp(8)
            Label:
                text: "Select date"
                bold: True
                color: 0.12, 0.14, 0.22, 1
                valign: "middle"
                text_size: self.size
            Label:
                text: "Selected: {}".format(root.selected_label)
                color: 0.18, 0.18, 0.24, 1
                halign: "right"
                valign: "middle"
                text_size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(36)
            spacing: dp(8)
            Button:
                text: "<"
                size_hint_x: None
                width: dp(44)
                background_normal: ""
                background_down: ""
                background_color: 0.18, 0.4, 0.85, 1
                color: 1, 1, 1, 1
                on_release: root.shift_month(-1)
            Label:
                text: root.month_label
                bold: True
                color: 0.12, 0.14, 0.22, 1
                halign: "center"
                valign: "middle"
                text_size: self.size
            Button:
                text: ">"
                size_hint_x: None
                width: dp(44)
                background_normal: ""
                background_down: ""
                background_color: 0.18, 0.4, 0.85, 1
                color: 1, 1, 1, 1
                on_release: root.shift_month(1)
        BoxLayout:
            size_hint_y: None
            height: dp(32)
            spacing: dp(6)
            Button:
                text: "<< Year"
                size_hint_x: None
                width: dp(84)
                background_normal: ""
                background_down: ""
                background_color: 0.18, 0.4, 0.85, 1
                color: 1, 1, 1, 1
                on_release: root.shift_year(-1)
            Button:
                text: "-3 mo"
                size_hint_x: None
                width: dp(70)
                background_normal: ""
                background_down: ""
                background_color: 0.18, 0.4, 0.85, 1
                color: 1, 1, 1, 1
                on_release: root.shift_month(-3)
            Widget:
            Button:
                text: "+3 mo"
                size_hint_x: None
                width: dp(70)
                background_normal: ""
                background_down: ""
                background_color: 0.18, 0.4, 0.85, 1
                color: 1, 1, 1, 1
                on_release: root.shift_month(3)
            Button:
                text: "Year >>"
                size_hint_x: None
                width: dp(84)
                background_normal: ""
                background_down: ""
                background_color: 0.18, 0.4, 0.85, 1
                color: 1, 1, 1, 1
                on_release: root.shift_year(1)
        GridLayout:
            id: day_grid
            cols: 7
            spacing: dp(6)
            padding: dp(4)
            size_hint_y: None
            row_default_height: dp(32)
            row_force_default: True
            col_force_default: True
            col_default_width: dp(40)
            height: dp(260)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Button:
                text: "Today"
                on_release: root.select_today()
            Button:
                text: "Use date"
                on_release: root.confirm_selection()
            Button:
                text: "Cancel"
                on_release: root.dismiss()

<WorkoutLogModal>:
    size_hint: 0.96, 0.9
    auto_dismiss: False
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]
        Label:
            text: "Log a completed workout"
            font_size: "18sp"
            bold: True
            color: 0.12, 0.14, 0.22, 1
            size_hint_y: None
            height: dp(24)
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                GridLayout:
                    cols: 2
                    spacing: dp(8)
                    row_default_height: dp(34)
                    size_hint_y: None
                    height: self.minimum_height
                    WrapLabel:
                        text: "Workout date (YYYY-MM-DD)"
                        color: 0.18, 0.18, 0.22, 1
                    BoxLayout:
                        spacing: dp(6)
                        TextInput:
                            id: workout_date_input
                            multiline: False
                            readonly: True
                            hint_text: "pick date"
                        Button:
                            text: "Pick"
                            size_hint_x: None
                            width: dp(70)
                            on_release: app.root.open_date_picker(workout_date_input)
                    WrapLabel:
                        text: "Duration (minutes)"
                        color: 0.18, 0.18, 0.22, 1
                    TextInput:
                        id: duration_input
                        multiline: False
                        input_filter: "int"
                        hint_text: "e.g. 45"
                    WrapLabel:
                        text: "Goal (optional)"
                        color: 0.18, 0.18, 0.22, 1
                    Spinner:
                        id: workout_goal_spinner
                        text: app.root.workout_goal_spinner_text
                        values: app.root.workout_goal_options
                        on_text: app.root.workout_goal_spinner_text = self.text
                    WrapLabel:
                        text: "Total sets completed (optional)"
                        color: 0.18, 0.18, 0.22, 1
                    TextInput:
                        id: total_sets_input
                        multiline: False
                        input_filter: "int"
                        hint_text: "e.g. 12"
                    WrapLabel:
                        text: "Exercises (comma or newline separated)"
                        color: 0.18, 0.18, 0.22, 1
                    TextInput:
                        id: exercises_input
                        multiline: True
                        size_hint_y: None
                        height: dp(80)
                        hint_text: "Push-Up, Plank, Jump Rope"
                    WrapLabel:
                        text: "Filter exercises"
                        color: 0.18, 0.18, 0.22, 1
                    BoxLayout:
                        spacing: dp(6)
                        TextInput:
                            id: history_exercise_filter_input
                            multiline: False
                            hint_text: "type to search"
                            on_text: app.root.filter_history_exercise_options(self.text)
                        Button:
                            text: "Clear"
                            size_hint_x: None
                            width: dp(70)
                            on_release: app.root.clear_history_exercise_filter()
                    WrapLabel:
                        text: "Add exercise from list"
                        color: 0.18, 0.18, 0.22, 1
                    BoxLayout:
                        spacing: dp(6)
                        Spinner:
                            id: history_exercise_spinner
                            text: app.root.history_exercise_spinner_text
                            values: app.root.history_exercise_filtered_options
                            on_text: app.root.history_exercise_spinner_text = self.text
                        Button:
                            text: "Add"
                            size_hint_x: None
                            width: dp(80)
                            on_release: app.root.add_history_exercise_from_menu()
        WrapLabel:
            text: app.root.history_status_text
            color: app.root.history_status_color
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Button:
                text: "Save workout"
                on_release: app.root.handle_add_workout()
            Button:
                text: "Cancel"
                on_release: root.dismiss()

<GoalPromptModal>:
    size_hint: 0.9, 0.55
    auto_dismiss: False
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]
        Label:
            text: "Set your training goal"
            font_size: "18sp"
            bold: True
            color: 0.12, 0.14, 0.22, 1
            size_hint_y: None
            height: dp(24)
        WrapLabel:
            text: "Choose a goal for {}.".format(app.root.current_user_display)
            color: 0.18, 0.18, 0.24, 1
        Spinner:
            id: goal_prompt_spinner
            text: app.root.user_profile_goal
            values: app.root.user_goal_options
            on_text: app.root.user_profile_goal = self.text
        WrapLabel:
            text: app.root.user_profile_status_text
            color: app.root.user_profile_status_color
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Button:
                text: "Save goal"
                on_release: app.root.save_user_profile() and root.dismiss()
            Button:
                text: "Skip for now"
                on_release: app.root.skip_goal_prompt()

<RecommendationDetailsModal>:
    size_hint: 0.96, 0.92
    auto_dismiss: False
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]
        Label:
            text: "Exercise details"
            font_size: "18sp"
            bold: True
            color: 0.12, 0.14, 0.22, 1
            size_hint_y: None
            height: dp(24)
        WrapLabel:
            text: root.exercise_name
            font_size: "20sp"
            bold: True
            color: 0.1, 0.12, 0.2, 1
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                WrapLabel:
                    text: root.description
                    color: 0.16, 0.18, 0.24, 1
                GridLayout:
                    cols: 2
                    spacing: dp(8)
                    row_default_height: dp(24)
                    size_hint_y: None
                    height: self.minimum_height
                    GridInfoLabel:
                        text: "Goal"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: root.goal_label or "—"
                        color: 0.16, 0.2, 0.3, 1
                    GridInfoLabel:
                        text: "Muscle"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: root.muscle_group or "—"
                        color: 0.16, 0.2, 0.3, 1
                    GridInfoLabel:
                        text: "Equipment"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: root.equipment or "—"
                        color: 0.16, 0.2, 0.3, 1
                    GridInfoLabel:
                        text: "Suitability"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: root.suitability or "—"
                        color: 0.16, 0.2, 0.3, 1
                    GridInfoLabel:
                        text: "Est. time"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: "{} min".format(root.estimated_minutes) if root.estimated_minutes else "—"
                        color: 0.16, 0.2, 0.3, 1
                    GridInfoLabel:
                        text: "Score"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: root.score_display or "—"
                        color: 0.16, 0.2, 0.3, 1
                    GridInfoLabel:
                        text: "Sets"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: root.sets_display
                        color: 0.16, 0.2, 0.3, 1
                    GridInfoLabel:
                        text: "Reps"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: root.reps_display
                        color: 0.16, 0.2, 0.3, 1
                    GridInfoLabel:
                        text: "Time"
                        color: 0.18, 0.18, 0.22, 1
                    WrapLabel:
                        text: root.time_display
                        color: 0.16, 0.2, 0.3, 1
                WrapLabel:
                    text: "Recommendation: {}".format(root.recommendation)
                    color: 0.16, 0.2, 0.3, 1
        BoxLayout:
            size_hint_y: None
            height: dp(36)
            spacing: dp(10)
            padding: dp(6), 0
            Widget:
            Button:
                text: "Add to plan"
                size_hint: None, None
                width: dp(140)
                height: dp(32)
                on_release: app.root.add_recommendation_to_plan(root.exercise_name); root.dismiss()
            Button:
                text: "Close"
                size_hint: None, None
                width: dp(110)
                height: dp(32)
                on_release: root.dismiss()
            Widget:

<LiveScreen>:
    ScrollView:
        do_scroll_x: False
        BoxLayout:
            orientation: "vertical"
            padding: dp(16)
            spacing: dp(12)
            size_hint_y: None
            height: self.minimum_height
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
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
                size_hint_y: None
                height: dp(38) if app.root.live_signal_text else dp(0)
                padding: dp(10), dp(6)
                canvas.before:
                    Color:
                        rgba: app.root.live_signal_color if app.root.live_signal_text else (0, 0, 0, 0)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8,]
                Label:
                    text: app.root.live_signal_text
                    color: 1, 1, 1, 1
                    bold: True
                    opacity: 1 if app.root.live_signal_text else 0
            BoxLayout:
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(6)
                size_hint_y: None
                height: self.minimum_height
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
                Image:
                    source: app.root.live_icon_source
                    size_hint_y: None
                    height: dp(140) if app.root.live_icon_source else dp(0)
                    fit_mode: "contain"
                    opacity: 1 if app.root.live_icon_source else 0
                Label:
                    text: app.root.live_icon_display
                    color: 0.18, 0.2, 0.32, 1
                    size_hint_y: None
                    height: self.texture_size[1] if not app.root.live_icon_source else dp(0)
                    opacity: 0 if app.root.live_icon_source else 1
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
                Label:
                    text: "Planned duration: {}".format(app.root.live_exercise_target_display)
                    color: 0.14, 0.22, 0.34, 1
                    size_hint_y: None
                    height: self.texture_size[1]
                BoxLayout:
                    size_hint_y: None
                    height: dp(36)
                    spacing: dp(8)
                    Button:
                        text: "Show details" if not app.root.live_details_expanded else "Hide details"
                        size_hint_x: None
                        width: dp(150)
                        on_release: app.root.toggle_live_details()
                    Label:
                        text: "Set: {}".format(app.root.live_current_set_display)
                        color: 0.16, 0.18, 0.24, 1
                        text_size: self.size
                        valign: "middle"
            BoxLayout:
                orientation: "vertical"
                padding: dp(10)
                spacing: dp(6)
                size_hint_y: None
                height: self.minimum_height if app.root.live_details_expanded else dp(0)
                opacity: 1 if app.root.live_details_expanded else 0
                canvas.before:
                    Color:
                        rgba: (0.95, 0.98, 1, 1) if app.root.live_details_expanded else (0, 0, 0, 0)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [10,]
                WrapLabel:
                    text: app.root.live_exercise_description
                    color: 0.14, 0.16, 0.24, 1
                WrapLabel:
                    text: app.root.live_recommendation_display
                    color: 0.16, 0.2, 0.3, 1
            BoxLayout:
                size_hint_y: None
                height: dp(176)
                spacing: dp(12)
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.94, 0.97, 1, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8,]
                ProgressRing:
                    size_hint: None, None
                    size: dp(110), dp(110)
                    thickness: dp(4)
                    color: app.root.live_progress_color
                    progress: app.root.live_exercise_progress
                    BoxLayout:
                        size_hint: None, None
                        size: self.parent.size
                        pos: self.parent.pos
                        padding: dp(12)
                        Label:
                            text: app.root.live_progress_timer
                            font_size: "16sp"
                            bold: True
                            color: 0.1, 0.12, 0.2, 1
                            halign: "center"
                            valign: "middle"
                            text_size: self.size
                BoxLayout:
                    orientation: "vertical"
                    spacing: dp(8)
                    BoxLayout:
                        size_hint_y: None
                        height: dp(78)
                        spacing: dp(8)
                        BoxLayout:
                            orientation: "vertical"
                            padding: dp(6)
                            Label:
                                text: "Set time"
                                font_size: "13sp"
                                color: 0.16, 0.18, 0.24, 1
                                size_hint_y: None
                                height: dp(18)
                            Label:
                                text: app.root.live_set_timer
                                font_size: "22sp"
                                bold: True
                                color: 0.08, 0.12, 0.22, 1
                        BoxLayout:
                            orientation: "vertical"
                            padding: dp(6)
                            Label:
                                text: "Break timer"
                                font_size: "13sp"
                                color: 0.16, 0.18, 0.24, 1
                                size_hint_y: None
                                height: dp(18)
                            Label:
                                text: app.root.live_rest_timer
                                font_size: "22sp"
                                bold: True
                                color: 0.08, 0.12, 0.22, 1
                    BoxLayout:
                        size_hint_y: None
                        height: dp(64)
                        spacing: dp(8)
                        BoxLayout:
                            orientation: "vertical"
                            padding: dp(6)
                            Label:
                                text: "Exercise time"
                                font_size: "12sp"
                                color: 0.16, 0.18, 0.24, 1
                                size_hint_y: None
                                height: dp(16)
                            Label:
                                text: app.root.live_exercise_timer
                                font_size: "18sp"
                                bold: True
                                color: 0.08, 0.12, 0.22, 1
                        BoxLayout:
                            orientation: "vertical"
                            padding: dp(6)
                            Label:
                                text: "Per-set target"
                                font_size: "12sp"
                                color: 0.16, 0.18, 0.24, 1
                                size_hint_y: None
                                height: dp(16)
                            Label:
                                text: app.root.live_set_target_display
                                font_size: "18sp"
                                bold: True
                                color: 0.08, 0.12, 0.22, 1
            BoxLayout:
                size_hint_y: None
                height: dp(52)
                spacing: dp(10)
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.96, 0.98, 1, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [8,]
                Button:
                    text: "Start workout"
                    size_hint: None, None
                    width: dp(160) if app.root.live_active and not app.root.live_started else dp(0)
                    height: dp(34)
                    opacity: 1 if app.root.live_active and not app.root.live_started else 0
                    disabled: not app.root.live_active or app.root.live_started
                    on_release: app.root.start_live_workout()
                BoxLayout:
                    size_hint_x: None
                    width: dp(190)
                    spacing: dp(6)
                    Label:
                        text: "Break (s)"
                        color: 0.16, 0.18, 0.24, 1
                        size_hint_x: None
                        width: dp(80)
                    TextInput:
                        id: live_break_input
                        text: app.root.live_rest_setting_text
                        multiline: False
                        input_filter: "int"
                        size_hint_x: None
                        width: dp(90)
                        on_text_validate: app.root.set_live_rest_seconds(self.text)
                        on_focus: app.root.set_live_rest_seconds(self.text) if not self.focus else None
                Label:
                    text: "Applies after each exercise and when tapping Next."
                    color: 0.18, 0.2, 0.28, 1
            InstructionBadge:
                text: app.root.live_instruction
            WrapLabel:
                text: app.root.live_tempo_hint
                color: 0.12, 0.18, 0.34, 1
            WrapLabel:
                text: app.root.live_hint_text
                color: app.root.live_hint_color
                bold: True
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
            Widget:
                size_hint_y: None
                height: dp(8)

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
        WrapLabel:
            text: "Live Mode: build a plan under Recommend, then press Start."
            font_size: "18sp"
            bold: True
            color: 0.16, 0.16, 0.22, 1
            text_size: self.width, None
            halign: "center"
        BoxLayout:
            orientation: "vertical"
            padding: dp(12)
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height
            canvas.before:
                Color:
                    rgba: 0.92, 0.97, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [10,]
            Label:
                text: "Your profile"
                font_size: "17sp"
                bold: True
                color: 0.12, 0.14, 0.22, 1
                size_hint_y: None
                height: dp(22)
            WrapLabel:
                text: "Current user: [b]{}[/b]".format(app.root.current_user_display)
                markup: True
                font_size: "16sp"
                color: 0.12, 0.14, 0.22, 1
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
                    text: app.root.user_profile_goal
                    values: app.root.user_goal_options
                    on_text: app.root.user_profile_goal = self.text
            BoxLayout:
                size_hint_y: None
                height: dp(36)
                spacing: dp(8)
                Button:
                    text: "Save profile"
                    on_release: app.root.save_user_profile()
            WrapLabel:
                text: app.root.user_profile_status_text
                color: app.root.user_profile_status_color
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
                        background_color: 0.16, 0.6, 0.65, 1
                        color: 1, 1, 1, 1
                        on_release: app.root.go_browse()
                    Button:
                        text: "Add"
                        font_size: "26sp"
                        bold: True
                        background_normal: ""
                        background_color: 0.2, 0.45, 0.85, 1
                        color: 1, 1, 1, 1
                        on_release: app.root.go_add()
                    Button:
                        text: "Users"
                        font_size: "26sp"
                        bold: True
                        background_normal: ""
                        background_color: 0.9, 0.55, 0.15, 1
                        color: 1, 1, 1, 1
                        on_release: app.root.go_users()
                BoxLayout:
                    size_hint_y: None
                    height: dp(70)
                    spacing: dp(12)
                    Button:
                        text: "History"
                        font_size: "26sp"
                        bold: True
                        background_normal: ""
                        background_color: 0.2, 0.65, 0.3, 1
                        color: 1, 1, 1, 1
                        on_release: app.root.go_history()
                    Button:
                        text: "Recommend"
                        font_size: "26sp"
                        bold: True
                        background_normal: ""
                        background_color: 0.85, 0.35, 0.25, 1
                        color: 1, 1, 1, 1
                        on_release: app.root.go_recommend()

<BrowseScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
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
                col_force_default: True
                col_default_width: self.width / 3
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
                    background_normal: ""
                    background_down: ""
                    background_color: app.root.filter_goal_color
                    color: app.root.filter_goal_text_color
                Spinner:
                    id: muscle_spinner
                    text: app.root.muscle_spinner_text
                    values: app.root.muscle_options
                    on_text: app.root.on_muscle_change(self.text)
                    background_normal: ""
                    background_down: ""
                    background_color: app.root.filter_muscle_color
                    color: app.root.filter_muscle_text_color
                Spinner:
                    id: equipment_spinner
                    text: app.root.equipment_spinner_text
                    values: app.root.equipment_options
                    on_text: app.root.on_equipment_change(self.text)
                    background_normal: ""
                    background_down: ""
                    background_color: app.root.filter_equipment_color
                    color: app.root.filter_equipment_text_color
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
                    rgba: 1, 1, 1, 1
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
                WrapLabel:
                    text: "Name"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: name_input
                    multiline: False
                    hint_text: "e.g. Bulgarian Split Squat"
                WrapLabel:
                    text: "Description"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: description_input
                    multiline: True
                    size_hint_y: None
                    height: dp(64)
                    hint_text: "Short overview"
                WrapLabel:
                    text: "Muscle group (choose known)"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: muscle_add_spinner
                    text: app.root.add_muscle_spinner_text
                    values: app.root.muscle_choice_options
                    on_text: app.root.add_muscle_spinner_text = self.text
                WrapLabel:
                    text: "Allowed muscle groups"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.muscle_choice_display
                    color: 0.2, 0.2, 0.28, 1
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]
                WrapLabel:
                    text: "Required equipment"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: equipment_add_spinner
                    text: app.root.add_equipment_spinner_text
                    values: app.root.equipment_choice_options
                    on_text: app.root.add_equipment_spinner_text = self.text
                WrapLabel:
                    text: "Allowed equipment"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.equipment_choice_display
                    color: 0.2, 0.2, 0.28, 1
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]
                WrapLabel:
                    text: "Equipment default"
                    color: 0.18, 0.18, 0.22, 1
                Label:
                    text: app.root.add_equipment_spinner_text or "Bodyweight"
                    color: 0.2, 0.2, 0.28, 1
                    size_hint_y: None
                    height: dp(18)
                WrapLabel:
                    text: "Icon (optional)"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: icon_spinner
                    text: app.root.icon_choice_spinner_text
                    values: app.root.icon_choice_options
                    on_text: app.root.on_icon_choice_change(self.text)
                WrapLabel:
                    text: "Icon preview"
                    color: 0.18, 0.18, 0.22, 1
                Image:
                    source: app.root.add_icon_source
                    size_hint_y: None
                    height: dp(80) if app.root.add_icon_source else dp(0)
                    fit_mode: "contain"
                    opacity: 1 if app.root.add_icon_source else 0
                WrapLabel:
                    text: "Target suitability goal"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: goal_add_spinner
                    text: app.root.add_goal_spinner_text
                    values: app.root.goal_choice_options
                    on_text: app.root.add_goal_spinner_text = self.text
                WrapLabel:
                    text: "Suitability rating (1-10, default 5)"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: rating_spinner
                    text: app.root.rating_spinner_text
                    values: ("1","2","3","4","5","6","7","8","9","10")
                WrapLabel:
                    text: "Recommended sets (optional, e.g. 3)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: sets_input
                    multiline: False
                    input_filter: "int"
                    hint_text: "e.g. 3 (optional)"
                WrapLabel:
                    text: "Recommended reps (optional, e.g. 10)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: reps_input
                    multiline: False
                    input_filter: "int"
                    hint_text: "e.g. 10 (optional)"
                WrapLabel:
                    text: "Recommended time (sec, optional, e.g. 45)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: time_input
                    multiline: False
                    input_filter: "int"
                    hint_text: "e.g. 45 (seconds, optional)"
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(10)
                Button:
                    text: "Add Exercise"
                    on_press: app.root.handle_add_exercise()
            WrapLabel:
                text: app.root.status_text
                color: app.root.status_color

<UserScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
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
                WrapLabel:
                    text: "Select user"
                    font_size: "18sp"
                    bold: True
                    color: 0.12, 0.14, 0.22, 1
                    text_size: self.width, None
                    halign: "center"
                AnchorLayout:
                    anchor_x: "center"
                    size_hint_y: None
                    height: dp(44)
                    Spinner:
                        id: user_spinner
                        text: app.root.user_spinner_text
                        values: app.root.user_options
                        on_text: app.root.on_user_selected(self.text)
                        size_hint_x: None
                        width: dp(240)
                        text_size: self.size
                        halign: "center"
                        valign: "middle"
                WrapLabel:
                    text: "Pick a user to get started."
                    color: 0.2, 0.2, 0.3, 1
                    text_size: self.width, None
                    halign: "center"
                WrapLabel:
                    text: "Current user: {}".format(app.root.current_user_display)
                    color: 0.2, 0.2, 0.3, 1
                    text_size: self.width, None
                    halign: "center"
                AnchorLayout:
                    anchor_x: "center"
                    size_hint_y: None
                    height: dp(40)
                    Button:
                        text: "Open history"
                        size_hint_x: None
                        width: dp(160)
                        on_release: app.root.go_history()
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
                    text: "New here?"
                    font_size: "17sp"
                    bold: True
                    color: 0.12, 0.14, 0.22, 1
                    size_hint_y: None
                    height: dp(24)
                WrapLabel:
                    text: "Create a profile with a username and goal."
                    color: 0.2, 0.2, 0.3, 1
                    text_size: self.width, None
                    halign: "center"
                AnchorLayout:
                    anchor_x: "center"
                    size_hint_y: None
                    height: dp(40)
                    Button:
                        text: "Register"
                        size_hint_x: None
                        width: dp(160)
                        on_release: app.root.go_register()
                WrapLabel:
                    text: app.root.user_status_text
                    color: app.root.user_status_color

<RegisterScreen>:
    AnchorLayout:
        anchor_y: "top"
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            orientation: "vertical"
            padding: dp(12), dp(6), dp(12), dp(12)
            spacing: dp(10)
            size_hint_y: None
            height: self.minimum_height
            Label:
                text: "Register new user"
                font_size: "18sp"
                bold: True
                color: 0.12, 0.14, 0.22, 1
                size_hint_y: None
                height: dp(26)
            WrapLabel:
                text: "Set a username and choose a goal to get started."
                color: 0.2, 0.2, 0.3, 1
            GridLayout:
                cols: 2
                spacing: dp(8)
                row_default_height: dp(34)
                size_hint_y: None
                height: self.minimum_height
                WrapLabel:
                    text: "Username"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: register_username_input
                    hint_text: "e.g. alex"
                    multiline: False
                WrapLabel:
                    text: "Display name (optional)"
                    color: 0.18, 0.18, 0.22, 1
                TextInput:
                    id: register_display_input
                    hint_text: "Name shown in app"
                    multiline: False
                WrapLabel:
                    text: "Goal"
                    color: 0.18, 0.18, 0.22, 1
                Spinner:
                    id: register_goal_spinner
                    text: app.root.register_goal_spinner_text
                    values: app.root.user_goal_options
                    on_text: app.root.register_goal_spinner_text = self.text
            WrapLabel:
                text: app.root.register_status_text
                color: app.root.register_status_color
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(8)
                Button:
                    text: "Register"
                    on_release: app.root.handle_register_user()
                Button:
                    text: "Cancel"
                    on_release: app.root.go_users()

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
                    rgba: 1, 1, 1, 1
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
            WrapLabel:
                text: "Current user: {}".format(app.root.current_user_display)
                color: 0.2, 0.2, 0.3, 1
            GridLayout:
                cols: 2
                spacing: dp(8)
                row_default_height: dp(34)
                size_hint_y: None
                height: self.minimum_height
                WrapLabel:
                    text: "Start date (YYYY-MM-DD)"
                    color: 0.18, 0.18, 0.22, 1
                BoxLayout:
                    spacing: dp(6)
                    TextInput:
                        id: start_date_input
                        multiline: False
                        readonly: True
                        hint_text: "optional"
                    Button:
                        text: "Pick"
                        size_hint_x: None
                        width: dp(70)
                        on_release: app.root.open_date_picker(start_date_input)
                WrapLabel:
                    text: "End date (YYYY-MM-DD)"
                    color: 0.18, 0.18, 0.22, 1
                BoxLayout:
                    spacing: dp(6)
                    TextInput:
                        id: end_date_input
                        multiline: False
                        readonly: True
                        hint_text: "optional"
                    Button:
                        text: "Pick"
                        size_hint_x: None
                        width: dp(70)
                        on_release: app.root.open_date_picker(end_date_input)
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(10)
                padding: dp(12), 0, dp(12), 0
                Button:
                    text: "Clear filter"
                    size_hint_x: None
                    width: dp(150)
                    on_release: app.root.clear_history_filter()
                Button:
                    text: "Apply filter"
                    size_hint_x: None
                    width: dp(150)
                    on_release: app.root.apply_history_filter()
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(6)
                canvas.before:
                    Color:
                        rgba: 0.93, 0.96, 1, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [10,]
                Label:
                    text: "Stats"
                    bold: True
                    font_size: "16sp"
                    color: 0.12, 0.14, 0.22, 1
                    size_hint_y: None
                    height: dp(22)
                Label:
                    text: "Total workouts: [b]{}[/b]".format(app.root.stats_total_workouts)
                    markup: True
                    font_size: "15sp"
                    color: 0.16, 0.18, 0.26, 1
                    text_size: self.width, None
                    halign: "left"
                    size_hint_y: None
                    height: dp(20)
                Label:
                    text: "Total time: [b]{} min[/b]".format(app.root.stats_total_minutes)
                    markup: True
                    font_size: "15sp"
                    color: 0.16, 0.18, 0.26, 1
                    text_size: self.width, None
                    halign: "left"
                    size_hint_y: None
                    height: dp(20)
                Label:
                    text: "Top exercise: [b]{}[/b]".format(app.root.stats_top_exercise)
                    markup: True
                    font_size: "15sp"
                    color: 0.16, 0.18, 0.26, 1
                    text_size: self.width, None
                    halign: "left"
                    size_hint_y: None
                    height: dp(20)
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(10)
                padding: dp(12), 0, dp(12), 0
                Button:
                    text: "Log a completed workout"
                    size_hint_x: None
                    width: dp(220)
                    on_release: app.root.open_workout_log_modal()
                Button:
                    text: "Refresh history"
                    size_hint_x: None
                    width: dp(180)
                    on_release: app.root._load_history()
            WrapLabel:
                text: app.root.history_status_text
                color: app.root.history_status_color
            BoxLayout:
                id: history_list
                orientation: "vertical"
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

<RecommendationScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        GridLayout:
            cols: 2
            spacing: dp(8)
            row_default_height: dp(34)
            size_hint_y: None
            height: self.minimum_height
            WrapLabel:
                text: "Goal"
                color: 0.18, 0.18, 0.22, 1
            Spinner:
                id: rec_goal_spinner
                text: app.root.rec_goal_spinner_text
                values: app.root.goal_choice_options
                on_text: app.root.rec_goal_spinner_text = self.text
            WrapLabel:
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
                text: "Clear plan"
                on_release: app.root.clear_recommendation_plan()
            Button:
                text: "Generate recommendations"
                on_release: app.root.handle_generate_recommendations()
        WrapLabel:
            text: app.root.rec_status_text
            color: app.root.rec_status_color
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
            size_hint_y: 1
            RecycleGridLayout:
                cols: 2
                default_size: None, dp(240)
                default_size_hint: 0.5, None
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
        WrapLabel:
            text: "Add your first exercise to get started." if not app.root.rec_plan else "Your training plan (reorder with Up/Down)"
            bold: False if not app.root.rec_plan else True
            color: (0.35, 0.35, 0.4, 1) if not app.root.rec_plan else (0.12, 0.14, 0.22, 1)
        RecycleView:
            id: rec_plan_list
            viewclass: "PlanItem"
            bar_width: dp(6)
            scroll_type: ['bars', 'content']
            size_hint_y: None
            height: app.root.rec_plan_height
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
                    rgba: 1, 1, 1, 1
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
                WrapLabel:
                    text: app.root.summary_performed_at_display
                    color: 0.16, 0.2, 0.3, 1
                    halign: "left"
                Label:
                    text: "Goal"
                    color: 0.18, 0.18, 0.22, 1
                WrapLabel:
                    text: app.root.summary_goal_display
                    color: 0.16, 0.2, 0.3, 1
                Label:
                    text: "Total duration"
                    color: 0.18, 0.18, 0.22, 1
                WrapLabel:
                    text: app.root.summary_duration_display
                    color: 0.16, 0.2, 0.3, 1
                Label:
                    text: "Completed sets"
                    color: 0.18, 0.18, 0.22, 1
                WrapLabel:
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
            rgba: 1, 1, 1, 1
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
                rgba: 0.94, 0.96, 0.99, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "Exercise Manager"
            font_size: "18sp"
            bold: True
            color: 0.1, 0.12, 0.2, 1
            size_hint_x: None
            width: self.texture_size[0] + dp(14)
        ScrollView:
            do_scroll_y: False
            bar_width: dp(0)
            size_hint_x: 1
            BoxLayout:
                size_hint_x: None
                width: self.minimum_width
                spacing: dp(10)
                NavButton:
                    text: "Home"
                    size_hint_x: None
                    width: dp(90)
                    on_release: root.go_home()
                NavButton:
                    text: "Browse"
                    size_hint_x: None
                    width: dp(90)
                    on_release: root.go_browse()
                NavButton:
                    text: "Add"
                    size_hint_x: None
                    width: dp(90)
                    on_release: root.go_add()
                NavButton:
                    text: "Users"
                    size_hint_x: None
                    width: dp(90)
                    on_release: root.go_users()
                NavButton:
                    text: "History"
                    size_hint_x: None
                    width: dp(90)
                    on_release: root.go_history()
                NavButton:
                    text: "Recommend"
                    size_hint_x: None
                    width: dp(110)
                    on_release: root.go_recommend()
                NavButton:
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
        RegisterScreen:
            name: "register"
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
    icon_source = StringProperty("")
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


class RegisterScreen(Screen):
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
    icon_source = StringProperty("")
    display = StringProperty()
    index = StringProperty()
    pass


class ProgressRing(Widget):
    progress = NumericProperty(0.0)
    thickness = NumericProperty(6.0)
    color = ListProperty((0.18, 0.4, 0.85, 1))
    background_color = ListProperty((0.86, 0.9, 0.96, 1))


class RecommendationCard(BoxLayout):
    name = StringProperty()
    icon_source = StringProperty("")
    description = StringProperty()
    muscle_group = StringProperty()
    equipment = StringProperty()
    suitability = StringProperty()
    estimated_minutes = StringProperty()
    score_display = StringProperty()
    recommendation = StringProperty()
    show_details = BooleanProperty(False)


class DatePickerPopup(ModalView):
    month_label = StringProperty("")
    selected_label = StringProperty("")

    def __init__(self, *, on_select, initial_date: Optional[date] = None, **kwargs):
        super().__init__(**kwargs)
        self._on_select = on_select
        chosen = initial_date or date.today()
        self._selected_date = chosen
        self.selected_label = chosen.isoformat()
        self._shown_year = chosen.year
        self._shown_month = chosen.month
        self.month_label = chosen.strftime("%B %Y")
        Clock.schedule_once(self._populate_calendar, 0)

    def shift_month(self, delta: int) -> None:
        self._change_months(delta)

    def shift_year(self, delta_years: int) -> None:
        self._change_months(delta_years * 12)

    def confirm_selection(self) -> None:
        selected = self._selected_date or date.today()
        if self._on_select:
            self._on_select(selected)
        self.dismiss()

    def select_today(self) -> None:
        today = date.today()
        self._set_selected_date(today, update_month=True)
        self.confirm_selection()

    def _set_selected_date(self, selected: date, *, update_month: bool = False) -> None:
        self._selected_date = selected
        self.selected_label = selected.isoformat()
        if update_month:
            self._shown_year = selected.year
            self._shown_month = selected.month
            self.month_label = selected.strftime("%B %Y")
        self._populate_calendar()

    def _set_selected_day(self, day: int, *_: Any) -> None:
        selected = date(self._shown_year, self._shown_month, day)
        self._set_selected_date(selected)

    def _change_months(self, delta_months: int) -> None:
        total_months = (self._shown_year * 12 + (self._shown_month - 1)) + delta_months
        if total_months < 0:
            total_months = 0
        new_year, month_index = divmod(total_months, 12)
        self._shown_year = new_year
        self._shown_month = month_index + 1
        self.month_label = date(self._shown_year, self._shown_month, 1).strftime("%B %Y")
        self._populate_calendar()

    def _populate_calendar(self, *_: Any) -> None:
        if not self.ids:
            return
        grid = self.ids.day_grid
        grid.clear_widgets()
        for weekday in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
            grid.add_widget(
                Label(
                    text=weekday,
                    bold=True,
                    font_size="12sp",
                    color=(0.15, 0.18, 0.25, 1),
                    halign="center",
                    valign="middle",
                    text_size=(dp(40), dp(32)),
                )
            )
        today = date.today()
        selected = self._selected_date
        month_days = calendar.Calendar(firstweekday=0).monthdayscalendar(self._shown_year, self._shown_month)
        for week in month_days:
            for day in week:
                if day == 0:
                    grid.add_widget(Label(text=""))
                else:
                    is_today = (
                        today.year == self._shown_year
                        and today.month == self._shown_month
                        and today.day == day
                    )
                    is_selected = (
                        selected
                        and selected.year == self._shown_year
                        and selected.month == self._shown_month
                        and selected.day == day
                    )
                    if is_selected:
                        background_color = (0.18, 0.4, 0.85, 1)
                        text_color = (1, 1, 1, 1)
                    elif is_today:
                        background_color = (0.85, 0.92, 1, 1)
                        text_color = (0.12, 0.14, 0.22, 1)
                    else:
                        background_color = (0.94, 0.96, 1, 1)
                        text_color = (0.14, 0.16, 0.24, 1)
                    grid.add_widget(
                        Button(
                            text=str(day),
                            font_size="14sp",
                            background_normal="",
                            background_down="",
                            background_color=background_color,
                            color=text_color,
                            on_release=partial(self._set_selected_day, day),
                        )
                    )


class WorkoutLogModal(ModalView):
    pass


class GoalPromptModal(ModalView):
    pass


class RecommendationDetailsModal(ModalView):
    exercise_name = StringProperty("")
    description = StringProperty("")
    muscle_group = StringProperty("")
    equipment = StringProperty("")
    goal_label = StringProperty("")
    suitability = StringProperty("")
    estimated_minutes = StringProperty("")
    score_display = StringProperty("")
    recommendation = StringProperty("")
    sets_display = StringProperty("—")
    reps_display = StringProperty("—")
    time_display = StringProperty("—")


class RootWidget(BoxLayout):
    goal_options = ListProperty()
    goal_choice_options = ListProperty()
    muscle_choice_options = ListProperty()
    equipment_choice_options = ListProperty()
    muscle_options = ListProperty()
    equipment_options = ListProperty()
    user_options = ListProperty()
    user_goal_options = ListProperty()
    history_exercise_options = ListProperty()
    history_exercise_filtered_options = ListProperty()
    workout_goal_options = ListProperty()
    icon_choice_options = ListProperty()

    goal_spinner_text = StringProperty("All goals")
    muscle_spinner_text = StringProperty("All muscle groups")
    equipment_spinner_text = StringProperty("All equipment")
    filter_goal_color = ListProperty((0.93, 0.95, 0.98, 1))
    filter_goal_text_color = ListProperty((0.2, 0.2, 0.25, 1))
    filter_muscle_color = ListProperty((0.93, 0.95, 0.98, 1))
    filter_muscle_text_color = ListProperty((0.2, 0.2, 0.25, 1))
    filter_equipment_color = ListProperty((0.93, 0.95, 0.98, 1))
    filter_equipment_text_color = ListProperty((0.2, 0.2, 0.25, 1))
    add_goal_spinner_text = StringProperty("")
    add_muscle_spinner_text = StringProperty("")
    add_equipment_spinner_text = StringProperty("")
    rating_spinner_text = StringProperty("5")
    icon_choice_spinner_text = StringProperty("No icon")
    history_exercise_spinner_text = StringProperty("Select exercise")
    workout_goal_spinner_text = StringProperty("No goal")
    history_exercise_filter = StringProperty("")

    filter_goal = StringProperty("All")
    filter_muscle_group = StringProperty("All")
    filter_equipment = StringProperty("All")
    status_text = StringProperty("")
    status_color = ListProperty((0.14, 0.4, 0.2, 1))
    muscle_choice_display = StringProperty("")
    equipment_choice_display = StringProperty("")
    add_icon_source = StringProperty("")
    user_spinner_text = StringProperty("Select user")
    current_user_display = StringProperty("No user selected")
    user_status_text = StringProperty("")
    user_status_color = ListProperty((0.14, 0.4, 0.2, 1))
    register_goal_spinner_text = StringProperty("No goal")
    register_status_text = StringProperty("")
    register_status_color = ListProperty((0.14, 0.4, 0.2, 1))
    user_profile_name = StringProperty("")
    user_profile_goal = StringProperty("No goal")
    user_profile_status_text = StringProperty("")
    user_profile_status_color = ListProperty((0.14, 0.4, 0.2, 1))
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
    rec_plan_height = NumericProperty(dp(70))
    live_active = BooleanProperty(False)
    live_paused = BooleanProperty(False)
    live_started = BooleanProperty(False)
    live_exercises = ListProperty()
    live_progress_display = StringProperty("No session")
    live_state_display = StringProperty("Not started")
    live_exercise_title = StringProperty("No exercise running")
    live_icon_display = StringProperty("")
    live_icon_source = StringProperty("")
    live_muscle_display = StringProperty("")
    live_equipment_display = StringProperty("")
    live_recommendation_display = StringProperty("")
    live_exercise_description = StringProperty("")
    live_details_expanded = BooleanProperty(False)
    live_exercise_target_display = StringProperty("—")
    live_set_target_display = StringProperty("—")
    live_rest_setting_text = StringProperty("30")
    live_exercise_timer = StringProperty("00:00")
    live_set_timer = StringProperty("00:00")
    live_rest_timer = StringProperty("—")
    live_current_set_display = StringProperty("")
    live_exercise_progress = NumericProperty(0.0)
    live_progress_timer = StringProperty("00:00")
    live_progress_color = ListProperty((0.18, 0.4, 0.85, 1))
    live_instruction = StringProperty("")
    live_tempo_hint = StringProperty("")
    live_hint_text = StringProperty("")
    live_hint_color = ListProperty((0.14, 0.4, 0.2, 1))
    live_signal_text = StringProperty("")
    live_signal_color = ListProperty((0.16, 0.32, 0.6, 1))
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
        self._goal_code_label_map = {goal: self._pretty_goal(goal) for goal in exercise_database.GOALS}
        self._workout_log_modal: Optional[WorkoutLogModal] = None
        self._goal_prompt_modal: Optional[GoalPromptModal] = None
        self._recommendation_detail_modal: Optional[RecommendationDetailsModal] = None
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
        self.live_rest_setting_text = str(int(self.live_rest_seconds))
        self._icon_lookup = self._build_icon_lookup()
        self.icon_choice_options = self._build_icon_choice_options()
        if self.icon_choice_spinner_text not in self.icon_choice_options:
            self.icon_choice_spinner_text = "No icon"
        self.on_icon_choice_change(self.icon_choice_spinner_text)
        self._signal_clear_event = None
        self._live_phase = "idle"
        self._update_rec_plan_height()
        Clock.schedule_once(self._bootstrap_data, 0)

    def _pretty_goal(self, goal: str) -> str:
        return goal.replace("_", " ").title()

    def _normalize_muscle_group(self, muscle_group: str) -> str:
        replacements = {
            "Chest, shoulders, triceps": "Chest",
        }
        cleaned = muscle_group.strip()
        return replacements.get(cleaned, cleaned)

    def _normalize_icon_key(self, value: str) -> str:
        return "".join(ch.lower() for ch in value if ch.isalnum())

    def _slugify_icon_name(self, value: str) -> str:
        cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
        return "_".join(part for part in cleaned.split("_") if part)

    def _build_icon_lookup(self) -> dict[str, str]:
        icon_dir = Path(__file__).with_name("Pictures")
        if not icon_dir.is_dir():
            return {}
        lookup: dict[str, str] = {}
        for entry in icon_dir.iterdir():
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                continue
            key = self._normalize_icon_key(entry.stem)
            if key and key not in lookup:
                lookup[key] = str(entry)
        return lookup

    def _build_icon_choice_options(self) -> list[str]:
        icon_dir = Path(__file__).with_name("Pictures")
        if not icon_dir.is_dir():
            return ["No icon"]
        choices: list[str] = []
        for entry in sorted(icon_dir.iterdir(), key=lambda path: path.name.lower()):
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                continue
            slug = self._slugify_icon_name(entry.stem)
            if slug and slug not in choices:
                choices.append(slug)
        return ["No icon"] + choices if choices else ["No icon"]

    def _resolve_icon_source(self, icon_name: str) -> str:
        if not icon_name:
            return ""
        key = self._normalize_icon_key(icon_name)
        if not key:
            return ""
        path = self._icon_lookup.get(key)
        if path:
            return path
        if not key.endswith("s"):
            path = self._icon_lookup.get(f"{key}s")
            if path:
                return path
        if key.endswith("s"):
            path = self._icon_lookup.get(key[:-1])
            if path:
                return path
        for candidate in sorted(self._icon_lookup):
            if candidate.startswith(key) or key.startswith(candidate):
                return self._icon_lookup[candidate]
        return ""

    def on_icon_choice_change(self, value: str) -> None:
        if not value or value in {"No icon", "Select icon", "No icons found"}:
            self.icon_choice_spinner_text = "No icon"
            self.add_icon_source = ""
            return
        self.icon_choice_spinner_text = value
        self.add_icon_source = self._resolve_icon_source(value)

    def _preferred_goal_label(self) -> str:
        """
        Pick a default goal label for forms:
        - Current recommendation goal if chosen
        - Else user's saved goal (if available)
        - Else "Muscle Building" (most common)
        - Else first available goal.
        """
        if self.rec_goal_spinner_text:
            return self.rec_goal_spinner_text
        if self.user_profile_goal and self.user_profile_goal in self.goal_choice_options:
            return self.user_profile_goal
        muscle_label = self._pretty_goal("muscle_building")
        if muscle_label in self.goal_choice_options:
            return muscle_label
        if self.goal_choice_options:
            return self.goal_choice_options[0]
        return ""

    def _default_workout_goal_label(self) -> str:
        if self.user_profile_goal and self.user_profile_goal in self.goal_choice_options:
            return self.user_profile_goal
        return "No goal"

    def on_user_profile_goal(self, *_: Any) -> None:
        self._sync_recommendation_goal()

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
            muscle_group = self._normalize_muscle_group(muscle_group)
            recommendation_parts = []
            if sets is not None and reps is not None:
                recommendation_parts.append(f"{sets} sets x {reps} reps")
            elif sets is not None:
                recommendation_parts.append(f"{sets} sets")
            if time_seconds is not None:
                recommendation_parts.append(f"{time_seconds}s hold")
            recommendation = " • ".join(recommendation_parts) if recommendation_parts else "Adjust volume to preference"
            icon_value = icon or ""
            icon_source = self._resolve_icon_source(icon_value)
            if not icon_source and name:
                icon_source = self._resolve_icon_source(name)
            records.append(
                {
                    "name": name,
                    "icon": icon_value,
                    "icon_source": icon_source,
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
        self.add_equipment_spinner_text = self._resolve_equipment_choice(self.add_equipment_spinner_text)

        self.goal_options = ["All goals"] + self.goal_choice_options
        self.user_goal_options = ["No goal"] + self.goal_choice_options
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
        if self.user_profile_goal not in self.user_goal_options:
            self.user_profile_goal = "No goal"
        self.history_exercise_options = sorted({r["name"] for r in self.records})
        self._refresh_history_exercise_filtered_options()
        self.workout_goal_options = ["No goal"] + self.goal_choice_options
        if self.workout_goal_spinner_text not in self.workout_goal_options:
            self.workout_goal_spinner_text = "No goal"
        if self.register_goal_spinner_text not in self.user_goal_options:
            self.register_goal_spinner_text = "No goal"
        self._sync_recommendation_goal()
        self._update_filter_colors()

    def _resolve_filter_colors(
        self,
        value: str,
        default_value: str,
        active_color: tuple[float, float, float, float],
        inactive_color: tuple[float, float, float, float],
        inactive_text: tuple[float, float, float, float],
        active_text: tuple[float, float, float, float],
    ) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
        if value and value != default_value:
            return active_color, active_text
        return inactive_color, inactive_text

    def _update_filter_colors(self) -> None:
        inactive_color = (0.93, 0.95, 0.98, 1)
        inactive_text = (0.2, 0.2, 0.25, 1)
        active_text = (1, 1, 1, 1)
        self.filter_goal_color, self.filter_goal_text_color = self._resolve_filter_colors(
            self.goal_spinner_text,
            "All goals",
            (0.18, 0.5, 0.85, 1),
            inactive_color,
            inactive_text,
            active_text,
        )
        self.filter_muscle_color, self.filter_muscle_text_color = self._resolve_filter_colors(
            self.muscle_spinner_text,
            "All muscle groups",
            (0.2, 0.65, 0.38, 1),
            inactive_color,
            inactive_text,
            active_text,
        )
        self.filter_equipment_color, self.filter_equipment_text_color = self._resolve_filter_colors(
            self.equipment_spinner_text,
            "All equipment",
            (0.9, 0.55, 0.2, 1),
            inactive_color,
            inactive_text,
            active_text,
        )

    def _sync_recommendation_goal(self) -> None:
        if self.user_profile_goal and self.user_profile_goal in self.goal_choice_options:
            self.rec_goal_spinner_text = self.user_profile_goal
        elif self.goal_choice_options and self.rec_goal_spinner_text not in self.goal_choice_options:
            self.rec_goal_spinner_text = self.goal_choice_options[0]

    def on_rec_plan(self, *_: Any) -> None:
        self._update_rec_plan_height()

    def _compute_rec_plan_height(self) -> float:
        min_height = dp(70)
        max_height = dp(240)
        item_height = dp(70)
        spacing = dp(6)
        count = len(self.rec_plan)
        if count <= 0:
            return min_height
        total = count * item_height + max(0, count - 1) * spacing
        return min(max_height, max(min_height, total))

    def _update_rec_plan_height(self) -> None:
        self.rec_plan_height = self._compute_rec_plan_height()

    def _refresh_history_exercise_filtered_options(self) -> None:
        query = self.history_exercise_filter.strip().lower()
        if query:
            filtered = [name for name in self.history_exercise_options if query in name.lower()]
        else:
            filtered = list(self.history_exercise_options)
        self.history_exercise_filtered_options = filtered
        if filtered:
            if self.history_exercise_spinner_text not in filtered:
                self.history_exercise_spinner_text = "Select exercise"
        else:
            self.history_exercise_spinner_text = "No matches" if self.history_exercise_options else "No exercises"

    def filter_history_exercise_options(self, query: str) -> None:
        self.history_exercise_filter = query
        self._refresh_history_exercise_filtered_options()

    def clear_history_exercise_filter(self) -> None:
        ids = self._workout_form_ids()
        if ids and "history_exercise_filter_input" in ids:
            ids.history_exercise_filter_input.text = ""
        else:
            self.history_exercise_filter = ""
            self._refresh_history_exercise_filtered_options()

    def _resolve_equipment_choice(self, current: str) -> str:
        if current and current in self.equipment_choice_options:
            return current
        if "Bodyweight" in self.equipment_choice_options:
            return "Bodyweight"
        if self.equipment_choice_options:
            return self.equipment_choice_options[0]
        return "Bodyweight"

    def _browse_screen(self) -> BrowseScreen:
        return self.ids.screen_manager.get_screen("browse")

    def _add_screen(self) -> AddScreen:
        return self.ids.screen_manager.get_screen("add")

    def _user_screen(self) -> UserScreen:
        return self.ids.screen_manager.get_screen("user")

    def _register_screen(self) -> RegisterScreen:
        return self.ids.screen_manager.get_screen("register")

    def _history_screen(self) -> HistoryScreen:
        return self.ids.screen_manager.get_screen("history")

    def _recommend_screen(self) -> RecommendationScreen:
        return self.ids.screen_manager.get_screen("recommend")

    def _workout_form_ids(self) -> Optional[Any]:
        if self._workout_log_modal is not None:
            return self._workout_log_modal.ids
        return None

    def _prefill_workout_date(self) -> None:
        """Populate the workout date field with today's date if available."""
        ids = self._workout_form_ids()
        if not ids:
            return
        date_field = ids.get("workout_date_input")
        if date_field and not date_field.text:
            date_field.text = date.today().isoformat()

    def _flash_color(
        self,
        base: tuple[float, float, float, float],
        text: tuple[float, float, float, float],
    ) -> tuple[float, float, float, float]:
        luma = 0.2126 * text[0] + 0.7152 * text[1] + 0.0722 * text[2]
        factor = 0.18
        if luma > 0.6:
            return (
                max(0.0, base[0] * (1 - factor)),
                max(0.0, base[1] * (1 - factor)),
                max(0.0, base[2] * (1 - factor)),
                base[3],
            )
        return (
            min(1.0, base[0] + (1 - base[0]) * factor),
            min(1.0, base[1] + (1 - base[1]) * factor),
            min(1.0, base[2] + (1 - base[2]) * factor),
            base[3],
        )

    def _animate_input_feedback(self, widget: Any) -> None:
        if not widget or not hasattr(widget, "background_color"):
            return
        try:
            Animation.cancel_all(widget, "background_color")
        except Exception:
            pass
        base_color = tuple(getattr(widget, "background_color", (1, 1, 1, 1)))
        text_color = tuple(getattr(widget, "color", (0, 0, 0, 1)))
        flash_color = self._flash_color(base_color, text_color)
        (Animation(background_color=flash_color, duration=0.08, t="out_quad")
         + Animation(background_color=base_color, duration=0.25, t="out_quad")).start(widget)

    def confirm_value_input(self, widget: Any) -> None:
        if not widget or not hasattr(widget, "text"):
            return
        current = getattr(widget, "text", "")
        if not getattr(widget, "get_root_window", None) or not widget.get_root_window():
            setattr(widget, "_last_confirmed_value", current)
            return
        last_value = getattr(widget, "_last_confirmed_value", None)
        if last_value is None and hasattr(widget, "values"):
            setattr(widget, "_last_confirmed_value", current)
            return
        if last_value is None and current == "":
            setattr(widget, "_last_confirmed_value", current)
            return
        if last_value == current:
            return
        setattr(widget, "_last_confirmed_value", current)
        Clock.schedule_once(lambda *_: self._animate_input_feedback(widget), 0)

    def on_goal_change(self, value: str) -> None:
        self.filter_goal = "All" if value == "All goals" else self._goal_label_map.get(value, "All")
        self.goal_spinner_text = value
        self._update_filter_colors()
        self.apply_filters()

    def on_muscle_change(self, value: str) -> None:
        self.filter_muscle_group = "All" if value == "All muscle groups" else value
        self.muscle_spinner_text = value
        self._update_filter_colors()
        self.apply_filters()

    def on_equipment_change(self, value: str) -> None:
        self.filter_equipment = "All" if value == "All equipment" else value
        self.equipment_spinner_text = value
        self._update_filter_colors()
        self.apply_filters()

    def apply_filters(self) -> None:
        filtered: list[dict[str, str]] = []
        goal_priority = {goal: idx for idx, goal in enumerate(exercise_database.GOALS)}
        if self.filter_goal == "All":
            grouped: dict[str, dict[str, Any]] = {}
            for record in self.records:
                if not record.get("name") or not record.get("description"):
                    continue
                if self.filter_muscle_group != "All" and record["muscle_group"] != self.filter_muscle_group:
                    continue
                if self.filter_equipment != "All" and record["equipment"] != self.filter_equipment:
                    continue
                existing = grouped.get(record["name"])
                if not existing:
                    grouped[record["name"]] = record
                    continue
                if record["rating"] > existing["rating"]:
                    grouped[record["name"]] = record
                elif record["rating"] == existing["rating"]:
                    if goal_priority.get(record["goal"], 0) < goal_priority.get(existing["goal"], 0):
                        grouped[record["name"]] = record
            for record in sorted(grouped.values(), key=lambda r: r["name"]):
                suitability_display = f'{record["goal_label"]} ({record["suitability_display"]})'
                filtered.append(
                    {
                        "name": record["name"],
                        "icon_source": record.get("icon_source", ""),
                        "description": record["description"],
                        "goal_label": record["goal_label"],
                        "muscle_group": record["muscle_group"],
                        "equipment": record["equipment"],
                        "suitability_display": suitability_display,
                        "recommendation": record["recommendation"],
                    }
                )
        else:
            for record in self.records:
                if not record.get("name") or not record.get("description"):
                    continue
                if record["goal"] != self.filter_goal:
                    continue
                if self.filter_muscle_group != "All" and record["muscle_group"] != self.filter_muscle_group:
                    continue
                if self.filter_equipment != "All" and record["equipment"] != self.filter_equipment:
                    continue
                suitability_display = record["suitability_display"]
                filtered.append(
                    {
                        "name": record["name"],
                        "icon_source": record.get("icon_source", ""),
                        "description": record["description"],
                        "goal_label": record["goal_label"],
                        "muscle_group": record["muscle_group"],
                        "equipment": record["equipment"],
                        "suitability_display": suitability_display,
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
        self._users = [
            {
                "id": user_id,
                "username": username,
                "display_name": display_name or username,
                "preferred_goal": preferred_goal,
            }
            for user_id, username, display_name, preferred_goal in rows
        ]
        self.user_options = [u["username"] for u in self._users]

        if self.current_user_id and not any(u["id"] == self.current_user_id for u in self._users):
            self.current_user_id = None

        if not self.current_user_id:
            example_user = next(
                (u for u in self._users if u["username"] == exercise_database.EXAMPLE_USERNAME),
                None,
            )
            if example_user:
                self.current_user_id = example_user["id"]

        if self.current_user_id:
            current = next((u for u in self._users if u["id"] == self.current_user_id), None)
            if current:
                self.current_user_display = current["display_name"]
                self.user_spinner_text = current["username"]
                self.user_profile_name = current["display_name"]
                preferred_goal = current.get("preferred_goal")
                if preferred_goal:
                    self.user_profile_goal = self._goal_code_label_map.get(preferred_goal, "No goal")
                else:
                    self.user_profile_goal = "No goal"
        if not self.current_user_id:
            self.current_user_display = "No user selected"
            self.user_spinner_text = "Select user"
            self.user_profile_name = ""
            self.user_profile_goal = "No goal"

        self._load_history()

    def _set_user_status(self, message: str, *, error: bool = False) -> None:
        self.user_status_text = message
        self.user_status_color = (0.65, 0.16, 0.16, 1) if error else (0.14, 0.4, 0.2, 1)

    def _set_register_status(self, message: str, *, error: bool = False) -> None:
        self.register_status_text = message
        self.register_status_color = (0.65, 0.16, 0.16, 1) if error else (0.14, 0.4, 0.2, 1)

    def _set_user_profile_status(self, message: str, *, error: bool = False) -> None:
        self.user_profile_status_text = message
        self.user_profile_status_color = (0.65, 0.16, 0.16, 1) if error else (0.14, 0.4, 0.2, 1)

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
        try:
            ids = self._register_screen().ids
        except Exception:
            self._set_register_status("Registration screen not available.", error=True)
            return
        username = ids.register_username_input.text.strip()
        if not username:
            self._set_register_status("Username is required.", error=True)
            return
        display_name = ids.register_display_input.text.strip() or None
        goal_label = ids.register_goal_spinner.text.strip()
        preferred_goal = None
        if goal_label and goal_label != "No goal":
            preferred_goal = self._goal_label_map.get(goal_label)
            if not preferred_goal:
                self._set_register_status("Select a valid goal option.", error=True)
                return

        try:
            new_user_id = exercise_database.add_user(
                username=username,
                display_name=display_name,
                preferred_goal=preferred_goal,
            )
        except ValueError as exc:
            self._set_register_status(str(exc), error=True)
            return
        except sqlite3.IntegrityError:
            self._set_register_status("Username already exists. Choose another.", error=True)
            return
        except sqlite3.DatabaseError as exc:
            self._set_register_status(f"Database error: {exc}", error=True)
            return

        ids.register_username_input.text = ""
        ids.register_display_input.text = ""
        self.register_goal_spinner_text = "No goal"
        self.current_user_id = new_user_id
        self._load_users()
        self._set_user_status(f"User '{username}' registered.")
        self._set_register_status(f"User '{username}' registered.")
        self.go_home()

    def save_user_profile(self) -> bool:
        if not self.current_user_id:
            self._set_user_profile_status("Select a user to update the profile.", error=True)
            return False
        display_name = self.user_profile_name.strip()
        if not display_name:
            self._set_user_profile_status("Display name cannot be empty.", error=True)
            return False
        preferred_goal = None
        if self.user_profile_goal and self.user_profile_goal != "No goal":
            preferred_goal = self._goal_label_map.get(self.user_profile_goal)
            if not preferred_goal:
                self._set_user_profile_status("Select a valid goal option.", error=True)
                return False
        try:
            exercise_database.update_user_profile(
                user_id=self.current_user_id,
                display_name=display_name,
                preferred_goal=preferred_goal,
            )
        except sqlite3.DatabaseError as exc:
            self._set_user_profile_status(f"Database error: {exc}", error=True)
            return False
        self.current_user_display = display_name
        self._load_users()
        self._set_user_profile_status("Profile saved.")
        self._sync_recommendation_goal()
        return True

    def on_user_selected(self, username: str) -> None:
        selected = next((u for u in self._users if u["username"] == username), None)
        if not selected:
            return
        self.current_user_id = selected["id"]
        self.current_user_display = selected.get("display_name") or selected["username"]
        self.user_spinner_text = selected["username"]
        self.user_profile_name = selected.get("display_name") or selected["username"]
        preferred_goal = selected.get("preferred_goal")
        if preferred_goal:
            self.user_profile_goal = self._goal_code_label_map.get(preferred_goal, "No goal")
        else:
            self.user_profile_goal = "No goal"
        self._set_user_status(f"User '{username}' selected.")
        self._load_history()
        self.go_home()

    def _split_exercises(self, raw: str) -> list[str]:
        normalized = raw.replace("\n", ",")
        return [part.strip() for part in normalized.split(",") if part.strip()]

    def _known_exercise_names(self) -> set[str]:
        return {record["name"].strip().lower() for record in self.records if record.get("name")}

    def _validate_history_exercises(self, exercises: list[str]) -> Optional[str]:
        known = self._known_exercise_names()
        if not known:
            return None
        unknown = [name for name in exercises if name.strip().lower() not in known]
        if unknown:
            return f"Unknown exercises: {', '.join(unknown)}"
        return None

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

    def open_date_picker(self, target_input: Any) -> None:
        if not target_input:
            return
        text_value = getattr(target_input, "text", "").strip()
        initial = None
        if text_value:
            try:
                initial = date.fromisoformat(text_value)
            except ValueError:
                initial = None
        DatePickerPopup(
            initial_date=initial,
            on_select=lambda selected: self._set_date_input(target_input, selected),
        ).open()

    def _set_date_input(self, target_input: Any, selected: date) -> None:
        if target_input:
            target_input.text = selected.isoformat()
            self.confirm_value_input(target_input)

    def _set_history_status(self, message: str, *, error: bool = False) -> None:
        self.history_status_text = message
        self.history_status_color = (0.65, 0.16, 0.16, 1) if error else (0.14, 0.4, 0.2, 1)

    def _reset_history_exercise_picker(self, ids: Optional[Any] = None) -> None:
        self.history_exercise_spinner_text = "Select exercise"
        self.history_exercise_filter = ""
        self._refresh_history_exercise_filtered_options()
        form_ids = ids or self._workout_form_ids()
        if form_ids and "history_exercise_filter_input" in form_ids:
            form_ids.history_exercise_filter_input.text = ""

    def _reset_workout_log_form(self, *, clear_status: bool = True) -> None:
        ids = self._workout_form_ids()
        if not ids:
            return
        ids.duration_input.text = ""
        ids.exercises_input.text = ""
        ids.total_sets_input.text = ""
        self._reset_history_exercise_picker(ids)
        self.workout_goal_spinner_text = self._default_workout_goal_label()
        if clear_status:
            self._set_history_status("")
        self._prefill_workout_date()

    def _clear_workout_log_modal(self, *_: Any) -> None:
        self._workout_log_modal = None

    def _clear_goal_prompt_modal(self, *_: Any) -> None:
        self._goal_prompt_modal = None

    def open_workout_log_modal(self) -> None:
        if not self._require_user():
            return
        if self._workout_log_modal is not None:
            try:
                self._workout_log_modal.dismiss()
            except Exception:
                pass
        modal = WorkoutLogModal()
        modal.bind(on_dismiss=self._clear_workout_log_modal)
        self._workout_log_modal = modal
        self._reset_workout_log_form(clear_status=True)
        modal.open()

    def _dismiss_workout_log_modal(self) -> None:
        if self._workout_log_modal is None:
            return
        try:
            self._workout_log_modal.dismiss()
        except Exception:
            pass

    def _dismiss_goal_prompt_modal(self) -> None:
        if self._goal_prompt_modal is None:
            return
        try:
            self._goal_prompt_modal.dismiss()
        except Exception:
            pass

    def open_goal_prompt(self) -> None:
        if not self.current_user_id or not self.user_goal_options:
            return
        if self._goal_prompt_modal is not None:
            try:
                self._goal_prompt_modal.dismiss()
            except Exception:
                pass
        if self.user_profile_goal == "No goal":
            preferred = self._preferred_goal_label()
            if preferred and preferred in self.user_goal_options:
                self.user_profile_goal = preferred
        self._set_user_profile_status("")
        modal = GoalPromptModal()
        modal.bind(on_dismiss=self._clear_goal_prompt_modal)
        self._goal_prompt_modal = modal
        modal.open()

    def skip_goal_prompt(self) -> None:
        self.user_profile_goal = "No goal"
        self._set_user_profile_status("")
        self._dismiss_goal_prompt_modal()

    def add_history_exercise_from_menu(self) -> None:
        ids = self._workout_form_ids()
        if not ids:
            return
        selected = ids.history_exercise_spinner.text.strip()
        if not selected or selected in {"Select exercise", "No matches", "No exercises"}:
            return
        existing = self._split_exercises(ids.exercises_input.text)
        existing_lower = {name.lower() for name in existing}
        if selected.lower() in existing_lower:
            self._set_history_status(f"{selected} is already listed.")
            return
        if ids.exercises_input.text.strip():
            ids.exercises_input.text = ids.exercises_input.text.rstrip() + "\n" + selected
        else:
            ids.exercises_input.text = selected
        self.confirm_value_input(ids.exercises_input)
        self._set_history_status(f"Added {selected}.")
        self.history_exercise_spinner_text = "Select exercise"

    def _load_history(self, *_: Any) -> None:
        try:
            history_screen = self._history_screen()
        except Exception:
            return

        if not self.current_user_id:
            history_list = history_screen.ids.history_list
            history_list.clear_widgets()
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

        cards: list[WorkoutCard] = []
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
            if duration_seconds is not None:
                duration_display = f"{duration_minutes} min ({duration_seconds}s)"
            else:
                duration_display = f"{duration_minutes} min"
            card = WorkoutCard(
                date_display=entry["performed_at"],
                duration_display=duration_display,
                exercises_display=exercises_display,
                goal_display=goal_display,
                sets_display=sets_display,
                attempts_display=attempts_display,
            )
            cards.append(card)
        history_list = history_screen.ids.history_list
        history_list.clear_widgets()
        for card in cards:
            history_list.add_widget(card)
        if cards:
            self._set_history_status(f"{len(cards)} workout(s) loaded.")
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

        ids = self._workout_form_ids()
        if not ids:
            self._set_history_status("Open the workout form to log a session.", error=True)
            return
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
        validation_error = self._validate_history_exercises(exercises)
        if validation_error:
            self._set_history_status(validation_error, error=True)
            return

        goal_label = ids.workout_goal_spinner.text.strip()
        goal = None
        if goal_label and goal_label != "No goal":
            goal = goal_label

        sets_raw = ids.total_sets_input.text.strip()
        total_sets_completed = None
        if sets_raw:
            try:
                total_sets_completed = int(sets_raw)
                if total_sets_completed < 0:
                    raise ValueError
            except ValueError:
                self._set_history_status("Total sets must be 0 or greater.", error=True)
                return

        try:
            exercise_database.log_workout(
                user_id=self.current_user_id,
                performed_at=workout_date,
                duration_minutes=duration_minutes,
                exercises=exercises,
                goal=goal,
                total_sets_completed=total_sets_completed,
            )
        except (ValueError, sqlite3.DatabaseError) as exc:
            self._set_history_status(str(exc), error=True)
            return

        self._set_history_status("Workout saved.")
        self._reset_workout_log_form(clear_status=False)
        self._load_history()
        self._dismiss_workout_log_modal()

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

    def _plan_goal_label(self) -> str:
        labels = {item.get("goal_label") for item in self.rec_plan if item.get("goal_label")}
        if not labels:
            return ""
        if len(labels) == 1:
            return labels.pop()
        return "Multiple goals"

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
                    "icon_source": record.get("icon_source", ""),
                    "description": record["description"],
                    "muscle_group": record["muscle_group"],
                    "equipment": record["equipment"],
                    "goal_label": record["goal_label"],
                    "suitability": record["suitability_display"],
                    "recommendation": record["recommendation"],
                    "sets": record.get("sets"),
                    "reps": record.get("reps"),
                    "time_seconds": record.get("time_seconds"),
                    "estimated_minutes": str(est_minutes),
                    "score": score,
                    "score_display": str(score),
                    "show_details": False,
                }
            )

        recommendations.sort(key=lambda r: (-r["score"], r["name"]))
        self.rec_recommendations = recommendations
        self._recommend_screen().ids.rec_list.data = recommendations
        self._set_rec_status(f"{len(recommendations)} exercises recommended.")
        # Reset plan only if the selected goal conflicts with the existing plan.
        plan_goal = self._plan_goal_label()
        if plan_goal and plan_goal != "Multiple goals" and plan_goal != self.rec_goal_spinner_text:
            self._reset_plan(silent=True)

    def _find_recommendation(self, name: str) -> Optional[dict[str, Any]]:
        return next((rec for rec in self.rec_recommendations if rec["name"] == name), None)

    def _clear_recommendation_detail_modal(self, *_: Any) -> None:
        self._recommendation_detail_modal = None

    def open_recommendation_details(self, name: str) -> None:
        rec = self._find_recommendation(name)
        if not rec:
            return
        if self._recommendation_detail_modal is not None:
            try:
                self._recommendation_detail_modal.dismiss()
            except Exception:
                pass
        modal = RecommendationDetailsModal()
        modal.exercise_name = rec.get("name", "")
        modal.description = rec.get("description", "")
        modal.muscle_group = rec.get("muscle_group", "")
        modal.equipment = rec.get("equipment", "")
        modal.goal_label = rec.get("goal_label", "")
        modal.suitability = rec.get("suitability", "")
        estimated = rec.get("estimated_minutes")
        score_display = rec.get("score_display")
        modal.estimated_minutes = str(estimated) if estimated is not None else ""
        modal.score_display = str(score_display) if score_display is not None else ""
        modal.recommendation = rec.get("recommendation", "")
        sets = rec.get("sets")
        reps = rec.get("reps")
        time_seconds = rec.get("time_seconds")
        modal.sets_display = str(sets) if sets is not None else "—"
        modal.reps_display = str(reps) if reps is not None else "—"
        if time_seconds is None:
            modal.time_display = "—"
        else:
            modal.time_display = f"{time_seconds} sec"
        modal.bind(on_dismiss=self._clear_recommendation_detail_modal)
        self._recommendation_detail_modal = modal
        modal.open()

    def toggle_recommendation_details(self, name: str) -> None:
        rec = self._find_recommendation(name)
        if not rec:
            return
        # flip detail visibility for this item
        current = bool(rec.get("show_details"))
        for r in self.rec_recommendations:
            if r["name"] == name:
                r["show_details"] = not current
            else:
                r["show_details"] = bool(r.get("show_details", False))
        self._recommend_screen().ids.rec_list.data = self.rec_recommendations
        self._set_rec_status("Details toggled.")

    def add_recommendation_to_plan(self, name: str) -> None:
        rec = self._find_recommendation(name)
        if not rec:
            return
        if any(item["name"] == name for item in self.rec_plan):
            self._set_rec_status(f"{name} is already in the plan.", error=True)
            return
        icon_source = rec.get("icon_source") or self._resolve_icon_source(rec.get("icon", "") or rec.get("name", ""))
        plan_item = {
            "name": rec["name"],
            "icon": rec.get("icon", ""),
            "icon_source": icon_source,
            "muscle_group": rec.get("muscle_group", ""),
            "equipment": rec.get("equipment", ""),
            "goal_label": rec.get("goal_label", ""),
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
                "icon_source": item.get("icon_source")
                or self._resolve_icon_source(item.get("icon", "") or item.get("name", "")),
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
                        "icon_source": match.get("icon_source", ""),
                        "goal_label": match["goal_label"],
                        "suitability": match["suitability_display"],
                        "recommendation": match["recommendation"],
                        "sets": match.get("sets"),
                        "reps": match.get("reps"),
                        "time_seconds": match.get("time_seconds"),
                        "estimated_minutes": str(est_minutes),
                        "score": score,
                        "score_display": str(score),
                        "show_details": False,
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
                    "icon_source": record.get("icon_source", ""),
                    "description": record.get("description", ""),
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
        self.add_equipment_spinner_text = self._resolve_equipment_choice("")
        self.rating_spinner_text = "5"
        self.icon_choice_spinner_text = "No icon"
        self.add_icon_source = ""

    def handle_add_exercise(self) -> None:
        ids = self._add_screen().ids
        name = ids.name_input.text.strip()
        description = ids.description_input.text.strip()
        equipment = ids.equipment_add_spinner.text.strip() or "Bodyweight"
        goal_label = ids.goal_add_spinner.text
        goal = self._goal_label_map.get(goal_label)
        muscle_group = ids.muscle_add_spinner.text.strip()
        icon_choice = ""
        if "icon_spinner" in ids:
            icon_choice = ids.icon_spinner.text.strip()
        icon = "" if icon_choice in {"", "No icon", "Select icon", "No icons found"} else icon_choice

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
                icon=icon,
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

    def go_register(self) -> None:
        try:
            ids = self._register_screen().ids
        except Exception:
            ids = None
        if ids:
            if "register_username_input" in ids:
                ids.register_username_input.text = ""
            if "register_display_input" in ids:
                ids.register_display_input.text = ""
        preferred = self._preferred_goal_label()
        if preferred and preferred in self.user_goal_options:
            self.register_goal_spinner_text = preferred
        else:
            self.register_goal_spinner_text = "No goal"
        self._set_register_status("")
        self.ids.screen_manager.current = "register"

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

    def _exercise_expected_duration_seconds(self, exercise: Optional[dict[str, Any]]) -> float:
        if not exercise:
            return 0.0
        sets = exercise.get("sets") or 1
        per_set = self._compute_set_target_seconds(exercise)
        total = sets * per_set
        if sets > 1:
            total += (sets - 1) * float(self.live_rest_seconds)
        est_minutes = exercise.get("estimated_minutes")
        if est_minutes is not None:
            try:
                est_seconds = float(est_minutes) * 60
                total = max(total, est_seconds)
            except (TypeError, ValueError):
                pass
        return max(total, per_set)

    def _set_hint(self, message: str, *, color: tuple = (0.14, 0.4, 0.2, 1), clear_after: float = 3.0) -> None:
        self.live_hint_text = message
        self.live_hint_color = color
        if clear_after > 0:
            Clock.schedule_once(lambda *_: self._clear_hint(message), clear_after)

    def _clear_hint(self, expected: str) -> None:
        if self.live_hint_text == expected:
            self.live_hint_text = ""

    def _flash_signal(self, message: str, color: tuple = (0.16, 0.32, 0.6, 1), duration: float = 2.5) -> None:
        """Show a transient banner for exercise transitions."""
        self.live_signal_text = message
        self.live_signal_color = color
        if self._signal_clear_event is not None:
            try:
                self._signal_clear_event.cancel()
            except Exception:
                pass
        self._signal_clear_event = Clock.schedule_once(lambda *_: self._clear_signal(message), duration)

    def _clear_signal(self, expected: str) -> None:
        if self.live_signal_text == expected:
            self.live_signal_text = ""
        self._signal_clear_event = None

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

    def toggle_live_details(self) -> None:
        self.live_details_expanded = not self.live_details_expanded

    def set_live_rest_seconds(self, value: str) -> None:
        """Allow the user to choose break length while keeping a sane minimum."""
        raw = (value or "").strip()
        if not raw:
            self.live_rest_setting_text = str(int(self.live_rest_seconds))
            return
        try:
            seconds = int(raw)
            if seconds < 5:
                raise ValueError
        except ValueError:
            self._set_hint("Break length must be 5 seconds or more.", color=(0.65, 0.3, 0.18, 1))
            self.live_rest_setting_text = str(int(self.live_rest_seconds))
            return
        self.live_rest_seconds = seconds
        if self._live_phase in ("rest", "between_exercises"):
            self._live_rest_remaining = float(seconds)
            self.live_rest_timer = self._format_time(self._live_rest_remaining)
        self.live_rest_setting_text = str(seconds)
        self._set_hint(f"Break length set to {seconds}s.", color=(0.18, 0.4, 0.2, 1))
        self._update_live_labels()

    def start_live_workout(self) -> None:
        if not self.live_active or self.live_started:
            return
        self.live_started = True
        self.live_paused = False
        self._live_session_started_at = datetime.now()
        self._set_hint("Session started. Begin your first set!", color=(0.18, 0.4, 0.2, 1))
        self._flash_signal("Session started", color=(0.16, 0.32, 0.6, 1))
        self._update_live_labels()
        self._start_live_clock()

    def _compute_live_progress_ratio(self) -> float:
        exercise = self._current_live_exercise()
        if not exercise or not self.live_active or not self.live_started:
            return 0.0
        if self._live_phase in ("rest", "between_exercises"):
            total = float(self.live_rest_seconds or 0)
            if total <= 0:
                return 0.0
            elapsed = max(0.0, total - self._live_rest_remaining)
            ratio = elapsed / total
            return max(0.0, min(1.0, ratio))
        target = float(self._live_set_target_seconds or 0)
        if target <= 0:
            return 0.0
        remaining = max(0.0, target - self._live_set_elapsed)
        ratio = remaining / target
        return max(0.0, min(1.0, ratio))

    def _update_live_progress(self) -> None:
        if self.live_active and self.live_started:
            if self._live_phase in ("rest", "between_exercises"):
                self.live_progress_color = (0.78, 0.22, 0.22, 1)
                self.live_progress_timer = self._format_time(self._live_rest_remaining)
            elif self._live_phase == "set":
                self.live_progress_color = (0.18, 0.5, 0.25, 1)
                target = float(self._live_set_target_seconds or 0)
                if target > 0:
                    remaining = max(0.0, target - self._live_set_elapsed)
                    self.live_progress_timer = self._format_time(remaining)
                else:
                    self.live_progress_timer = self._format_time(self._live_set_elapsed)
            else:
                self.live_progress_color = (0.18, 0.4, 0.85, 1)
                self.live_progress_timer = "00:00"
        else:
            self.live_progress_color = (0.18, 0.4, 0.85, 1)
            self.live_progress_timer = "00:00"

        ratio = self._compute_live_progress_ratio()
        try:
            Animation.cancel_all(self, "live_exercise_progress")
        except Exception:
            pass
        if self.live_active and self.live_started:
            Animation(live_exercise_progress=ratio, duration=0.45, t="linear").start(self)
        else:
            self.live_exercise_progress = ratio

    def _update_live_labels(self) -> None:
        exercise = self._current_live_exercise()
        total_exercises = len(self.live_exercises)
        if not exercise:
            self.live_progress_display = "No session running"
            self.live_exercise_title = "No exercise running"
            self.live_icon_display = ""
            self.live_icon_source = ""
            self.live_muscle_display = ""
            self.live_equipment_display = ""
            self.live_recommendation_display = ""
            self.live_instruction = ""
            self.live_current_set_display = ""
            self.live_state_display = "Not started"
            self.live_upcoming_display = "None"
            self.live_exercise_description = ""
            self.live_exercise_target_display = "—"
            self.live_set_target_display = "—"
            self.live_exercise_timer = "00:00"
            self.live_set_timer = "00:00"
            self.live_rest_timer = "—"
            self.live_exercise_progress = 0.0
            self.live_progress_timer = "00:00"
            self.live_progress_color = (0.18, 0.4, 0.85, 1)
            return
        total_sets = exercise.get("sets") or 1
        self._live_total_sets = total_sets
        self.live_progress_display = f"Exercise {self._live_current_index + 1}/{total_exercises} – {exercise.get('name', '')}"
        self.live_exercise_title = exercise.get("name", "Exercise")
        icon_source = exercise.get("icon_source") or self._resolve_icon_source(
            exercise.get("icon", "") or exercise.get("name", "")
        )
        self.live_icon_source = icon_source
        self.live_icon_display = "No icon available" if not icon_source else ""
        self.live_muscle_display = exercise.get("muscle_group", "")
        self.live_equipment_display = exercise.get("equipment", "")
        self.live_recommendation_display = exercise.get("recommendation", "")
        self.live_exercise_description = exercise.get("description", "")
        expected_seconds = self._exercise_expected_duration_seconds(exercise)
        self.live_exercise_target_display = f"~{self._format_time(expected_seconds)}" if expected_seconds else "—"
        set_target = self._live_set_target_seconds or self._compute_set_target_seconds(exercise)
        self.live_set_target_display = self._format_time(set_target) if set_target else "—"
        if self._live_phase == "between_exercises":
            next_name = ""
            if self._live_current_index + 1 < len(self.live_exercises):
                next_name = self.live_exercises[self._live_current_index + 1].get("name", "Next exercise")
            self.live_instruction = f"Rest, then start {next_name or 'the next exercise'}"
            self.live_current_set_display = f"Completed {total_sets} set(s)."
        else:
            self.live_instruction = self._build_instruction(exercise)
            self.live_current_set_display = f"Set {self._live_current_set} of {total_sets}"
        if self._live_phase == "rest":
            phase_label = "Resting between sets"
        elif self._live_phase == "between_exercises":
            phase_label = "Resting before next exercise"
        elif self._live_phase == "set":
            phase_label = "In set"
        else:
            phase_label = "Not started"
        if self._live_phase == "between_exercises":
            self.live_state_display = phase_label
        else:
            self.live_state_display = f"{phase_label} (Set {self._live_current_set}/{total_sets})"
        self.live_exercise_timer = self._format_time(self._live_exercise_elapsed)
        self.live_set_timer = self._format_time(self._live_set_elapsed)
        if self._live_phase in ("rest", "between_exercises"):
            self.live_rest_timer = self._format_time(self._live_rest_remaining)
        else:
            self.live_rest_timer = "—"
        self._update_live_upcoming()
        if self.live_active and not self.live_started:
            self.live_state_display = "Ready to start"
            self.live_instruction = "Press Start to begin."
            self.live_tempo_hint = ""
        else:
            self._update_tempo_hint()
        self._update_live_progress()

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
        self._live_clock = Clock.schedule_interval(self._tick_live, 0.5)

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
        self.live_started = False
        self.live_active = True
        self._live_session_started_at = None
        self.live_details_expanded = False
        self.live_rest_setting_text = str(int(self.live_rest_seconds))
        self._update_live_labels()
        self._set_hint("Press Start when you're ready.", color=(0.18, 0.4, 0.2, 1))

    def _update_tempo_hint(self) -> None:
        exercise = self._current_live_exercise()
        if not exercise:
            self.live_tempo_hint = ""
            return
        reps = exercise.get("reps")
        if self._live_phase == "between_exercises":
            self.live_tempo_hint = "Rest up — next exercise will start after the break."
            return
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
        if not self.live_active or self.live_paused or not self.live_started:
            return
        exercise = self._current_live_exercise()
        if not exercise:
            return
        if self._live_phase in ("rest", "between_exercises"):
            self._live_rest_remaining = max(0.0, self._live_rest_remaining - dt)
            if self._live_phase == "rest":
                self._live_exercise_elapsed += dt
                self.live_exercise_timer = self._format_time(self._live_exercise_elapsed)
            self.live_rest_timer = self._format_time(self._live_rest_remaining)
            if self._live_rest_remaining <= 0:
                if self._live_phase == "between_exercises":
                    self._advance_exercise(skipped=False, record_status=False)
                else:
                    self._start_next_set()
            self._update_live_progress()
            return
        self._live_exercise_elapsed += dt
        self._live_set_elapsed += dt
        self.live_exercise_timer = self._format_time(self._live_exercise_elapsed)
        self.live_set_timer = self._format_time(self._live_set_elapsed)
        self._update_tempo_hint()
        self._update_live_progress()
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
            self._start_between_exercise_rest(skipped=False)
            return
        self._live_phase = "rest"
        self._live_rest_remaining = float(self.live_rest_seconds)
        self.live_state_display = "Resting"
        self.live_rest_timer = self._format_time(self._live_rest_remaining)
        self._set_hint("Rest now – next set will start automatically.", color=(0.18, 0.4, 0.2, 1))
        self._update_tempo_hint()
        self._update_live_labels()

    def _start_between_exercise_rest(self, *, skipped: bool) -> None:
        if not self.live_active:
            return
        exercise = self._current_live_exercise()
        if not exercise:
            return
        at_last_exercise = self._live_current_index >= len(self.live_exercises) - 1
        status = "skipped" if skipped else "completed"
        self._record_attempt(status)
        if at_last_exercise:
            self._flash_signal("Last exercise finished.", color=(0.18, 0.5, 0.3, 1))
            self.end_live_session(early=skipped)
            return
        self._live_phase = "between_exercises"
        self._live_rest_remaining = float(self.live_rest_seconds)
        self.live_state_display = "Resting before next exercise"
        self.live_rest_timer = self._format_time(self._live_rest_remaining)
        self._set_hint("Exercise finished. Resting before the next one.", color=(0.18, 0.4, 0.2, 1))
        self._flash_signal("Exercise complete — rest break", color=(0.85, 0.55, 0.2, 1))
        self._update_tempo_hint()
        self._update_live_labels()

    def _advance_exercise(self, *, skipped: bool = False, record_status: bool = True) -> None:
        if record_status:
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
        self._flash_signal(f"Starting {self.live_exercise_title}", color=(0.16, 0.32, 0.6, 1))

    def skip_current_exercise(self) -> None:
        if not self.live_active or not self.live_started:
            return
        self._start_between_exercise_rest(skipped=True)

    def manual_next_exercise(self) -> None:
        if not self.live_active or not self.live_started:
            return
        self._start_between_exercise_rest(skipped=False)

    def manual_complete_set(self) -> None:
        if not self.live_active or not self.live_started or self._live_phase in ("rest", "between_exercises"):
            return
        self._complete_current_set(auto=False)

    def toggle_live_pause(self) -> None:
        if not self.live_active or not self.live_started:
            return
        self.live_paused = not self.live_paused
        if self.live_paused:
            self.live_state_display = "Paused"
            self._set_hint("Paused – timers stopped.", color=(0.65, 0.3, 0.18, 1))
        else:
            if self._live_phase == "rest":
                self.live_state_display = "Resting"
            elif self._live_phase == "between_exercises":
                self.live_state_display = "Resting before next exercise"
            else:
                self.live_state_display = "In set"
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
        self.live_started = False
        self._live_phase = "idle"
        self._live_rest_remaining = 0.0
        self._stop_live_clock()
        self.live_rest_timer = "—"
        self.live_set_timer = self._format_time(self._live_set_elapsed)
        self.live_exercise_timer = self._format_time(self._live_exercise_elapsed)
        self.live_upcoming_display = "Session ended"
        try:
            Animation.cancel_all(self, "live_exercise_progress")
        except Exception:
            pass
        self.live_exercise_progress = 0.0
        self.live_progress_timer = "00:00"
        self.live_progress_color = (0.18, 0.4, 0.85, 1)
        attempts = self._collect_attempts(mark_unattempted_skipped=early)
        completed_count = sum(1 for att in attempts if att.get("status") == "completed")
        skipped_count = sum(1 for att in attempts if att.get("status") == "skipped")
        status = "Workout finished" if not early else "Workout ended early"
        summary = f"{status}. Completed {completed_count}, skipped {skipped_count}."
        self.live_state_display = status
        self.live_progress_display = summary
        self._set_hint(summary, color=(0.18, 0.4, 0.2, 1), clear_after=0)
        self.live_signal_text = ""
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
