import cv2
import os
import json
import numpy as np
import pickle
import time
import shutil
import warnings

# Suppress annoying Protobuf and Mediapipe warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')

from sklearn.ensemble import RandomForestClassifier

# Use absolute paths relative to execution
base_dir = os.path.dirname(os.path.abspath(__file__))
# Data/Faces should live at Jarvis root
data_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "Data", "Faces"))
os.makedirs(data_dir, exist_ok=True)

MODEL_PATH = os.path.join(data_dir, "face_model.pkl")
FACE_DB_PATH = os.path.join(data_dir, "FaceDB.json")

def load_face_db():
    if os.path.exists(FACE_DB_PATH):
        try:
            with open(FACE_DB_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_face_db(db):
    list_db = {str(k): v for k, v in db.items()}
    with open(FACE_DB_PATH, "w") as f:
        json.dump(list_db, f, indent=4)

def crop_face_and_embed(bgr_image, detection):
    h, w = bgr_image.shape[:2]
    # Mediapipe detection gives relative bounding box
    bbox = detection.location_data.relative_bounding_box
    x1 = int(max(0, bbox.xmin * w))
    y1 = int(max(0, bbox.ymin * h))
    x2 = int(min(w, (bbox.xmin + bbox.width) * w))
    y2 = int(min(h, (bbox.ymin + bbox.height) * h))
    if x2 <= x1 or y2 <= y1:
        return None, None
    
    face = bgr_image[y1:y2, x1:x2]
    face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    face_resized = cv2.resize(face_gray, (32, 32), interpolation=cv2.INTER_AREA)
    emb = face_resized.flatten().astype(np.float32) / 255.0
    
    # Also return the pixel box (top, right, bottom, left) for Jarvis legacy compatibility
    box = (y1, x2, y2, x1)
    return emb, box

class FaceRecognizer:
    def __init__(self):
        import mediapipe as mp
        self.mp_face = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
        self.model = None
        self.face_db = load_face_db()
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)

    def identify_faces(self, frame):
        """Detects and identifies faces using Mediapipe & Random Forest."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.mp_face.process(rgb)
        
        face_locations = []
        face_names = []
        
        if not results.detections:
            return face_locations, face_names
            
        for detection in results.detections:
            emb, box = crop_face_and_embed(frame, detection)
            if emb is None:
                continue
            
            face_locations.append(box)
            name = "Unknown"
            
            if self.model is not None and len(self.face_db) > 0:
                proba = self.model.predict_proba([emb])[0]
                idx = np.argmax(proba)
                conf = float(proba[idx])
                
                if conf >= 0.5:
                    class_id = str(self.model.classes_[idx])
                    name = self.face_db.get(class_id, "Unknown person")
                
            face_names.append(name)

        return face_locations, face_names

    def enroll_face(self, name, cap):
        """Captures webcam frames to learn a face, updates model and DB, then cleans up images."""
        
        # 1. Update Database ID
        class_id = len(self.face_db) + 1
        self.face_db[str(class_id)] = name
        save_face_db(self.face_db)
        
        # Create user dataset folder
        student_dir = os.path.join(data_dir, str(class_id))
        os.makedirs(student_dir, exist_ok=True)
        
        captured_count = 0
        total_needed = 30
        
        while captured_count < total_needed:
            ret, frame = cap.read()
            if not ret: continue
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = self.mp_face.process(rgb)
            if res.detections:
                path = os.path.join(student_dir, f"{int(time.time() * 1000)}.jpg")
                cv2.imwrite(path, frame)
                captured_count += 1
                time.sleep(0.05) 
        
        cv2.destroyAllWindows()
        
        # 3. Train the model
        X, y = [], []
        student_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
        
        for sid in student_dirs:
            folder = os.path.join(data_dir, sid)
            for fn in os.listdir(folder):
                if fn.endswith((".jpg", ".png")):
                    img = cv2.imread(os.path.join(folder, fn))
                    if img is None: continue
                    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    res = self.mp_face.process(rgb)
                    if res.detections:
                        emb, _ = crop_face_and_embed(img, res.detections[0])
                        if emb is not None:
                            X.append(emb)
                            y.append(int(sid))
                            
        if len(X) > 0:
            X = np.stack(X)
            y = np.array(y)
            clf = RandomForestClassifier(n_estimators=150, n_jobs=-1, random_state=42)
            clf.fit(X, y)
            
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(clf, f)
            
            self.model = clf
            
            # 4. OPTIMIZATION: Delete the images to save space after model is trained
            for sid in student_dirs:
                folder = os.path.join(data_dir, sid)
                try:
                    shutil.rmtree(folder)
                except:
                    pass
                    
            return True
        else:
            return False
