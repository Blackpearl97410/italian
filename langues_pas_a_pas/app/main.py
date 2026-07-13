from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.paths import SEED_DIR
from database.db import create_session, engine
from database.init_db import ensure_languages, init_db
from database.seed_data import seed_database
from ui.main_window import MainWindow


STYLE = """
QWidget {
    font-size: 15px;
    color: #17202a;
    background: #f7f8fa;
}
QPushButton {
    background: #1f6feb;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background: #195cc4;
}
QPushButton:disabled {
    background: #a8b3c2;
}
QLineEdit, QTextEdit {
    background: white;
    border: 1px solid #c9d1d9;
    border-radius: 6px;
    padding: 9px;
}
QRadioButton {
    padding: 8px;
}
QLabel#title {
    font-size: 34px;
    font-weight: 800;
}
QLabel#screenTitle {
    font-size: 24px;
    font-weight: 750;
    margin-bottom: 8px;
}
QLabel#sectionTitle {
    font-size: 18px;
    font-weight: 700;
    margin-top: 14px;
}
QFrame#compareCard, QWidget#listRow, QLabel#grammarBox, QFrame#progressCard {
    background: white;
    border: 1px solid #d8dee7;
    border-radius: 8px;
    padding: 12px;
}
QLabel#languageLabel, QLabel#cardLabel {
    color: #57606a;
    font-size: 12px;
    font-weight: 700;
}
QLabel#phraseText, QLabel#cardMetric {
    font-size: 18px;
    font-weight: 700;
}
QLabel#trapText {
    color: #8a3b12;
}
QLabel#feedbackBox {
    background: #eef6ff;
    border: 1px solid #82b7ff;
    border-radius: 8px;
    padding: 12px;
}
QLabel#feedbackBox[state="wrong"] {
    background: #fff4e5;
    border-color: #f2a65a;
}
QLabel#feedbackBox[state="correct"] {
    background: #eaf7ef;
    border-color: #6fcf97;
}
"""


def bootstrap_database() -> None:
    init_db(engine)
    session = create_session()
    try:
        ensure_languages(session)
        seed_database(session, SEED_DIR / "situations_seed.json")
    finally:
        session.close()


def main() -> int:
    bootstrap_database()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

