from __future__ import annotations

import json

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from database.db import create_session
from domain.models import Exercise
from services.exercise_service import ExerciseService
from services.progress_service import ProgressService
from ui.widgets.feedback_box import FeedbackBox


class ExerciseScreen(QWidget):
    back_situations = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.situation_id: int | None = None
        self.exercises: list[Exercise] = []
        self.index = 0
        self.correct_count = 0
        self.answered = False
        self.layout = QVBoxLayout(self)
        self.progress_label = QLabel("")
        self.question = QLabel("")
        self.question.setWordWrap(True)
        self.question.setObjectName("screenTitle")
        self.options_group = QButtonGroup(self)
        self.options_widget = QWidget()
        self.options_layout = QVBoxLayout(self.options_widget)
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Votre reponse")
        self.feedback = FeedbackBox()
        self.validate_button = QPushButton("Valider")
        self.validate_button.clicked.connect(self.validate_answer)
        self.next_button = QPushButton("Suivant")
        self.next_button.clicked.connect(self.next_exercise)
        self.back_button = QPushButton("Retour aux situations")
        self.back_button.clicked.connect(self.back_situations.emit)
        for widget in (
            self.progress_label,
            self.question,
            self.options_widget,
            self.answer_input,
            self.feedback,
            self.validate_button,
            self.next_button,
            self.back_button,
        ):
            self.layout.addWidget(widget)
        self.layout.addStretch()

    def load_situation(self, situation_id: int) -> None:
        self.situation_id = situation_id
        self.index = 0
        self.correct_count = 0
        session = create_session()
        try:
            self.exercises = ExerciseService(session).list_for_situation(situation_id)
        finally:
            session.close()
        self.show_current()

    def show_current(self) -> None:
        self.feedback.hide()
        self.answered = False
        self.next_button.setEnabled(False)
        self.validate_button.setEnabled(True)
        self.answer_input.clear()
        self._clear_options()
        if not self.exercises:
            self.question.setText("Aucun exercice disponible.")
            return
        exercise = self.exercises[self.index]
        self.progress_label.setText(f"Exercice {self.index + 1}/{len(self.exercises)} - {exercise.type}")
        self.question.setText(exercise.question)
        options = json.loads(exercise.options_json or "[]")
        if options:
            self.answer_input.hide()
            self.options_widget.show()
            for option in options:
                radio = QRadioButton(option)
                self.options_group.addButton(radio)
                self.options_layout.addWidget(radio)
        else:
            self.options_widget.hide()
            self.answer_input.show()

    def validate_answer(self) -> None:
        if self.answered or not self.exercises:
            return
        exercise = self.exercises[self.index]
        answer = self._selected_answer()
        if not answer:
            self.feedback.show_feedback("Saisissez ou selectionnez une reponse.", False)
            return
        session = create_session()
        try:
            result = ExerciseService(session).answer(exercise, answer)
            if result.is_correct:
                self.correct_count += 1
            self.feedback.show_feedback(result.message, result.is_correct)
        finally:
            session.close()
        self.answered = True
        self.validate_button.setEnabled(False)
        self.next_button.setEnabled(True)

    def next_exercise(self) -> None:
        if self.index + 1 < len(self.exercises):
            self.index += 1
            self.show_current()
            return
        if self.situation_id is not None:
            session = create_session()
            try:
                ProgressService(session).update_situation_score(
                    self.situation_id,
                    self.correct_count,
                    len(self.exercises),
                )
            finally:
                session.close()
        self.question.setText(f"Serie terminee. Score : {self.correct_count}/{len(self.exercises)}")
        self.progress_label.setText("Bravo, revision enregistree.")
        self.options_widget.hide()
        self.answer_input.hide()
        self.validate_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def _selected_answer(self) -> str:
        checked = self.options_group.checkedButton()
        if checked:
            return checked.text()
        return self.answer_input.text()

    def _clear_options(self) -> None:
        for button in self.options_group.buttons():
            self.options_group.removeButton(button)
            button.deleteLater()
        while self.options_layout.count():
            child = self.options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

