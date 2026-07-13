from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class ProgressCard(QFrame):
    def __init__(self, title: str, value: str) -> None:
        super().__init__()
        self.setObjectName("progressCard")
        layout = QVBoxLayout(self)
        label = QLabel(title)
        label.setObjectName("cardLabel")
        metric = QLabel(value)
        metric.setObjectName("cardMetric")
        layout.addWidget(label)
        layout.addWidget(metric)

