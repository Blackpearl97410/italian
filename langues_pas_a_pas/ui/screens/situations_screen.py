from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from database.db import create_session
from services.lesson_service import LessonService
from services.progress_service import ProgressService


class SituationsScreen(QWidget):
    open_situation = Signal(int)
    back_home = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.layout = QVBoxLayout(self)
        header = QLabel("Parcours par situations")
        header.setObjectName("screenTitle")
        self.layout.addWidget(header)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.items_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        back = QPushButton("Retour")
        back.clicked.connect(self.back_home.emit)
        self.layout.addWidget(back)

    def refresh(self) -> None:
        while self.items_layout.count():
            child = self.items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        session = create_session()
        try:
            service = LessonService(session)
            progress_service = ProgressService(session)
            progress_by_situation = {row.situation_id: row for row in progress_service.progress.list_progress()}
            for situation in service.list_situations():
                row = QWidget()
                row.setObjectName("listRow")
                layout = QVBoxLayout(row)
                progress = progress_by_situation.get(situation.id)
                score = f"{progress.score:.0f}%" if progress else "0%"
                label = QLabel(f"{situation.order_index}. {situation.title} - {situation.level} - progression {score}")
                label.setWordWrap(True)
                objective = QLabel(situation.objective)
                objective.setWordWrap(True)
                button = QPushButton("Ouvrir")
                button.clicked.connect(lambda checked=False, sid=situation.id: self.open_situation.emit(sid))
                layout.addWidget(label)
                layout.addWidget(objective)
                layout.addWidget(button)
                self.items_layout.addWidget(row)
            self.items_layout.addStretch()
        finally:
            session.close()

