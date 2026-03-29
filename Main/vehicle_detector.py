import cv2
import numpy as np
from ultralytics import YOLO
import torch

class VehicleDetector:
    def __init__(self):
        # Load YOLO model
        self.model = YOLO('yolov8n.pt')  # Using YOLOv8 nano for faster inference
        
        # Vehicle classes in COCO dataset
        self.vehicle_classes = {
            2: 'car',
            3: 'motorcycle', 
            5: 'bus',
            7: 'truck'
        }
        
        # Detection confidence threshold
        self.confidence_threshold = 0.5
        
        # Colors for bounding boxes (BGR format)
        self.colors = {
            'car': (0, 255, 0),
            'motorcycle': (255, 0, 0),
            'bus': (0, 0, 255),
            'truck': (255, 255, 0)
        }
    
    def detect_vehicles(self, frame):
        """
        Detect vehicles in a frame using YOLO
        Returns: detections list with (bbox, class, confidence)
        """
        results = self.model(frame, conf=self.confidence_threshold)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bbox coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Check if it's a vehicle
                    if class_id in self.vehicle_classes:
                        vehicle_type = self.vehicle_classes[class_id]
                        detections.append({
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'class': vehicle_type,
                            'confidence': float(confidence),
                            'center': (int((x1 + x2) / 2), int((y1 + y2) / 2))
                        })
        
        return detections
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels on frame
        """
        for detection in detections:
            bbox = detection['bbox']
            vehicle_type = detection['class']
            confidence = detection['confidence']
            color = self.colors.get(vehicle_type, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # Draw label
            label = f"{vehicle_type}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame, (bbox[0], bbox[1] - label_size[1] - 10), 
                         (bbox[0] + label_size[0], bbox[1]), color, -1)
            cv2.putText(frame, label, (bbox[0], bbox[1] - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Draw center point
            center = detection['center']
            cv2.circle(frame, center, 3, color, -1)
        
        return frame
