# pages/attendance_page.py
"""
Attendance Page with Real-time Face Recognition
Modern UI with live camera feed and instant recognition
"""
import cv2
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTextEdit, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
import logging

from recognizer import recognize_and_annotate, get_last_event, get_model
from database import get_today_attendance_count, get_total_users, get_last_marked_user

logger = logging.getLogger(__name__)


class AttendancePage(QWidget):
    """Real-time attendance marking page"""
    
    def __init__(self):
        super().__init__()
        
        self.camera = None
        self.active = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        
        self.last_marked_name = None
        self.marked_cooldown = {}  # Prevent duplicate marking
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📹 Live Attendance")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        
        header.addStretch()
        
        # Stats
        self.today_count_label = QLabel("Today: 0")
        self.today_count_label.setStyleSheet("color: #00e5ff; font-size: 16px; font-weight: bold;")
        header.addWidget(self.today_count_label)
        
        self.total_users_label = QLabel("Total: 0")
        self.total_users_label.setStyleSheet("color: #ff2bd6; font-size: 16px; font-weight: bold;")
        header.addWidget(self.total_users_label)
        
        layout.addLayout(header)
        
        subtitle = QLabel("Real-time face recognition and attendance marking")
        subtitle.setObjectName("mutedLabel")
        layout.addWidget(subtitle)
        
        # Main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # LEFT - Camera feed
        camera_container = QFrame()
        camera_container.setObjectName("glassCard")
        
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(20, 20, 20, 20)
        camera_layout.setSpacing(15)
        
        camera_title = QLabel("📷 Live Camera Feed")
        camera_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        camera_title.setStyleSheet("color: #00e5ff;")
        camera_layout.addWidget(camera_title)
        
        # Camera display
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setMaximumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #0a0a0a;
                border: 3px solid #00e5ff;
                border-radius: 12px;
            }
        """)
        self.camera_label.setText("📹\n\nLive Feed\n\nClick 'Start Camera' to begin")
        camera_layout.addWidget(self.camera_label)
        
        # Camera controls
        controls = QHBoxLayout()
        
        self.start_btn = QPushButton("🎥 Start Camera")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00e5ff, stop:1 #0088cc);
                color: white;
                font-weight: bold;
                font-size: 15px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #18f5ff, stop:1 #00a0ee);
            }
        """)
        self.start_btn.clicked.connect(self.toggle_camera)
        controls.addWidget(self.start_btn)
        
        refresh_btn = QPushButton("🔄 Refresh Stats")
        refresh_btn.setMinimumHeight(50)
        refresh_btn.clicked.connect(self.refresh_stats)
        controls.addWidget(refresh_btn)
        
        camera_layout.addLayout(controls)
        
        content_layout.addWidget(camera_container)
        
        # RIGHT - Activity log & stats
        right_container = QFrame()
        right_container.setObjectName("glassCard")
        right_container.setMinimumWidth(350)
        right_container.setMaximumWidth(400)
        
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)
        
        # Stats cards
        stats_title = QLabel("📊 Today's Statistics")
        stats_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        stats_title.setStyleSheet("color: #ff2bd6;")
        right_layout.addWidget(stats_title)
        
        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)
        
        self.present_card = self.create_mini_stat_card("Present", "0", "#00ff88")
        self.absent_card = self.create_mini_stat_card("Absent", "0", "#ff6b6b")
        self.rate_card = self.create_mini_stat_card("Rate", "0%", "#00e5ff")
        self.last_card = self.create_mini_stat_card("Last Marked", "None", "#ffa500")
        
        stats_grid.addWidget(self.present_card, 0, 0)
        stats_grid.addWidget(self.absent_card, 0, 1)
        stats_grid.addWidget(self.rate_card, 1, 0)
        stats_grid.addWidget(self.last_card, 1, 1)
        
        right_layout.addLayout(stats_grid)
        
        # Activity log
        log_title = QLabel("📋 Activity Log")
        log_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        log_title.setStyleSheet("color: #00e5ff;")
        right_layout.addWidget(log_title)
        
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                border: 1px solid #23233a;
                border-radius: 8px;
                color: #e0e0e0;
                padding: 10px;
                font-size: 12px;
                font-family: 'Consolas', monospace;
            }
        """)
        right_layout.addWidget(self.activity_log)
        
        content_layout.addWidget(right_container)
        
        layout.addLayout(content_layout)
        
        # Initial refresh
        self.refresh_stats()
        self.log_activity("ℹ️ System ready", "#00e5ff")
    
    def create_mini_stat_card(self, title, value, color):
        """Create mini stat card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        card.setMinimumHeight(80)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #b0b0c0; font-size: 10px;")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        setattr(card, 'value_label', value_label)
        card_layout.addWidget(value_label)
        
        return card
    
    def toggle_camera(self):
        """Start/stop camera"""
        if not self.active:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Start camera"""
        try:
            # Check if model is trained
            model, labels = get_model()
            if model is None:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Model Not Trained",
                    "No trained model found!\n\nPlease register users first."
                )
                return
            
            # Check if users are registered in database
            from database import get_total_users
            if get_total_users() == 0:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "No Users Registered",
                    "No users found in database!\n\nPlease register users first using the 'Register User' page."
                )
                return
            
            # Open camera
            for cam_idx in [0, 1, 2]:
                self.camera = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
                if self.camera.isOpened():
                    break
            
            if not self.camera or not self.camera.isOpened():
                self.camera = cv2.VideoCapture(0)
            
            if not self.camera or not self.camera.isOpened():
                raise Exception("Cannot open camera")
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.active = True
            self.timer.start(30)
            
            self.start_btn.setText("⏹️ Stop Camera")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff2bd6, stop:1 #cc0099);
                    color: white;
                    font-weight: bold;
                    font-size: 15px;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff4de6, stop:1 #ee00bb);
                }
            """)
            
            self.log_activity("✅ Camera started", "#00ff88")
            
        except Exception as e:
            logger.error(f"Camera error: {e}")
            self.log_activity(f"❌ Camera error: {e}", "#ff0000")
    
    def stop_camera(self):
        """Stop camera"""
        self.timer.stop()
        self.active = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.camera_label.clear()
        self.camera_label.setText("📹\n\nCamera Stopped\n\nClick 'Start Camera' to resume")
        
        self.start_btn.setText("🎥 Start Camera")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00e5ff, stop:1 #0088cc);
                color: white;
                font-weight: bold;
                font-size: 15px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #18f5ff, stop:1 #00a0ee);
            }
        """)
        
        self.log_activity("⏹️ Camera stopped", "#ffa500")
    
    def process_frame(self):
        """Process camera frame"""
        if not self.camera or not self.camera.isOpened():
            return
        
        ret, frame = self.camera.read()
        if not ret:
            return
        
        # Run recognition
        frame = recognize_and_annotate(frame)
        
        # Check for recognition events
        event = get_last_event()
        if event:
            name = event.get('name')
            status = event.get('status')
            
            # Log attendance
            if name and status and name != self.last_marked_name:
                self.last_marked_name = name
                
                if status == "Marked":
                    self.log_activity(f"✅ {name} - Attendance marked", "#00ff88")
                    self.refresh_stats()
                elif status == "Already Marked":
                    self.log_activity(f"ℹ️ {name} - Already marked today", "#00e5ff")
                elif status == "Unknown":
                    self.log_activity(f"⚠️ Unknown person detected", "#ffa500")
            
            if status == "Spoof":
                self.log_activity(f"🛡️ Spoof attempt detected!", "#ff0000")
        
        # Convert and display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qt_image = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        self.camera_label.setPixmap(pixmap.scaled(
            self.camera_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
    
    def refresh_stats(self):
        """Refresh statistics"""
        try:
            today_count = get_today_attendance_count()
            total_users = get_total_users()
            
            self.present_card.value_label.setText(str(today_count))
            absent_count = max(0, total_users - today_count)
            self.absent_card.value_label.setText(str(absent_count))
            
            if total_users > 0:
                rate = (today_count / total_users) * 100
                self.rate_card.value_label.setText(f"{rate:.0f}%")
            else:
                self.rate_card.value_label.setText("0%")
            
            # Last marked
            last = get_last_marked_user()
            if last:
                name, time = last
                self.last_card.value_label.setText(name[:10])
                self.last_card.value_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            else:
                self.last_card.value_label.setText("None")
            
            # Update header
            self.today_count_label.setText(f"Today: {today_count}")
            self.total_users_label.setText(f"Total: {total_users}")
            
        except Exception as e:
            logger.error(f"Stats refresh error: {e}")
    
    def log_activity(self, message, color="#e0e0e0"):
        """Add to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(
            f'<span style="color:{color};">[{timestamp}] {message}</span>'
        )
        
        # Auto scroll to bottom
        self.activity_log.verticalScrollBar().setValue(
            self.activity_log.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """Clean up"""
        self.stop_camera()
        event.accept()
