# 🎯 Smart Attendance System with Anti-Spoofing

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green?style=flat&logo=opencv)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-purple?style=flat)
![SQLite](https://img.shields.io/badge/SQLite-Database-orange?style=flat&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-red?style=flat)

A real-time face recognition attendance system built with Python, featuring a multi-layer anti-spoofing pipeline to prevent fraudulent check-ins. Designed with a neon-themed PyQt5 desktop interface and a structured SQLite backend.

---

## 📸 Screenshots

> *(
> <img width="1919" height="1079" alt="Screenshot 2026-03-30 013124" src="https://github.com/user-attachments/assets/30d9cee3-521b-46fe-acdc-155f62289e0a" />
<img width="1919" height="1079" alt="Screenshot 2026-03-30 013124" src="https://github.com/user-attachments/assets/77f6cdcd-e12f-413d-93d0-ce92adf1e878" />
> <img width="1904" height="1074" alt="Screenshot 2026-03-30 013214" src="https://github.com/user-attachments/assets/7bbb8cac-7181-4180-b2fd-aafffaf5ad99" />
<img width="1919" height="1079" alt="Screenshot 2026-03-30 013134" src="https://github.com/user-attachments/assets/592458b0-ef7d-4eec-8715-119e1d78c652" />

)*

---

## ✨ Features

### 🧠 Face Recognition
- Real-time face detection using OpenCV Haar Cascades
- LBPH (Local Binary Patterns Histograms) recognition algorithm
- Face preprocessing pipeline — histogram equalization + noise reduction
- Confidence scoring for every recognition event

### 🛡️ Multi-Layer Anti-Spoofing
- **Sharpness Analysis** — Laplacian variance detects printed photos
- **Texture Analysis** — Local Binary Pattern (LBP) detects flat surfaces
- **Color Distribution** — HSV analysis detects screen displays
- **Motion Detection** — Frame-difference analysis detects static images
- Passes if at least 2/3 checks succeed — configurable thresholds

### 💾 Database (SQLite)
- Users table with metadata (role, department, email, phone)
- Attendance table with confidence scores + duplicate prevention
- Admin management with password hashing (SHA-256 + salt)
- Session management with timeout and lockout after failed attempts
- Indexed queries for fast lookups
- System logs table for audit trail

### 🖥️ Desktop UI (PyQt5)
- Neon dark theme with custom QSS styling
- Sidebar navigation — Dashboard, Register, Attendance, Records
- Glass-morphism login screen with FaceID option
- Auto-refreshing dashboard with live statistics
- Splash screen on startup

### ⚙️ System
- Centralized config management via `config.py`
- Rotating log files with configurable levels
- SHA-256 + salt password hashing
- SQL injection prevention via parameterized queries
- Account lockout after configurable failed login attempts

---

## 🗂️ Project Structure

```
smart-attendance/
│
├── main.py               # Main application window (PyQt5)
├── login.py              # Login screen with FaceID support
├── register.py           # Face capture & registration
├── recognizer.py         # LBPH recognition engine
├── anti_spoof.py         # Multi-layer liveness detection
├── database.py           # SQLite ORM & all DB operations
├── config.py             # Centralized configuration
├── utils.py              # Helpers — hashing, logging, validation
├── splash_screen.py      # Startup splash screen
├── theme_neon.qss        # PyQt5 neon dark theme
├── requirements.txt      # Python dependencies
│
├── pages/
│   ├── dashboard_page.py # Live stats dashboard
│   ├── register_page.py  # User registration UI
│   ├── attendance_page.py# Camera + marking UI
│   └── records_page.py   # Attendance records viewer
│
├── data/                 # Auto-created at runtime
│   ├── faces/            # Captured face images
│   ├── models/           # Trained LBPH models
│   ├── exports/          # CSV/PDF exports
│   └── smart_attendance.db
│
├── logs/
│   └── attendance.log    # Rotating application logs
│
└── assets/
    └── icons/            # UI icons & background images
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Webcam

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/SiD4422/smart-attendance.git
cd smart-attendance

# 2. Create virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / Mac
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python login.py
```

### Default Login (Development)
```
Username: admin
Password: 1234
```
> ⚠️ Change these before deploying in any real environment.

---

## 🔧 Configuration

All settings are in `config.py`:

```python
# Camera
CAMERA_INDEX = 0          # Change if using external webcam

# Recognition
CONFIDENCE_THRESHOLD = 70  # Lower = stricter matching
SAMPLES_PER_USER = 30      # Face samples captured during registration

# Anti-Spoofing
LIVENESS_THRESHOLD = 10    # Laplacian variance threshold
TEXTURE_THRESHOLD = 0.15   # LBP texture threshold

# Security
MAX_LOGIN_ATTEMPTS = 3     # Before account lockout
SESSION_TIMEOUT = 3600     # Seconds (1 hour)
```

---

## 🧩 How It Works

```
Camera Feed
    │
    ▼
Face Detection (Haar Cascade)
    │
    ▼
Anti-Spoof Check ──── FAIL ──→ Mark as "Spoof", reject
    │
   PASS
    │
    ▼
LBPH Recognition
    │
    ├── confidence < 75 → Identify user
    │       │
    │       ▼
    │   Mark Attendance (SQLite) — blocks duplicates per day
    │
    └── confidence ≥ 75 → "Unknown"
```

---

## 📊 Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.8+ |
| GUI Framework | PyQt5 |
| Computer Vision | OpenCV 4.8 |
| Face Recognition | LBPH (opencv-contrib) |
| Database | SQLite3 |
| Image Processing | NumPy, Pillow |
| Security | SHA-256 + Salt, Session tokens |

---

## 🔐 Security Notes

- Passwords stored as `salt$sha256hash` — never plain text
- All DB queries use parameterized statements (no SQL injection)
- Sessions expire after 1 hour of inactivity
- Account locks for 5 minutes after 3 failed login attempts
- All events written to rotating log files

---

## 📋 Requirements

```
PyQt5==5.15.9
opencv-python==4.8.1.78
opencv-contrib-python==4.8.1.78
numpy==1.24.3
Pillow==10.0.0
```

---

## 🗺️ Roadmap

- [ ] REST API layer (FastAPI) for web integration
- [ ] CSV / PDF export for attendance records
- [ ] Email notifications on attendance events
- [ ] Deep learning recognition (FaceNet / DeepFace)
- [ ] Multi-camera support
- [ ] Mobile companion app

---

## 👨‍💻 Developer

**Siddharth Kumar**  
B.Tech EEE — SRM Institute of Science & Technology  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-siddharth--kumar--eee-blue?style=flat&logo=linkedin)](https://linkedin.com/in/siddharth-kumar-eee)
[![GitHub](https://img.shields.io/badge/GitHub-SiD4422-black?style=flat&logo=github)](https://github.com/SiD4422)

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

> Built with Python, OpenCV, and PyQt5
