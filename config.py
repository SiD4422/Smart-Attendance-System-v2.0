# config.py
"""
Configuration management for Smart Attendance System
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FACES_DIR = DATA_DIR / "faces"
MODELS_DIR = DATA_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure directories exist
for directory in [DATA_DIR, FACES_DIR, MODELS_DIR, LOGS_DIR, ASSETS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database settings
DB_PATH = DATA_DIR / "smart_attendance.db"

# Camera settings
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Face recognition settings
FACE_RECOGNITION_MODEL = "LBPH"  # Options: LBPH, DEEPFACE, FACENET
CONFIDENCE_THRESHOLD = 70
MIN_FACE_SIZE = (100, 100)
SAMPLES_PER_USER = 30

# Anti-spoofing settings
ENABLE_ANTI_SPOOF = True
LIVENESS_THRESHOLD = 10  # Laplacian variance threshold
TEXTURE_THRESHOLD = 0.15  # Texture analysis threshold
MOTION_FRAMES = 5  # Frames to analyze for motion
EYE_BLINK_THRESHOLD = 0.25  # Eye aspect ratio threshold

# Security settings
PASSWORD_MIN_LENGTH = 8
SESSION_TIMEOUT = 3600  # seconds (1 hour)
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # seconds (5 minutes)

# UI settings
THEME_FILE = BASE_DIR / "theme_neon.qss"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
SIDEBAR_WIDTH = 260

# Logging settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = LOGS_DIR / "attendance.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Export settings
EXPORT_DIR = DATA_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

# Notification settings
ENABLE_NOTIFICATIONS = False
NOTIFICATION_EMAIL = ""
NOTIFICATION_SMS = ""

# Application metadata
APP_NAME = "Smart Attendance System"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Your Name"

# Development settings
DEBUG_MODE = False
SHOW_FPS = False
SAVE_DETECTION_FRAMES = False
