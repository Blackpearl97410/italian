from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from database.db import create_session
from services.import_service import ImportService


class ImportScreen(QWidget):
    back_home = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.selected_path: Path | None = None
        layout = QVBoxLayout(self)
        title = QLabel("Importer du contenu source")
        title.setObjectName("screenTitle")
        self.path_label = QLabel("Aucun fichier selectionne.")
        self.path_label.setWordWrap(True)
        choose = QPushButton("Choisir un fichier JSON ou CSV")
        choose.clicked.connect(self.choose_file)
        validate = QPushButton("Valider")
        validate.clicked.connect(self.validate_file)
        importer = QPushButton("Importer en base")
        importer.clicked.connect(self.import_file)
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        back = QPushButton("Retour")
        back.clicked.connect(self.back_home.emit)
        for widget in (title, self.path_label, choose, validate, importer, self.result, back):
            layout.addWidget(widget)

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier",
            "",
            "Contenus (*.json *.csv)",
        )
        if path:
            self.selected_path = Path(path)
            self.path_label.setText(str(self.selected_path))

    def validate_file(self) -> None:
        if self.selected_path is None:
            self.result.setText("Selectionnez un fichier d'abord.")
            return
        session = create_session()
        try:
            result = ImportService(session).validate_file(self.selected_path)
        finally:
            session.close()
        self._display_result(result.valid, result.errors, "Validation")

    def import_file(self) -> None:
        if self.selected_path is None:
            self.result.setText("Selectionnez un fichier d'abord.")
            return
        session = create_session()
        try:
            result = ImportService(session).import_file(self.selected_path)
        finally:
            session.close()
        if result.valid:
            self.result.setText(f"Import termine. Situations importees : {result.imported_situations}")
        else:
            self._display_result(False, result.errors, "Import")

    def _display_result(self, valid: bool, errors: list[str], label: str) -> None:
        if valid:
            self.result.setText(f"{label} OK. Le contenu peut etre importe.")
            return
        self.result.setText(f"{label} invalide:\n" + "\n".join(f"- {error}" for error in errors))

