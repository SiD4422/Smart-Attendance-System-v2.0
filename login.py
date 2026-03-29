# login.py
import sys
import cv2
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QApplication, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, QTimer

from recognizer import recognize_and_annotate, get_model, get_last_event
from main import MainWindow
from database import init_db


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        init_db()

        self.faceid_cap = None
        self.faceid_active = False
        self.faceid_timer = QTimer(self)
        self.faceid_timer.timeout.connect(self.faceid_capture_frame)

        self.setWindowTitle("Smart Attendance – Login")
        self.setGeometry(400, 120, 420, 580)
        self.setStyleSheet("background-color: transparent;")

        # Background
        self.bg = QLabel(self)
        self.bg.setPixmap(QPixmap("assets/icons/bg.jpg").scaled(
            self.width(), self.height(), Qt.KeepAspectRatioByExpanding
        ))
        self.bg.setGeometry(0, 0, self.width(), self.height())

        # Glass card
        self.card = QWidget(self)
        self.card.setGeometry(80, 120, 260, 360)
        self.card.setStyleSheet("""
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 22px;
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        title = QLabel("Welcome Back")
        title.setFont(QFont("Segoe UI", 17, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Sign in to continue")
        subtitle.setStyleSheet("color: #cccccc; font-size: 11px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet(self._input_style())
        layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Password")
        self.password.setStyleSheet(self._input_style())
        layout.addWidget(self.password)

        btn_faceid = QPushButton("Login with FaceID")
        btn_faceid.setStyleSheet(self._faceid_button())
        btn_faceid.clicked.connect(self.start_faceid_login)
        layout.addWidget(btn_faceid)

        btn_login = QPushButton("Sign In")
        btn_login.setStyleSheet(self._login_button())
        btn_login.clicked.connect(self.check_login)
        layout.addWidget(btn_login)

    def _input_style(self):
        return """
        QLineEdit {
            background: rgba(0,0,0,0);
            border: 1px solid rgba(255,255,255,0.35);
            border-radius: 10px;
            padding: 8px;
            color: white;
        }
        QLineEdit:focus {
            border: 1px solid #00e5ff;
        }
        """

    def _faceid_button(self):
        return """
        QPushButton {
            background-color: rgba(0,229,255,0.2);
            color: white;
            padding: 8px;
            border-radius: 10px;
            border: 1px solid #00e5ff;
        }
        QPushButton:hover {
            background-color: rgba(0,229,255,0.35);
        }
        """

    def _login_button(self):
        return """
        QPushButton {
            background-color: #ff007f;
            color: white;
            padding: 10px;
            border-radius: 12px;
        }
        QPushButton:hover {
            background-color: #ff4da6;
        }
        """

    def check_login(self):
        if self.username.text().strip() == "admin" and self.password.text().strip() == "1234":
            win = MainWindow()
            win.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password!")

    def start_faceid_login(self):
        model, labels = get_model()
        if model is None:
            QMessageBox.warning(self, "Error", "Train the model first.")
            return

        self.faceid_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.faceid_cap.isOpened():
            QMessageBox.warning(self, "Error", "Camera not available.")
            return

        self.faceid_active = True
        self.faceid_timer.start(40)
        QMessageBox.information(self, "FaceID", "Look at the camera…")

    def stop_faceid(self):
        self.faceid_timer.stop()
        if self.faceid_cap:
            self.faceid_cap.release()
        self.faceid_active = False

    def faceid_capture_frame(self):
        if not self.faceid_active or self.faceid_cap is None:
            return

        ret, frame = self.faceid_cap.read()
        if not ret:
            return

        recognize_and_annotate(frame)
        evt = get_last_event()

        if evt and evt.get("status") != "Spoof" and evt.get("name"):
            name = evt["name"]
            self.stop_faceid()
            QMessageBox.information(self, "FaceID", f"Welcome, {name}!")
            win = MainWindow()
            win.show()
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        with open("theme_neon.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())
