# register.py
import cv2
import os

DATA_DIR = "data/faces"


def register_face(username, num_samples=20):
    os.makedirs(DATA_DIR, exist_ok=True)

    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    count = 0
    print(f"Registering face for: {username}")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_roi = gray[y:y + h, x:x + w]
            face_roi = cv2.resize(face_roi, (200, 200))

            count += 1
            filename = os.path.join(DATA_DIR, f"{username}_{count}.jpg")
            cv2.imwrite(filename, face_roi)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"{count}/{num_samples}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

        cv2.imshow("Register Face — ESC to stop", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            print("Registration cancelled.")
            break

        if count >= num_samples:
            print("Registration complete.")
            break

    cam.release()
    cv2.destroyAllWindows()
