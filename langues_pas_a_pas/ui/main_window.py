from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.exercise_screen import ExerciseScreen
from ui.screens.home_screen import HomeScreen
from ui.screens.import_screen import ImportScreen
from ui.screens.lesson_screen import LessonScreen
from ui.screens.situations_screen import SituationsScreen


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Langues Pas a Pas")
        self.resize(1100, 760)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.home = HomeScreen()
        self.situations = SituationsScreen()
        self.lesson = LessonScreen()
        self.exercise = ExerciseScreen()
        self.dashboard = DashboardScreen()
        self.import_screen = ImportScreen()
        for screen in (
            self.home,
            self.situations,
            self.lesson,
            self.exercise,
            self.dashboard,
            self.import_screen,
        ):
            self.stack.addWidget(screen)
        self._connect()

    def _connect(self) -> None:
        self.home.show_situations.connect(self.show_situations)
        self.home.show_dashboard.connect(self.show_dashboard)
        self.home.show_import.connect(lambda: self.stack.setCurrentWidget(self.import_screen))
        self.situations.back_home.connect(self.show_home)
        self.situations.open_situation.connect(self.show_lesson)
        self.lesson.back_situations.connect(self.show_situations)
        self.lesson.start_exercises.connect(self.show_exercises)
        self.exercise.back_situations.connect(self.show_situations)
        self.dashboard.back_home.connect(self.show_home)
        self.import_screen.back_home.connect(self.show_home)

    def show_home(self) -> None:
        self.stack.setCurrentWidget(self.home)

    def show_situations(self) -> None:
        self.situations.refresh()
        self.stack.setCurrentWidget(self.situations)

    def show_lesson(self, situation_id: int) -> None:
        self.lesson.load_situation(situation_id)
        self.stack.setCurrentWidget(self.lesson)

    def show_exercises(self, situation_id: int) -> None:
        self.exercise.load_situation(situation_id)
        self.stack.setCurrentWidget(self.exercise)

    def show_dashboard(self) -> None:
        self.dashboard.refresh()
        self.stack.setCurrentWidget(self.dashboard)

