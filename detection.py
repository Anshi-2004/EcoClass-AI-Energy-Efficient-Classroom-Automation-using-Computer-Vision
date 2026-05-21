"""
Detection Module - YOLOv8 Person Detection
============================================
This module handles all computer vision tasks:
- Loading the YOLOv8 model
- Running inference on video frames
- Filtering detections to only the "person" class
- Drawing bounding boxes and returning annotated frames
"""

import cv2
import numpy as np
from ultralytics import YOLO


class PersonDetector:
    """
    A wrapper around YOLOv8 for detecting people in video frames.
    Uses the pre-trained YOLOv8n (nano) model for real-time performance.
    """

    # COCO class index for "person"
    PERSON_CLASS_ID = 0

    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.60):
        """
        Initialize the detector.

        Args:
            model_path: Path to the YOLOv8 weights file.
                        Defaults to 'yolov8n.pt' (auto-downloaded).
            confidence: Minimum confidence threshold for detections.
        """
        self.model = YOLO(model_path)
        self.confidence = confidence
        # Bounding box styling
        self.box_color = (0, 255, 120)       # Green
        self.box_thickness = 2
        self.label_color = (255, 255, 255)   # White text
        self.label_bg = (0, 200, 100)        # Green background for labels

    def detect(self, frame: np.ndarray) -> tuple[np.ndarray, int, list]:
        """
        Run person detection on a single frame.

        Args:
            frame: BGR image (numpy array from OpenCV).

        Returns:
            annotated_frame: Frame with bounding boxes drawn.
            person_count:    Number of people detected.
            boxes:           List of bounding box coordinates [(x1,y1,x2,y2,conf), ...].
        """
        # Run YOLOv8 inference (stream=False for single frame)
        results = self.model(frame, conf=self.confidence, verbose=False)

        person_boxes = []
        person_count = 0

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                # Filter: keep only "person" class
                if cls_id == self.PERSON_CLASS_ID:
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    person_boxes.append((x1, y1, x2, y2, conf))
                    person_count += 1

        # Draw bounding boxes on the frame
        annotated_frame = self._draw_boxes(frame.copy(), person_boxes)

        return annotated_frame, person_count, person_boxes

    def _draw_boxes(self, frame: np.ndarray, boxes: list) -> np.ndarray:
        """
        Draw styled bounding boxes and labels on the frame.

        Args:
            frame: The image to draw on.
            boxes: List of (x1, y1, x2, y2, confidence) tuples.

        Returns:
            Frame with annotations drawn.
        """
        for idx, (x1, y1, x2, y2, conf) in enumerate(boxes, start=1):
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2),
                          self.box_color, self.box_thickness)

            # Prepare label text
            label = f"Person #{idx} ({conf:.0%})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(
                label, font, font_scale, thickness
            )

            # Draw label background
            cv2.rectangle(
                frame,
                (x1, y1 - text_h - 10),
                (x1 + text_w + 6, y1),
                self.label_bg,
                -1,  # Filled rectangle
            )

            # Draw label text
            cv2.putText(
                frame, label,
                (x1 + 3, y1 - 5),
                font, font_scale,
                self.label_color, thickness,
                cv2.LINE_AA,
            )

        return frame
