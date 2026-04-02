import cv2
import os
import numpy as np

class ObjectDetector:
    def __init__(self):
        base_dir = r"c:\Users\Ritvik\Favorites\Jarvis\Backend\Vision\Models"
        pb_path = os.path.join(base_dir, "frozen_inference_graph.pb")
        pbtxt_path = os.path.join(base_dir, "model.pbtxt")

        # COCO Labels (Index 1 to 90)
        self.classNames = {
            1: 'person', 2: 'bicycle', 3: 'car', 4: 'motorcycle', 5: 'airplane',
            6: 'bus', 7: 'train', 8: 'truck', 9: 'boat', 10: 'traffic light',
            11: 'fire hydrant', 13: 'stop sign', 14: 'parking meter', 15: 'bench',
            16: 'bird', 17: 'cat', 18: 'dog', 19: 'horse', 20: 'sheep',
            21: 'cow', 22: 'elephant', 23: 'bear', 24: 'zebra', 25: 'giraffe',
            27: 'backpack', 28: 'umbrella', 31: 'handbag', 32: 'tie', 33: 'suitcase',
            34: 'frisbee', 35: 'skis', 36: 'snowboard', 37: 'sports ball', 38: 'kite',
            39: 'baseball bat', 40: 'baseball glove', 41: 'skateboard', 42: 'surfboard',
            43: 'tennis racket', 44: 'bottle', 46: 'wine glass', 47: 'cup', 48: 'fork',
            49: 'knife', 50: 'spoon', 51: 'bowl', 52: 'banana', 53: 'apple',
            54: 'sandwich', 55: 'orange', 56: 'broccoli', 57: 'carrot', 58: 'hot dog',
            59: 'pizza', 60: 'donut', 61: 'cake', 62: 'chair', 63: 'couch',
            64: 'potted plant', 65: 'bed', 67: 'dining table', 70: 'toilet',
            72: 'tv', 73: 'laptop', 74: 'mouse', 75: 'remote', 76: 'keyboard',
            77: 'cell phone', 78: 'microwave', 79: 'oven', 80: 'toaster',
            81: 'sink', 82: 'refrigerator', 84: 'book', 85: 'clock', 86: 'vase',
            87: 'scissors', 88: 'teddy bear', 89: 'hair drier', 90: 'toothbrush'
        }

        try:
            # Use raw cv2.dnn API - the DetectionModel wrapper has a parsing bug with SSD V2
            self.net = cv2.dnn.readNetFromTensorflow(pb_path, pbtxt_path)
            self.is_loaded = True
            print("[Vision] Object Detector loaded successfully (COCO SSD MobileNet V2).")
        except Exception as e:
            print(f"[ERROR] Object Detector could not load models: {e}")
            self.net = None
            self.is_loaded = False

    def detect_objects(self, frame, conf_threshold=0.35):
        """Detect objects using the raw cv2.dnn API for maximum compatibility."""
        detected_names = []
        if not self.is_loaded or self.net is None:
            return frame, detected_names

        h, w = frame.shape[:2]

        # Pre-process: slight brightness/contrast boost for better detection in low light
        frame_processed = cv2.convertScaleAbs(frame, alpha=1.2, beta=15)

        blob = cv2.dnn.blobFromImage(frame_processed, size=(300, 300), swapRB=True)
        self.net.setInput(blob)
        output = self.net.forward()

        for detection in output[0, 0, :, :]:
            conf = float(detection[2])
            if conf < conf_threshold:
                continue

            class_id = int(detection[1])
            if class_id not in self.classNames:
                continue

            name = self.classNames[class_id]
            detected_names.append(name.title())

            # Scale bounding box back to the original frame dimensions
            x1 = int(detection[3] * w)
            y1 = int(detection[4] * h)
            x2 = int(detection[5] * w)
            y2 = int(detection[6] * h)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 50), 2)
            label = f"{name.upper()} {conf:.0%}"
            cv2.putText(frame, label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 220, 50), 1)

        return frame, list(set(detected_names))
