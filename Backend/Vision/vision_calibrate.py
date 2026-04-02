import cv2
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from Backend.Vision.ObjectDetection import ObjectDetector

def calibrate_vision():
    print("[System] Initializing calibration...")
    detector = ObjectDetector()
    if not detector.is_loaded:
        print("[Error] Detector not loaded. Check model files.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not open camera.")
        return

    # Let the camera warm up/adjust exposure
    time.sleep(2)
    
    frames = []
    print("[System] Capturing 5 calibration frames...")
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
        time.sleep(0.5)
    
    cap.release()

    if not frames:
        print("[Error] No frames captured.")
        return

    # Analyze detection at different thresholds
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    best_threshold = 0.55 # Default
    max_detections = 0
    consistent_objects = {}

    print("\n[Analysis Results]")
    for thresh in thresholds:
        total_detections = 0
        for i, frame in enumerate(frames):
            # Use the detector's own detection method
            _, detected_names = detector.detect_objects(frame, conf_threshold=thresh)
            total_detections += len(detected_names)
            
            for name in detected_names:
                consistent_objects[name] = consistent_objects.get(name, 0) + 1

        avg = total_detections / 5
        print(f"Threshold {thresh:.1f}: Avg {avg:.1f} detections")
        
        # We want a threshold that sees something but isn't pure noise
        # Usually, if avg > 0.5 and thresh is reasonably high, it's good.
        if avg >= 1.0 and thresh >= 0.2:
            best_threshold = thresh

    print(f"\n[Recommendation] Optimal Confidence Threshold: {best_threshold}")
    print("[Note] This value will be applied to ObjectDetection.py")

if __name__ == "__main__":
    calibrate_vision()
