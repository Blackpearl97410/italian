from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from domain.models import Phrase


class LanguageCompareCard(QFrame):
    def __init__(self, phrase: Phrase) -> None:
        super().__init__()
        self.setObjectName("compareCard")
        layout = QVBoxLayout(self)
        grid = QGridLayout()
        for col, label in enumerate(("FR", "EN", "IT")):
            title = QLabel(label)
            title.setObjectName("languageLabel")
            grid.addWidget(title, 0, col)
        for col, text in enumerate((phrase.fr_text, phrase.en_text, phrase.it_text)):
            value = QLabel(text)
            value.setWordWrap(True)
            value.setObjectName("phraseText")
            grid.addWidget(value, 1, col)
        layout.addLayout(grid)
        explanation = QLabel(phrase.explanation)
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        trap = QLabel(f"Piege frequent : {phrase.common_trap}")
        trap.setWordWrap(True)
        trap.setObjectName("trapText")
        layout.addWidget(trap)

