# anti_spoof.py
"""
Advanced anti-spoofing module with multiple liveness checks
"""
import cv2
import numpy as np
from typing import Tuple, List, Optional
import logging

from config import (
    LIVENESS_THRESHOLD, TEXTURE_THRESHOLD,
    MOTION_FRAMES, EYE_BLINK_THRESHOLD
)

logger = logging.getLogger(__name__)


# ============================================================
#  SHARPNESS-BASED DETECTION
# ============================================================
def check_sharpness(roi_gray: np.ndarray, threshold: float = LIVENESS_THRESHOLD) -> Tuple[bool, float]:
    """
    Check image sharpness using Laplacian variance.
    Low sharpness indicates printed photo or screen display.
    
    Returns:
        (is_live, sharpness_score)
    """
    if roi_gray is None or roi_gray.size == 0:
        return False, 0.0
    
    try:
        laplacian_var = cv2.Laplacian(roi_gray, cv2.CV_64F).var()
        is_live = laplacian_var >= threshold
        return is_live, laplacian_var
    except Exception as e:
        logger.error(f"Sharpness check error: {e}")
        return False, 0.0


# ============================================================
#  TEXTURE ANALYSIS
# ============================================================
def check_texture(roi_gray: np.ndarray) -> Tuple[bool, float]:
    """
    Analyze texture patterns to detect printed photos.
    Real faces have different texture than printed images.
    
    Returns:
        (is_live, texture_score)
    """
    if roi_gray is None or roi_gray.size == 0:
        return False, 0.0
    
    try:
        # Local Binary Pattern (LBP) for texture analysis
        lbp = np.zeros_like(roi_gray)
        
        for i in range(1, roi_gray.shape[0] - 1):
            for j in range(1, roi_gray.shape[1] - 1):
                center = roi_gray[i, j]
                binary_string = ""
                
                # 8 neighbors
                neighbors = [
                    roi_gray[i-1, j-1], roi_gray[i-1, j], roi_gray[i-1, j+1],
                    roi_gray[i, j+1], roi_gray[i+1, j+1], roi_gray[i+1, j],
                    roi_gray[i+1, j-1], roi_gray[i, j-1]
                ]
                
                for neighbor in neighbors:
                    binary_string += "1" if neighbor >= center else "0"
                
                lbp[i, j] = int(binary_string, 2)
        
        # Calculate texture score based on LBP variance
        texture_score = np.std(lbp) / 100.0
        is_live = texture_score >= TEXTURE_THRESHOLD
        
        return is_live, texture_score
    except Exception as e:
        logger.error(f"Texture analysis error: {e}")
        return False, 0.0


# ============================================================
#  COLOR ANALYSIS
# ============================================================
def check_color_distribution(roi_color: np.ndarray) -> Tuple[bool, float]:
    """
    Analyze color distribution to detect screen displays.
    Screen displays have different color characteristics.
    
    Returns:
        (is_live, color_score)
    """
    if roi_color is None or roi_color.size == 0:
        return False, 0.0
    
    try:
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(roi_color, cv2.COLOR_BGR2HSV)
        
        # Calculate color diversity
        h_std = np.std(hsv[:, :, 0])
        s_std = np.std(hsv[:, :, 1])
        v_std = np.std(hsv[:, :, 2])
        
        color_diversity = (h_std + s_std + v_std) / 3
        
        # Real faces have moderate color diversity
        color_score = min(color_diversity / 50.0, 1.0)
        is_live = color_score >= 0.3
        
        return is_live, color_score
    except Exception as e:
        logger.error(f"Color distribution check error: {e}")
        return False, 0.0


# ============================================================
#  MOTION DETECTION
# ============================================================
class MotionDetector:
    """Detect motion across multiple frames for liveness"""
    
    def __init__(self, frame_buffer_size: int = MOTION_FRAMES):
        self.frame_buffer: List[np.ndarray] = []
        self.buffer_size = frame_buffer_size
    
    def add_frame(self, frame: np.ndarray):
        """Add frame to buffer"""
        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        self.frame_buffer.append(frame)
        
        if len(self.frame_buffer) > self.buffer_size:
            self.frame_buffer.pop(0)
    
    def check_motion(self) -> Tuple[bool, float]:
        """
        Check if there's natural motion in frames.
        Real people have subtle movements (micro-expressions, slight head motion).
        
        Returns:
            (has_motion, motion_score)
        """
        if len(self.frame_buffer) < 2:
            return False, 0.0
        
        try:
            motion_scores = []
            
            for i in range(1, len(self.frame_buffer)):
                # Calculate frame difference
                diff = cv2.absdiff(self.frame_buffer[i-1], self.frame_buffer[i])
                motion_score = np.mean(diff)
                motion_scores.append(motion_score)
            
            avg_motion = np.mean(motion_scores)
            
            # Real faces have motion between 5-50 (subtle movements)
            has_motion = 5 <= avg_motion <= 50
            
            return has_motion, avg_motion
        except Exception as e:
            logger.error(f"Motion detection error: {e}")
            return False, 0.0
    
    def reset(self):
        """Reset frame buffer"""
        self.frame_buffer.clear()


# ============================================================
#  EYE BLINK DETECTION (Optional - requires dlib)
# ============================================================
def calculate_eye_aspect_ratio(eye_points: np.ndarray) -> float:
    """
    Calculate Eye Aspect Ratio (EAR) for blink detection.
    Requires facial landmarks from dlib or mediapipe.
    """
    try:
        # Vertical eye distances
        A = np.linalg.norm(eye_points[1] - eye_points[5])
        B = np.linalg.norm(eye_points[2] - eye_points[4])
        
        # Horizontal eye distance
        C = np.linalg.norm(eye_points[0] - eye_points[3])
        
        # EAR formula
        ear = (A + B) / (2.0 * C)
        return ear
    except Exception as e:
        logger.error(f"EAR calculation error: {e}")
        return 0.0


class BlinkDetector:
    """Detect eye blinks for advanced liveness"""
    
    def __init__(self, threshold: float = EYE_BLINK_THRESHOLD):
        self.threshold = threshold
        self.blink_count = 0
        self.ear_history: List[float] = []
        self.consecutive_closed = 0
    
    def process_ear(self, ear: float) -> bool:
        """
        Process Eye Aspect Ratio to detect blinks.
        
        Returns:
            True if blink detected
        """
        self.ear_history.append(ear)
        if len(self.ear_history) > 20:
            self.ear_history.pop(0)
        
        # Eye is closed
        if ear < self.threshold:
            self.consecutive_closed += 1
        else:
            # Eye opened after being closed = blink
            if self.consecutive_closed >= 2:
                self.blink_count += 1
                self.consecutive_closed = 0
                return True
            self.consecutive_closed = 0
        
        return False
    
    def has_blinked(self) -> bool:
        """Check if any blinks were detected"""
        return self.blink_count > 0
    
    def reset(self):
        """Reset blink detector"""
        self.blink_count = 0
        self.ear_history.clear()
        self.consecutive_closed = 0


# ============================================================
#  COMPREHENSIVE LIVENESS CHECK
# ============================================================
def check_liveness_comprehensive(
    roi_color: np.ndarray,
    roi_gray: np.ndarray,
    motion_detector: Optional[MotionDetector] = None
) -> Tuple[bool, dict]:
    """
    Comprehensive liveness detection combining multiple methods.
    
    Args:
        roi_color: Color face ROI
        roi_gray: Grayscale face ROI
        motion_detector: Optional motion detector instance
    
    Returns:
        (is_live, details_dict)
    """
    details = {
        'sharpness': {'passed': False, 'score': 0.0},
        'texture': {'passed': False, 'score': 0.0},
        'color': {'passed': False, 'score': 0.0},
        'motion': {'passed': False, 'score': 0.0}
    }
    
    # Sharpness check
    sharp_pass, sharp_score = check_sharpness(roi_gray)
    details['sharpness'] = {'passed': sharp_pass, 'score': sharp_score}
    
    # Texture check
    texture_pass, texture_score = check_texture(roi_gray)
    details['texture'] = {'passed': texture_pass, 'score': texture_score}
    
    # Color check
    color_pass, color_score = check_color_distribution(roi_color)
    details['color'] = {'passed': color_pass, 'score': color_score}
    
    # Motion check
    if motion_detector:
        motion_pass, motion_score = motion_detector.check_motion()
        details['motion'] = {'passed': motion_pass, 'score': motion_score}
    
    # Decision: Pass if at least 2 out of 3 checks pass (excluding motion which needs time)
    checks_passed = sum([
        sharp_pass,
        texture_pass,
        color_pass
    ])
    
    is_live = checks_passed >= 2
    
    logger.debug(f"Liveness check: {checks_passed}/3 passed, Final: {is_live}")
    
    return is_live, details


# ============================================================
#  SIMPLE LIVENESS (BACKWARD COMPATIBLE)
# ============================================================
def check_liveness_simple(roi_color: np.ndarray, roi_gray: np.ndarray) -> bool:
    """
    Simple liveness check - backward compatible with original.
    Only blocks extremely flat / low-detail cases.
    """
    is_live, _ = check_sharpness(roi_gray, threshold=5)
    return is_live
