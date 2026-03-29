# pages/register_page.py
"""
User Registration Page with Face Capture
Modern UI with working camera functionality
"""
import cv2
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGridLayout, QMessageBox, QComboBox,
    QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont
import logging

from database import register_user, get_all_users
from recognizer import train_recognizer
from config import SAMPLES_PER_USER, FACES_DIR

logger = logging.getLogger(__name__)


class RegisterPage(QWidget):
    """User registration page with face capture"""
    
    registration_complete = pyqtSignal(str)  # Signal when registration completes
    
    def __init__(self):
        super().__init__()
        
        self.camera = None
        self.capture_active = False
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.captured_samples = 0
        self.max_samples = SAMPLES_PER_USER
        self.current_username = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("👤 Register New User")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.load_existing_users)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        subtitle = QLabel("Capture face samples to register a new user")
        subtitle.setObjectName("mutedLabel")
        layout.addWidget(subtitle)
        
        # Main content in two columns
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # LEFT COLUMN - User Details Form
        form_container = QFrame()
        form_container.setObjectName("glassCard")
        form_container.setMinimumWidth(400)
        form_container.setMaximumWidth(450)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(25, 25, 25, 25)
        form_layout.setSpacing(15)
        
        form_title = QLabel("📋 User Information")
        form_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        form_title.setStyleSheet("color: #00e5ff;")
        form_layout.addWidget(form_title)
        
        # User ID
        form_layout.addWidget(QLabel("User ID *"))
        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("e.g., EMP001")
        form_layout.addWidget(self.user_id_input)
        
        # Name
        form_layout.addWidget(QLabel("Full Name *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., John Doe")
        form_layout.addWidget(self.name_input)
        
        # Email
        form_layout.addWidget(QLabel("Email"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("e.g., john@example.com")
        form_layout.addWidget(self.email_input)
        
        # Phone
        form_layout.addWidget(QLabel("Phone"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g., +1234567890")
        form_layout.addWidget(self.phone_input)
        
        # Department
        form_layout.addWidget(QLabel("Department"))
        self.department_input = QComboBox()
        self.department_input.addItems([
            "Select Department",
            "IT",
            "HR",
            "Finance",
            "Marketing",
            "Operations",
            "Sales",
            "Engineering",
            "Other"
        ])
        form_layout.addWidget(self.department_input)
        
        # Role
        form_layout.addWidget(QLabel("Role"))
        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("e.g., Software Engineer")
        form_layout.addWidget(self.role_input)
        
        form_layout.addStretch()
        
        content_layout.addWidget(form_container)
        
        # RIGHT COLUMN - Camera & Capture
        camera_container = QFrame()
        camera_container.setObjectName("glassCard")
        
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(25, 25, 25, 25)
        camera_layout.setSpacing(15)
        
        camera_title = QLabel("📷 Face Capture")
        camera_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        camera_title.setStyleSheet("color: #ff2bd6;")
        camera_layout.addWidget(camera_title)
        
        # Camera display
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setMaximumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #0a0a0a;
                border: 2px solid #00e5ff;
                border-radius: 10px;
            }
        """)
        self.camera_label.setText("📷\n\nCamera Preview\n\nClick 'Start Camera' to begin")
        camera_layout.addWidget(self.camera_label)
        
        # Progress bar
        progress_layout = QVBoxLayout()
        progress_label = QLabel("Capture Progress")
        progress_label.setStyleSheet("color: #b0b0c0; font-size: 12px;")
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.max_samples)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #23233a;
                border-radius: 5px;
                text-align: center;
                background-color: #0d0d12;
                color: white;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00e5ff, stop:1 #ff2bd6);
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_text = QLabel(f"0 / {self.max_samples} samples captured")
        self.progress_text.setStyleSheet("color: #00e5ff; font-size: 11px;")
        self.progress_text.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_text)
        
        camera_layout.addLayout(progress_layout)
        
        # Camera controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.start_camera_btn = QPushButton("🎥 Start Camera")
        self.start_camera_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00e5ff, stop:1 #0088cc);
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #18f5ff, stop:1 #00a0ee);
            }
            QPushButton:pressed {
                background: #006699;
            }
        """)
        self.start_camera_btn.clicked.connect(self.toggle_camera)
        controls_layout.addWidget(self.start_camera_btn)
        
        self.capture_btn = QPushButton("📸 Start Capture")
        self.capture_btn.setEnabled(False)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff2bd6, stop:1 #cc0099);
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff4de6, stop:1 #ee00bb);
            }
            QPushButton:pressed {
                background: #990066;
            }
            QPushButton:disabled {
                background: #333333;
                color: #666666;
            }
        """)
        self.capture_btn.clicked.connect(self.start_capture)
        controls_layout.addWidget(self.capture_btn)
        
        camera_layout.addLayout(controls_layout)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                border: 1px solid #23233a;
                border-radius: 5px;
                color: #b0b0c0;
                padding: 8px;
                font-size: 11px;
            }
        """)
        self.status_text.setText("ℹ️ Fill in user details and start camera to begin registration")
        camera_layout.addWidget(self.status_text)
        
        content_layout.addWidget(camera_container)
        
        layout.addLayout(content_layout)
        
        # Bottom action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(15)
        
        self.save_btn = QPushButton("💾 Save User")
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff88, stop:1 #00cc66);
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff99, stop:1 #00dd77);
            }
            QPushButton:disabled {
                background: #333333;
                color: #666666;
            }
        """)
        self.save_btn.clicked.connect(self.save_user)
        action_layout.addWidget(self.save_btn)
        
        clear_btn = QPushButton("🗑️ Clear Form")
        clear_btn.setMinimumHeight(45)
        clear_btn.clicked.connect(self.clear_form)
        action_layout.addWidget(clear_btn)
        
        layout.addLayout(action_layout)
        
        # Load existing users
        self.load_existing_users()
    
    def add_status(self, message: str, color: str = "#b0b0c0"):
        """Add status message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f'<span style="color:{color};">[{timestamp}] {message}</span>')
        logger.info(message)
    
    def toggle_camera(self):
        """Start or stop camera"""
        if not self.capture_active:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Initialize and start camera"""
        try:
            # Try different camera indices
            for cam_idx in [0, 1, 2]:
                self.camera = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
                if self.camera.isOpened():
                    self.add_status(f"✅ Camera {cam_idx} opened successfully", "#00ff88")
                    break
            
            if not self.camera or not self.camera.isOpened():
                # Try without CAP_DSHOW
                self.camera = cv2.VideoCapture(0)
                
            if not self.camera or not self.camera.isOpened():
                raise Exception("Could not open camera")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.capture_active = True
            self.timer.start(30)  # 30ms = ~33 FPS
            
            self.start_camera_btn.setText("⏹️ Stop Camera")
            self.capture_btn.setEnabled(True)
            self.add_status("📷 Camera started", "#00e5ff")
            
        except Exception as e:
            logger.error(f"Camera error: {e}")
            QMessageBox.critical(
                self,
                "Camera Error",
                f"Failed to open camera:\n{str(e)}\n\nTry:\n"
                "1. Check if camera is connected\n"
                "2. Close other apps using camera\n"
                "3. Restart the application"
            )
            self.add_status(f"❌ Camera error: {str(e)}", "#ff0000")
    
    def stop_camera(self):
        """Stop camera"""
        self.timer.stop()
        self.capture_active = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.camera_label.clear()
        self.camera_label.setText("📷\n\nCamera Stopped\n\nClick 'Start Camera' to resume")
        
        self.start_camera_btn.setText("🎥 Start Camera")
        self.capture_btn.setEnabled(False)
        self.add_status("⏹️ Camera stopped", "#ffa500")
    
    def update_frame(self):
        """Update camera frame"""
        if not self.camera or not self.camera.isOpened():
            return
        
        ret, frame = self.camera.read()
        if not ret:
            self.add_status("⚠️ Failed to read frame", "#ff0000")
            return
        
        # Detect faces
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            color = (0, 255, 0) if len(faces) == 1 else (0, 165, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Add text
            if self.captured_samples < self.max_samples:
                text = f"Sample {self.captured_samples}/{self.max_samples}"
            else:
                text = "Capture Complete!"
            
            cv2.putText(frame, text, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Convert to QImage
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Display
        pixmap = QPixmap.fromImage(qt_image)
        self.camera_label.setPixmap(pixmap.scaled(
            self.camera_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
    
    def start_capture(self):
        """Start capturing face samples"""
        # Validate inputs
        user_id = self.user_id_input.text().strip()
        name = self.name_input.text().strip()
        
        if not user_id or not name:
            QMessageBox.warning(self, "Input Error", "User ID and Name are required!")
            return
        
        # Check if already exists
        users = get_all_users()
        if any(u['name'].lower() == name.lower() for u in users):
            QMessageBox.warning(self, "User Exists", f"User '{name}' already registered!")
            return
        
        self.current_username = name
        self.captured_samples = 0
        self.progress_bar.setValue(0)
        
        # Create directory
        os.makedirs(FACES_DIR, exist_ok=True)
        
        self.capture_btn.setText("⏸️ Stop Capture")
        self.capture_btn.clicked.disconnect()
        self.capture_btn.clicked.connect(self.stop_capture)
        
        self.add_status(f"📸 Starting capture for '{name}'...", "#00e5ff")
        self.timer.timeout.disconnect()
        self.timer.timeout.connect(self.capture_frame)
    
    def capture_frame(self):
        """Capture face samples"""
        if not self.camera or not self.camera.isOpened():
            return
        
        ret, frame = self.camera.read()
        if not ret:
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Capture if face detected
        if len(faces) == 1 and self.captured_samples < self.max_samples:
            (x, y, w, h) = faces[0]
            face_roi = gray[y:y + h, x:x + w]
            face_roi = cv2.resize(face_roi, (200, 200))
            
            # Save sample
            filename = os.path.join(FACES_DIR, f"{self.current_username}_{self.captured_samples + 1}.jpg")
            cv2.imwrite(filename, face_roi)
            
            self.captured_samples += 1
            self.progress_bar.setValue(self.captured_samples)
            self.progress_text.setText(f"{self.captured_samples} / {self.max_samples} samples captured")
            
            if self.captured_samples % 5 == 0:
                self.add_status(f"✅ Captured {self.captured_samples} samples", "#00ff88")
        
        # Draw on frame
        for (x, y, w, h) in faces:
            color = (0, 255, 0) if len(faces) == 1 else (0, 165, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{self.captured_samples}/{self.max_samples}",
                       (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qt_image = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.camera_label.setPixmap(pixmap.scaled(
            self.camera_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        
        # Check if complete
        if self.captured_samples >= self.max_samples:
            self.capture_complete()
    
    def capture_complete(self):
        """Handle capture completion"""
        self.timer.timeout.disconnect()
        self.timer.timeout.connect(self.update_frame)
        
        self.capture_btn.setText("📸 Start Capture")
        self.capture_btn.clicked.disconnect()
        self.capture_btn.clicked.connect(self.start_capture)
        self.capture_btn.setEnabled(False)
        
        self.save_btn.setEnabled(True)
        
        self.add_status(f"🎉 Capture complete! {self.max_samples} samples saved", "#00ff88")
        QMessageBox.information(
            self,
            "Capture Complete",
            f"Successfully captured {self.max_samples} samples!\n\nClick 'Save User' to complete registration."
        )
    
    def stop_capture(self):
        """Stop capturing"""
        self.timer.timeout.disconnect()
        self.timer.timeout.connect(self.update_frame)
        
        self.capture_btn.setText("📸 Start Capture")
        self.capture_btn.clicked.disconnect()
        self.capture_btn.clicked.connect(self.start_capture)
        
        self.add_status("⏸️ Capture paused", "#ffa500")
    
    def save_user(self):
        """Save user to database"""
        try:
            user_id = self.user_id_input.text().strip()
            name = self.name_input.text().strip()
            email = self.email_input.text().strip() or None
            phone = self.phone_input.text().strip() or None
            department = self.department_input.currentText()
            if department == "Select Department":
                department = None
            role = self.role_input.text().strip() or None
            join_date = datetime.now().strftime("%Y-%m-%d")
            
            # Register user
            register_user(
                user_id=user_id,
                name=name,
                email=email,
                phone=phone,
                role=role,
                department=department,
                join_date=join_date
            )
            
            self.add_status(f"💾 User '{name}' saved to database", "#00ff88")
            
            # Retrain model
            self.add_status("🔄 Retraining recognition model...", "#00e5ff")
            train_recognizer()
            self.add_status("✅ Model trained successfully", "#00ff88")
            
            QMessageBox.information(
                self,
                "Success",
                f"User '{name}' registered successfully!\n\n"
                f"User ID: {user_id}\n"
                f"Samples: {self.max_samples}\n"
                f"Model: Retrained"
            )
            
            self.clear_form()
            self.load_existing_users()
            self.registration_complete.emit(name)
            
        except Exception as e:
            logger.error(f"Save user error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save user:\n{str(e)}")
            self.add_status(f"❌ Error: {str(e)}", "#ff0000")
    
    def clear_form(self):
        """Clear all form fields"""
        self.user_id_input.clear()
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.department_input.setCurrentIndex(0)
        self.role_input.clear()
        
        self.captured_samples = 0
        self.progress_bar.setValue(0)
        self.progress_text.setText(f"0 / {self.max_samples} samples captured")
        self.save_btn.setEnabled(False)
        
        self.status_text.clear()
        self.status_text.setText("ℹ️ Form cleared - Ready for new registration")
        
        self.add_status("🗑️ Form cleared", "#00e5ff")
    
    def load_existing_users(self):
        """Load existing users count"""
        try:
            users = get_all_users()
            count = len(users)
            self.add_status(f"📊 {count} users in database", "#b0b0c0")
        except Exception as e:
            logger.error(f"Load users error: {e}")
    
    def closeEvent(self, event):
        """Clean up on close"""
        self.stop_camera()
        event.accept()
