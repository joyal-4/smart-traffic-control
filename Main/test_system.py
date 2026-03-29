import cv2
import numpy as np
import time
import random
from traffic_lane_manager import TrafficLaneManager
from traffic_signal_controller import TrafficSignalController

class TestTrafficSystem:
    def __init__(self):
        # Frame dimensions
        self.frame_width = 640
        self.frame_height = 480
        
        # Initialize components
        self.lane_manager = TrafficLaneManager(self.frame_width, self.frame_height)
        self.traffic_signal_controller = TrafficSignalController()
        
        # Start traffic signal controller
        self.traffic_signal_controller.start()
        
        # Window
        self.window_name = "Test Traffic Control System"
        
    def create_test_frame(self):
        """Create a test frame with simulated vehicles"""
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        frame[:] = (80, 80, 80)  # Gray road background
        
        # Draw lane markings
        cv2.rectangle(frame, (self.frame_width//3 - 2, 0), (self.frame_width//3 + 2, self.frame_height), (255, 255, 255), -1)
        cv2.rectangle(frame, (2*self.frame_width//3 - 2, 0), (2*self.frame_width//3 + 2, self.frame_height), (255, 255, 255), -1)
        cv2.rectangle(frame, (0, self.frame_height//3 - 2), (self.frame_width, self.frame_height//3 + 2), (255, 255, 255), -1)
        cv2.rectangle(frame, (0, 2*self.frame_height//3 - 2), (self.frame_width, 2*self.frame_height//3 + 2), (255, 255, 255), -1)
        
        # Simulate random vehicle detections
        detections = []
        for lane_id in range(4):
            # Random number of vehicles per lane
            num_vehicles = random.randint(0, 5)
            for i in range(num_vehicles):
                # Random position within lane
                lane_info = self.lane_manager.lanes[lane_id]
                x1, y1, x2, y2 = lane_info['region']
                
                # Random vehicle position
                vx = random.randint(x1 + 10, x2 - 50)
                vy = random.randint(y1 + 10, y2 - 30)
                
                detections.append({
                    'bbox': (vx, vy, vx + 40, vy + 20),
                    'class': 'car',
                    'confidence': 0.8,
                    'center': (vx + 20, vy + 10)
                })
        
        return frame, detections
    
    def draw_detections(self, frame, detections):
        """Draw simulated vehicle detections"""
        for detection in detections:
            bbox = detection['bbox']
            vehicle_type = detection['class']
            confidence = detection['confidence']
            color = (0, 255, 0)  # Green for cars
            
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
    
    def draw_info_panel(self, frame):
        """Draw information panel"""
        overlay = frame.copy()
        panel_height = 120
        cv2.rectangle(overlay, (0, 0), (self.frame_width, panel_height), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        # Title
        cv2.putText(frame, "TEST TRAFFIC CONTROL SYSTEM", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # Current active lane
        current_lane_name = self.lane_manager.lanes[self.traffic_signal_controller.current_lane]['name']
        cv2.putText(frame, f"Active Lane: {current_lane_name}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Countdown timer
        cv2.putText(frame, f"Signal Timer: {self.traffic_signal_controller.countdown}s", 
                   (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Vehicle counts summary
        counts = self.lane_manager.get_all_counts()
        total_vehicles = sum(counts.values())
        cv2.putText(frame, f"Total Vehicles: {total_vehicles}", (300, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Instructions
        cv2.putText(frame, "Press 'q' to quit", (300, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return frame
    
    def run(self):
        """Run the test system"""
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.frame_width, self.frame_height + 120)
            
            frame_count = 0
            
            while True:
                # Create test frame with simulated vehicles
                frame, detections = self.create_test_frame()
                
                # Update lane manager with detections
                self.lane_manager.update_vehicle_counts(detections)
                
                # Update traffic signal controller with vehicle counts
                vehicle_counts = self.lane_manager.get_all_counts()
                self.traffic_signal_controller.update_vehicle_counts(vehicle_counts)
                
                # Draw detections
                frame = self.draw_detections(frame, detections)
                
                # Draw lane regions
                frame = self.lane_manager.draw_lanes(frame)
                
                # Draw traffic signals
                frame = self.traffic_signal_controller.draw_signals(frame, self.lane_manager)
                
                # Draw info panel
                frame = self.draw_info_panel(frame)
                
                # Display frame
                cv2.imshow(self.window_name, frame)
                
                # Handle keyboard input
                key = cv2.waitKey(100) & 0xFF  # 100ms delay
                if key == ord('q'):
                    break
                
                frame_count += 1
                if frame_count % 10 == 0:
                    print(f"Frame {frame_count}: Active lane = {self.lane_manager.lanes[self.traffic_signal_controller.current_lane]['name']}, Timer = {self.traffic_signal_controller.countdown}s")
        
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            # Cleanup
            self.traffic_signal_controller.stop()
            cv2.destroyAllWindows()
            print("Test system shutdown complete")

if __name__ == "__main__":
    system = TestTrafficSystem()
    system.run()
