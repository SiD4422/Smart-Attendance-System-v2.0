# recognizer.py
import cv2
import os
import numpy as np
from datetime import datetime

from database import mark_attendance, get_user_id_by_name
from anti_spoof import check_liveness_simple

DATA_DIR = "data/faces"

_recognizer = None
_label_map = None
_last_event = None


def _set_last_event(**kwargs):
    global _last_event
    _last_event = kwargs


def get_last_event():
    return _last_event


def train_recognizer():
    """
    Train LBPH recognizer from images in data/faces.
    Filenames: name_1.jpg, name_2.png, etc.
    """
    global _recognizer, _label_map

    faces = []
    labels = []
    label_map = {}
    current_label = 0

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    for filename in os.listdir(DATA_DIR):
        if not filename.lower().endswith((".jpg", ".png")):
            continue

        path = os.path.join(DATA_DIR, filename)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        name = filename.split("_")[0]

        faces.append(img)
        if name not in label_map:
            label_map[name] = current_label
            current_label += 1
        labels.append(label_map[name])

    if len(faces) == 0:
        print("[Recognizer] No faces in data/faces")
        _recognizer = None
        _label_map = None
        return None, None

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    _recognizer = recognizer
    _label_map = label_map

    print("[Recognizer] Trained with", len(label_map), "users.")
    return recognizer, label_map


def get_model():
    global _recognizer, _label_map
    if _recognizer is None or _label_map is None:
        return train_recognizer()
    return _recognizer, _label_map


def recognize_and_annotate(frame):
    """
    Detect faces, run liveness + recognition, mark attendance, and
    write a structured event into _last_event.
    """
    recognizer, label_map = get_model()
    if recognizer is None:
        return frame

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = cascade.detectMultiScale(gray, 1.3, 5)

    now = datetime.now()
    t_str = now.strftime("%H:%M:%S")
    d_str = now.strftime("%Y-%m-%d")

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]

        # ----- Anti-spoof -----
        live = check_liveness_simple(roi_color, roi_gray)
        if not live:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, "Spoof", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            _set_last_event(
                name=None,
                user_id=None,
                status="Spoof",
                time=t_str,
                date=d_str,
            )
            continue

        # ----- Recognition -----
        label_id, confidence = recognizer.predict(roi_gray)

        if confidence < 75:
            # Map label_id back to name
            name = None
            for n, lid in label_map.items():
                if lid == label_id:
                    name = n
                    break

            if name is None:
                color = (0, 0, 255)
                display = "Unknown"
                status = "Unknown"
                user_id = None
            else:
                user_id = get_user_id_by_name(name)
                if user_id is None:
                    # User recognized but not registered in database
                    color = (255, 165, 0)  # Orange color
                    display = f"{name} (Not Registered)"
                    status = "Not Registered"
                else:
                    status = mark_attendance(user_id, name)
                    color = (0, 255, 0)
                    display = f"{name} ({int(confidence)})"

            _set_last_event(
                name=name,
                user_id=user_id,
                status=status,
                time=t_str,
                date=d_str,
            )
        else:
            color = (0, 0, 255)
            display = "Unknown"
            _set_last_event(
                name=None,
                user_id=None,
                status="Unknown",
                time=t_str,
                date=d_str,
            )

        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            frame,
            display,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

    return frame
