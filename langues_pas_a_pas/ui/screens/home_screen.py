from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class HomeScreen(QWidget):
    show_situations = Signal()
    show_dashboard = Signal()
    show_import = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        title = QLabel("Langues Pas a Pas")
        title.setObjectName("title")
        subtitle = QLabel("Apprendre l'anglais et l'italien depuis le francais, situation par situation.")
        subtitle.setWordWrap(True)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        start = QPushButton("Commencer")
        start.clicked.connect(self.show_situations.emit)
        continue_button = QPushButton("Continuer")
        continue_button.clicked.connect(self.show_situations.emit)
        dashboard = QPushButton("Tableau de bord")
        dashboard.clicked.connect(self.show_dashboard.emit)
        importer = QPushButton("Importer du contenu")
        importer.clicked.connect(self.show_import.emit)
        for button in (start, continue_button, dashboard, importer):
            button.setMinimumHeight(44)
            layout.addWidget(button)
        layout.addStretch()

