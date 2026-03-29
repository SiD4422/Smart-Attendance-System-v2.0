# splash_screen.py
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt


class SplashScreen(QSplashScreen):
    def __init__(self):
        # you can replace with your own image
        pix = QPixmap("assets/icons/splash_bg.png")
        if pix.isNull():
            # fallback – solid background if image not found
            super().__init__()
            self.setStyleSheet("background-color:#050509;")
        else:
            super().__init__(pix)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFont(QFont("Segoe UI", 10))
        self.showMessage(
            "Initializing AI Attendance Engine…",
            Qt.AlignBottom | Qt.AlignHCenter,
            Qt.white,
        )
