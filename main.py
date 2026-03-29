# main.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt

from database import init_db
from pages.dashboard_page import DashboardPage
from pages.register_page import RegisterPage
from pages.attendance_page import AttendancePage
from pages.records_page import RecordsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Attendance System")
        self.setGeometry(200, 100, 1200, 700)

        self.sidebar_buttons = []

        self.base_btn_style = """
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                font-size: 16px;
                padding: 10px 8px;
                text-align: left;
                border: none;
                border-left: 4px solid transparent;
            }
            QPushButton:hover {
                color: #00e5ff;
                border-left: 4px solid #00e5ff;
            }
        """
        self.active_btn_style = """
            QPushButton {
                background-color: #101020;
                color: #ff2bd6;
                font-size: 16px;
                padding: 10px 8px;
                text-align: left;
                border: none;
                border-left: 4px solid #ff2bd6;
            }
        """

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # SIDEBAR
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(16)

        logo = QLabel("SMART\nATTENDANCE")
        logo.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        sidebar_layout.addWidget(logo)

        def make_btn(text, icon_path, page_index):
            btn = QPushButton(f"  {text}")
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(22, 22))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self.base_btn_style)
            btn.clicked.connect(lambda _, i=page_index, b=btn: self.handle_nav(i, b))
            self.sidebar_buttons.append(btn)
            sidebar_layout.addWidget(btn)
            return btn

        self.btn_dashboard = make_btn("Dashboard", "assets/icons/dashboard.png", 0)
        self.btn_register = make_btn("Register User", "assets/icons/register.png", 1)
        self.btn_attendance = make_btn("Start Attendance", "assets/icons/camera.png", 2)
        self.btn_records = make_btn("Attendance Records", "assets/icons/records.png", 3)

        sidebar_layout.addStretch()
        sidebar_widget.setFixedWidth(260)

        # PAGES
        self.pages = QStackedWidget()
        self.pages.setObjectName("contentArea")
        self.pages.addWidget(DashboardPage())
        self.pages.addWidget(RegisterPage())
        self.pages.addWidget(AttendancePage())
        self.pages.addWidget(RecordsPage())

        root_layout.addWidget(sidebar_widget)
        root_layout.addWidget(self.pages)

        self.handle_nav(0, self.btn_dashboard)

    def handle_nav(self, index, button):
        self.pages.setCurrentIndex(index)
        self.set_active_button(button)

    def set_active_button(self, active_btn):
        for btn in self.sidebar_buttons:
            if btn is active_btn:
                btn.setStyleSheet(self.active_btn_style)
            else:
                btn.setStyleSheet(self.base_btn_style)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    init_db()

    try:
        with open("theme_neon.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
