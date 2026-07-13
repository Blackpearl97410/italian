from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from database.db import create_session
from services.progress_service import ProgressService
from services.review_service import ReviewService
from ui.widgets.progress_card import ProgressCard


class DashboardScreen(QWidget):
    back_home = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.layout = QVBoxLayout(self)
        title = QLabel("Tableau de bord")
        title.setObjectName("screenTitle")
        self.layout.addWidget(title)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.layout.addWidget(self.cards_container)
        self.mistakes = QLabel("")
        self.mistakes.setWordWrap(True)
        self.layout.addWidget(self.mistakes)
        back = QPushButton("Retour")
        back.clicked.connect(self.back_home.emit)
        self.layout.addWidget(back)
        self.layout.addStretch()

    def refresh(self) -> None:
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        session = create_session()
        try:
            stats = ProgressService(session).dashboard_stats()
            review = ReviewService(session)
            self.cards_layout.addWidget(ProgressCard("Situations commencees", str(stats["started"])))
            self.cards_layout.addWidget(ProgressCard("Situations terminees", str(stats["completed"])))
            self.cards_layout.addWidget(ProgressCard("Score moyen", f"{stats['average_score']}%"))
            self.cards_layout.addWidget(ProgressCard("Elements a reviser", str(review.due_items_count())))
            mistakes = review.frequent_mistakes()
            if mistakes:
                lines = [
                    f"- {item.phrase.fr_text}: {item.mistake_count} erreur(s), prochaine revision planifiee"
                    for item in mistakes
                ]
                self.mistakes.setText("Erreurs frequentes\n" + "\n".join(lines))
            else:
                self.mistakes.setText("Erreurs frequentes\nAucune erreur enregistree pour le moment.")
        finally:
            session.close()

