from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from database.db import create_session
from services.lesson_service import LessonService
from services.progress_service import ProgressService
from ui.widgets.language_compare_card import LanguageCompareCard


class LessonScreen(QWidget):
    start_exercises = Signal(int)
    back_situations = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.situation_id: int | None = None
        self.layout = QVBoxLayout(self)
        self.title = QLabel("")
        self.title.setObjectName("screenTitle")
        self.objective = QLabel("")
        self.objective.setWordWrap(True)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.objective)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.cards_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        self.exercise_button = QPushButton("Faire les exercices")
        self.exercise_button.clicked.connect(self._start)
        back = QPushButton("Retour aux situations")
        back.clicked.connect(self.back_situations.emit)
        self.layout.addWidget(self.exercise_button)
        self.layout.addWidget(back)

    def load_situation(self, situation_id: int) -> None:
        self.situation_id = situation_id
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        session = create_session()
        try:
            ProgressService(session).mark_opened(situation_id)
            situation = LessonService(session).get_situation(situation_id)
            if situation is None:
                self.title.setText("Situation introuvable")
                return
            self.title.setText(f"{situation.title} - {situation.level}")
            self.objective.setText(situation.objective)
            for phrase in situation.phrases:
                self.cards_layout.addWidget(LanguageCompareCard(phrase))
            if situation.grammar_points:
                grammar_title = QLabel("Points grammaticaux")
                grammar_title.setObjectName("sectionTitle")
                self.cards_layout.addWidget(grammar_title)
                for grammar in situation.grammar_points:
                    label = QLabel(
                        f"{grammar.title}\n{grammar.explanation}\n"
                        f"FR: {grammar.example_fr}\nEN: {grammar.example_en}\nIT: {grammar.example_it}"
                    )
                    label.setWordWrap(True)
                    label.setObjectName("grammarBox")
                    self.cards_layout.addWidget(label)
            self.cards_layout.addStretch()
        finally:
            session.close()

    def _start(self) -> None:
        if self.situation_id is not None:
            self.start_exercises.emit(self.situation_id)

