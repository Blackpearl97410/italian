from __future__ import annotations

from PySide6.QtWidgets import QLabel


class FeedbackBox(QLabel):
    def __init__(self) -> None:
        super().__init__("")
        self.setWordWrap(True)
        self.setObjectName("feedbackBox")
        self.hide()

    def show_feedback(self, text: str, is_correct: bool) -> None:
        self.setText(text)
        self.setProperty("state", "correct" if is_correct else "wrong")
        self.style().unpolish(self)
        self.style().polish(self)
        self.show()

