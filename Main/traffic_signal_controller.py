import time
import threading
import cv2
from enum import Enum
from collections import deque

class SignalState(Enum):
    RED = "RED"
    YELLOW = "YELLOW" 
    GREEN = "GREEN"

class TrafficSignalController:
    def __init__(self):
        # Four lanes: 0=North, 1=East, 2=South, 3=West
        self.num_lanes = 4
        
        # Signal states for each lane
        self.signals = [SignalState.RED] * self.num_lanes
        
        # Timing parameters (in seconds)
        self.min_green_time = 10  # Minimum green time
        self.max_green_time = 60  # Maximum green time
        self.yellow_time = 3      # Yellow transition time
        self.all_red_time = 2     # All red time between switches
        
        # Current active lane (green signal)
        self.current_lane = 0
        
        # Countdown timer
        self.countdown = self.min_green_time
        self.max_countdown = self.min_green_time
        
        # Signal history for smooth transitions
        self.signal_history = deque(maxlen=100)
        
        # Control thread
        self.control_thread = None
        self.running = False
        self.lock = threading.Lock()
        
        # Vehicle counts from lane manager
        self.vehicle_counts = [0] * self.num_lanes
        
    def update_vehicle_counts(self, counts):
        """Update vehicle counts from lane manager"""
        with self.lock:
            for lane_id in range(self.num_lanes):
                self.vehicle_counts[lane_id] = counts.get(lane_id, 0)
    
    def get_next_lane(self):
        """
        Determine next lane to get green signal based on vehicle density
        """
        # Get vehicle counts for all lanes except current one
        lane_priorities = []
        for lane_id in range(self.num_lanes):
            if lane_id != self.current_lane:
                priority = self.vehicle_counts[lane_id]
                lane_priorities.append((lane_id, priority))
        
        # Sort by vehicle count (highest first)
        lane_priorities.sort(key=lambda x: x[1], reverse=True)
        
        # Return lane with highest vehicle count
        if lane_priorities:
            return lane_priorities[0][0]
        
        # Fallback to next lane in sequence
        return (self.current_lane + 1) % self.num_lanes
    
    def calculate_green_time(self, lane_id):
        """
        Calculate green time based on vehicle density
        """
        vehicle_count = self.vehicle_counts[lane_id]
        
        # Base time + additional time per vehicle
        base_time = self.min_green_time
        additional_time = min(vehicle_count * 2, self.max_green_time - self.min_green_time)
        
        return base_time + additional_time
    
    def switch_signals(self, next_lane):
        """
        Switch traffic signals from current lane to next lane
        """
        # Phase 1: Current lane goes yellow
        self.signals[self.current_lane] = SignalState.YELLOW
        self.countdown = self.yellow_time
        self.max_countdown = self.yellow_time
        
        # Wait for yellow time
        time.sleep(self.yellow_time)
        
        # Phase 2: All lanes red (safety period)
        self.signals = [SignalState.RED] * self.num_lanes
        self.countdown = self.all_red_time
        self.max_countdown = self.all_red_time
        
        # Wait for all red time
        time.sleep(self.all_red_time)
        
        # Phase 3: Next lane goes green
        self.current_lane = next_lane
        self.signals[self.current_lane] = SignalState.GREEN
        
        # Calculate green time based on vehicle density
        green_time = self.calculate_green_time(next_lane)
        self.countdown = green_time
        self.max_countdown = green_time
    
    def control_loop(self):
        """
        Main control loop for traffic signal management
        """
        # Initialize with first lane green
        self.signals[0] = SignalState.GREEN
        self.countdown = self.calculate_green_time(0)
        self.max_countdown = self.countdown
        
        while self.running:
            with self.lock:
                if self.countdown <= 0:
                    # Time to switch signals
                    next_lane = self.get_next_lane()
                    self.switch_signals(next_lane)
                
                # Update countdown
                if self.countdown > 0:
                    self.countdown -= 1
                
                # Record signal state
                self.signal_history.append({
                    'timestamp': time.time(),
                    'current_lane': self.current_lane,
                    'signals': self.signals.copy(),
                    'countdown': self.countdown,
                    'vehicle_counts': self.vehicle_counts.copy()
                })
            
            time.sleep(1)  # Update every second
    
    def start(self):
        """Start the traffic signal controller"""
        if not self.running:
            self.running = True
            self.control_thread = threading.Thread(target=self.control_loop, daemon=True)
            self.control_thread.start()
    
    def stop(self):
        """Stop the traffic signal controller"""
        self.running = False
        if self.control_thread:
            self.control_thread.join()
    
    def get_signal_colors(self):
        """
        Get BGR color values for each lane's signal
        """
        color_map = {
            SignalState.RED: (0, 0, 255),      # Red
            SignalState.YELLOW: (0, 255, 255), # Yellow  
            SignalState.GREEN: (0, 255, 0)    # Green
        }
        
        return [color_map[signal] for signal in self.signals]
    
    def draw_signals(self, frame, lane_manager):
        """
        Draw traffic signals on the frame
        """
        signal_colors = self.get_signal_colors()
        
        for lane_id in range(self.num_lanes):
            lane_info = lane_manager.lanes[lane_id]
            x1, y1, x2, y2 = lane_info['region']
            
            # Signal position (top-right corner of each lane)
            signal_x = x2 - 60
            signal_y = y1 + 10
            
            # Draw signal background
            cv2.rectangle(frame, (signal_x - 5, signal_y - 5), 
                         (signal_x + 55, signal_y + 65), (50, 50, 50), -1)
            
            # Draw three signal lights
            # Red light
            red_color = signal_colors[lane_id] if self.signals[lane_id] == SignalState.RED else (30, 30, 30)
            cv2.circle(frame, (signal_x + 15, signal_y + 15), 8, red_color, -1)
            
            # Yellow light  
            yellow_color = signal_colors[lane_id] if self.signals[lane_id] == SignalState.YELLOW else (30, 30, 30)
            cv2.circle(frame, (signal_x + 15, signal_y + 35), 8, yellow_color, -1)
            
            # Green light
            green_color = signal_colors[lane_id] if self.signals[lane_id] == SignalState.GREEN else (30, 30, 30)
            cv2.circle(frame, (signal_x + 15, signal_y + 55), 8, green_color, -1)
            
            # Draw countdown timer for active lane
            if lane_id == self.current_lane:
                countdown_text = f"{self.countdown}s"
                cv2.putText(frame, countdown_text, (signal_x + 25, signal_y + 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame
