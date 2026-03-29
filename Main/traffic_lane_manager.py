import cv2
import numpy as np
from collections import defaultdict, deque

class TrafficLaneManager:
    def __init__(self, frame_width, frame_height):
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Define four lanes for four-way intersection
        # Lane 0: North (top)
        # Lane 1: East (right)  
        # Lane 2: South (bottom)
        # Lane 3: West (left)
        
        self.lanes = {
            0: {  # North lane - vehicles coming from top
                'name': 'North',
                'region': (frame_width//3, 0, 2*frame_width//3, frame_height//3),
                'direction': 'south',
                'color': (255, 0, 0)  # Red
            },
            1: {  # East lane - vehicles coming from right
                'name': 'East', 
                'region': (2*frame_width//3, frame_height//3, frame_width, 2*frame_height//3),
                'direction': 'west',
                'color': (0, 255, 0)  # Green
            },
            2: {  # South lane - vehicles coming from bottom
                'name': 'South',
                'region': (frame_width//3, 2*frame_height//3, 2*frame_width//3, frame_height),
                'direction': 'north', 
                'color': (0, 0, 255)  # Blue
            },
            3: {  # West lane - vehicles coming from left
                'name': 'West',
                'region': (0, frame_height//3, frame_width//3, 2*frame_height//3),
                'direction': 'east',
                'color': (255, 255, 0)  # Yellow
            }
        }
        
        # Vehicle tracking for each lane
        self.vehicle_counts = defaultdict(int)
        self.vehicle_history = defaultdict(lambda: deque(maxlen=30))  # Last 30 frames
        
        # Tracking IDs to avoid double counting
        self.tracked_vehicles = {}
        self.next_id = 0
        
    def get_lane_for_vehicle(self, vehicle_center):
        """
        Determine which lane a vehicle belongs to based on its center position
        """
        x, y = vehicle_center
        
        for lane_id, lane_info in self.lanes.items():
            x1, y1, x2, y2 = lane_info['region']
            if x1 <= x <= x2 and y1 <= y <= y2:
                return lane_id
        
        return None
    
    def update_vehicle_counts(self, detections):
        """
        Update vehicle counts for each lane based on current detections
        """
        # Reset current counts
        current_counts = defaultdict(int)
        
        # Count vehicles in each lane
        for detection in detections:
            lane_id = self.get_lane_for_vehicle(detection['center'])
            if lane_id is not None:
                current_counts[lane_id] += 1
        
        # Update history and current counts
        for lane_id in range(4):
            self.vehicle_history[lane_id].append(current_counts[lane_id])
            # Use average of last 10 frames for stability
            if len(self.vehicle_history[lane_id]) > 0:
                self.vehicle_counts[lane_id] = int(np.mean(list(self.vehicle_history[lane_id])[-10:]))
            else:
                self.vehicle_counts[lane_id] = 0
    
    def get_vehicle_count(self, lane_id):
        """Get current vehicle count for a specific lane"""
        return self.vehicle_counts.get(lane_id, 0)
    
    def get_all_counts(self):
        """Get vehicle counts for all lanes"""
        return {lane_id: self.get_vehicle_count(lane_id) for lane_id in range(4)}
    
    def draw_lanes(self, frame):
        """
        Draw lane regions on frame
        """
        overlay = frame.copy()
        
        for lane_id, lane_info in self.lanes.items():
            x1, y1, x2, y2 = lane_info['region']
            color = lane_info['color']
            
            # Draw semi-transparent lane region
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            
            # Draw lane border
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw lane name and vehicle count
            count = self.get_vehicle_count(lane_id)
            text = f"{lane_info['name']}: {count} vehicles"
            cv2.putText(frame, text, (x1 + 10, y1 + 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Blend overlay with original frame
        alpha = 0.2
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        return frame
    
    def get_congested_lanes(self):
        """
        Get lanes sorted by vehicle count (most congested first)
        """
        counts = self.get_all_counts()
        sorted_lanes = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_lanes
