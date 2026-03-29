# utils.py
"""
Utility functions for Smart Attendance System
"""
import logging
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import numpy as np

from config import LOG_FILE, LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT


# ============================================================
#  LOGGING SETUP
# ============================================================
def setup_logging():
    """Configure logging with rotation"""
    from logging.handlers import RotatingFileHandler
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s')
    )
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


# ============================================================
#  PASSWORD HASHING
# ============================================================
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        salt, pwd_hash = hashed.split('$')
        return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ============================================================
#  SESSION MANAGEMENT
# ============================================================
class SessionManager:
    """Manage user sessions with timeout"""
    
    def __init__(self, timeout: int = 3600):
        self.timeout = timeout
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: str, username: str) -> str:
        """Create new session"""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'user_id': user_id,
            'username': username,
            'created': datetime.now(),
            'last_activity': datetime.now()
        }
        logger.info(f"Session created for user: {username}")
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate and refresh session"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # Check timeout
        if (datetime.now() - session['last_activity']).seconds > self.timeout:
            self.destroy_session(session_id)
            logger.warning(f"Session expired for user: {session['username']}")
            return None
        
        # Refresh activity time
        session['last_activity'] = datetime.now()
        return session
    
    def destroy_session(self, session_id: str):
        """Destroy session"""
        if session_id in self.sessions:
            username = self.sessions[session_id]['username']
            del self.sessions[session_id]
            logger.info(f"Session destroyed for user: {username}")


# ============================================================
#  IMAGE PROCESSING
# ============================================================
def preprocess_face(face_img: np.ndarray, target_size: tuple = (200, 200)) -> np.ndarray:
    """Preprocess face image for recognition"""
    try:
        # Convert to grayscale if needed
        if len(face_img.shape) == 3:
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        
        # Resize
        face_img = cv2.resize(face_img, target_size)
        
        # Histogram equalization for better contrast
        face_img = cv2.equalizeHist(face_img)
        
        # Noise reduction
        face_img = cv2.GaussianBlur(face_img, (5, 5), 0)
        
        return face_img
    except Exception as e:
        logger.error(f"Face preprocessing error: {e}")
        return face_img


def calculate_face_quality(face_img: np.ndarray) -> float:
    """Calculate face quality score (0-1)"""
    try:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY) if len(face_img.shape) == 3 else face_img
        
        # Sharpness (Laplacian variance)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Brightness
        brightness = np.mean(gray)
        brightness_score = 1 - abs(brightness - 127.5) / 127.5
        
        # Contrast
        contrast = gray.std()
        contrast_score = min(contrast / 50, 1.0)
        
        # Combined score
        quality = (
            min(sharpness / 100, 1.0) * 0.5 +
            brightness_score * 0.25 +
            contrast_score * 0.25
        )
        
        return quality
    except Exception as e:
        logger.error(f"Face quality calculation error: {e}")
        return 0.0


def detect_motion(frames: list) -> bool:
    """Detect motion across multiple frames"""
    if len(frames) < 2:
        return False
    
    try:
        motion_detected = False
        for i in range(1, len(frames)):
            diff = cv2.absdiff(frames[i-1], frames[i])
            motion_score = np.mean(diff)
            if motion_score > 10:  # Threshold for motion
                motion_detected = True
                break
        return motion_detected
    except Exception as e:
        logger.error(f"Motion detection error: {e}")
        return False


# ============================================================
#  FILE OPERATIONS
# ============================================================
def save_json(data: dict, filepath: Path):
    """Save data to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {filepath}")
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {e}")


def load_json(filepath: Path) -> Optional[dict]:
    """Load data from JSON file"""
    try:
        if not filepath.exists():
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {filepath}: {e}")
        return None


# ============================================================
#  DATE/TIME UTILITIES
# ============================================================
def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object"""
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse datetime string"""
    try:
        return datetime.strptime(dt_str, format_str)
    except Exception as e:
        logger.error(f"Error parsing datetime: {e}")
        return None


def get_date_range(days: int = 7) -> tuple:
    """Get date range (start_date, end_date)"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


# ============================================================
#  VALIDATION
# ============================================================
def validate_user_id(user_id: str) -> bool:
    """Validate user ID format"""
    return bool(user_id and len(user_id) >= 3 and user_id.isalnum())


def validate_name(name: str) -> bool:
    """Validate name format"""
    return bool(name and len(name) >= 2 and name.replace(" ", "").isalpha())


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# ============================================================
#  ERROR HANDLING
# ============================================================
class AttendanceSystemError(Exception):
    """Base exception for attendance system"""
    pass


class CameraError(AttendanceSystemError):
    """Camera related errors"""
    pass


class RecognitionError(AttendanceSystemError):
    """Face recognition errors"""
    pass


class DatabaseError(AttendanceSystemError):
    """Database related errors"""
    pass


def handle_exception(func):
    """Decorator for exception handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper
