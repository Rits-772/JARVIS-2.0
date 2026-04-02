import cv2
import time
import threading
from Backend.Vision.FaceRecognition import FaceRecognizer
from Backend.Vision.ObjectDetection import ObjectDetector

class VisualEngine:
    def __init__(self):
        self.face_recognizer = None
        self.object_detector = None
        self.is_active = False
        self.cap = None

    def initialize_models(self):
        """Pre-loads stable OpenCV models so they are ready instantly."""
        try:
            if not self.face_recognizer:
                self.face_recognizer = FaceRecognizer()
            if not self.object_detector:
                self.object_detector = ObjectDetector()
        except Exception as e:
            print(f"[ERROR] Jarvis Visual System Error (Models): {e}")

    def warm_up_camera(self):
        """
        Starts the camera stream in the background to eliminate the 2-3 sec
        hardware startup delay. Also initializes the models.
        """
        self.initialize_models()
        if self.cap is None:
            # Setting cv2.CAP_DSHOW can sometimes speed up camera initialization on Windows
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback to default backend
                self.cap = cv2.VideoCapture(0)

    def scan(self, duration=10, mode="both"):
        """
        Runs the pre-warmed camera for a set duration for visual detection.
        Returns a summary of what was seen.
        """
        self.warm_up_camera()
        self.is_active = True
        
        start_time = time.time()
        final_summary = {"faces": set(), "objects": set()}

        while self.is_active and (time.time() - start_time < duration):
            ret, frame = self.cap.read()
            if not ret:
                break

            # 1. Run Face Detection
            if mode in ["face", "both"] and self.face_recognizer:
                locations, names = self.face_recognizer.identify_faces(frame)
                for name in names:
                    final_summary["faces"].add(name)
                
                # Draw boxes for faces
                for (top, right, bottom, left), name in zip(locations, names):
                    cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 255), 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

            # 2. Run Object Detection
            if mode in ["object", "both"] and self.object_detector:
                frame, detected_objects = self.object_detector.detect_objects(frame)
                for obj in detected_objects:
                    final_summary["objects"].add(obj)

            cv2.imshow("Jarvis Visual Feed", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.is_active = False
        # Destroy window, but KEEP self.cap open to eliminate future delays
        cv2.destroyAllWindows()
        
        return self.format_summary(final_summary)

    def enroll_face(self, name):
        """Delegates face enrollment using the pre-warmed camera feed."""
        self.warm_up_camera()
        self.is_active = True
        if self.face_recognizer:
            success = self.face_recognizer.enroll_face(name, self.cap)
            self.is_active = False
            return success
        self.is_active = False
        return False

    def format_summary(self, summary):
        """Converts the results into a natural, witty report."""
        if not summary["faces"] and not summary["objects"]:
            return "I've scanned the environment, sir. No biological signatures or significant objects detected at this time."

        report = "Visual scan complete, sir. "
        
        if summary["faces"]:
            known_faces = [f for f in summary["faces"] if f not in ["Unknown", "Person Detected"]]
            if known_faces:
                report += f"I've recognized you, Sir. "
            else:
                report += f"I've identified {len(summary['faces'])} unidentified biological signature(s). "

        if summary["objects"]:
            objs = list(summary["objects"])
            report += f"I have also cataloged: {', '.join(objs)}."

        return report

# Singleton instance
JarvisEyes = VisualEngine()
