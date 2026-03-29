# ⚡ Quick Setup Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Run the App

```bash
python login.py
```

Default credentials: `admin` / `1234`

---

## 3. Register a New User

1. Log in → click **Register User** in the sidebar
2. Enter a name and User ID
3. Look at the camera — it captures 30 face samples automatically
4. Click **Train Model** once registration is done

## 4. Mark Attendance

1. Click **Start Attendance** in the sidebar
2. Look at the camera
3. The system runs anti-spoof checks → recognizes your face → logs attendance
4. Each person can only be marked once per day

---

## 5. Common Issues

| Problem | Fix |
|---|---|
| Camera not opening | Change `CAMERA_INDEX = 1` in `config.py` |
| Low accuracy | Increase `SAMPLES_PER_USER = 50` in `config.py` |
| Always shows "Unknown" | Lower `CONFIDENCE_THRESHOLD = 60` in `config.py` |
| Always shows "Spoof" | Lower `LIVENESS_THRESHOLD = 5` in `config.py` |
| DB locked error | Restart the app; only one instance should run |

---

## 6. Folder Structure Created Automatically

When you run the app, these folders are created automatically:

```
data/faces/      ← face images saved here during registration
data/models/     ← trained LBPH model saved here
logs/            ← rotating application logs
```

You do **not** need to create these manually.
