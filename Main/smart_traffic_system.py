import cv2
import numpy as np
import time
import argparse
import os
from vehicle_detector import VehicleDetector
from traffic_lane_manager import TrafficLaneManager
from traffic_signal_controller import TrafficSignalController

class SmartTrafficSystem:
    def __init__(self, video_path=None):
        # Initialize components
        self.vehicle_detector = VehicleDetector()
        self.traffic_signal_controller = TrafficSignalController()
        
        # Video source
        self.video_path = video_path
        self.cap = None
        
        # Frame dimensions
        self.frame_width = 640
        self.frame_height = 480
        
        # Initialize lane manager after getting frame dimensions
        self.lane_manager = None
        
        # Performance metrics
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # GUI elements
        self.window_name = "Smart Traffic Control System"
        
    def initialize_video(self):
        """Initialize video capture"""
        if self.video_path and os.path.exists(self.video_path):
            self.cap = cv2.VideoCapture(self.video_path)
            print(f"Loaded video: {self.video_path}")
        else:
            # Use webcam if no video file provided
            self.cap = cv2.VideoCapture(0)
            print("Using webcam for live traffic monitoring")
        
        if not self.cap.isOpened():
            raise Exception("Could not open video source")
        
        # Get frame dimensions
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Initialize lane manager with actual frame dimensions
        self.lane_manager = TrafficLaneManager(self.frame_width, self.frame_height)
        
        print(f"Frame dimensions: {self.frame_width}x{self.frame_height}")
    
    def draw_info_panel(self, frame):
        """Draw information panel on the frame"""
        # Create semi-transparent overlay for info panel
        overlay = frame.copy()
        panel_height = 120
        cv2.rectangle(overlay, (0, 0), (self.frame_width, panel_height), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        # Title
        cv2.putText(frame, "SMART TRAFFIC CONTROL SYSTEM", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # FPS
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Current active lane
        current_lane_name = self.lane_manager.lanes[self.traffic_signal_controller.current_lane]['name']
        cv2.putText(frame, f"Active Lane: {current_lane_name}", (10, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Countdown timer
        cv2.putText(frame, f"Signal Timer: {self.traffic_signal_controller.countdown}s", 
                   (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Vehicle counts summary
        counts = self.lane_manager.get_all_counts()
        total_vehicles = sum(counts.values())
        cv2.putText(frame, f"Total Vehicles: {total_vehicles}", (300, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Most congested lane
        congested_lanes = self.lane_manager.get_congested_lanes()
        if congested_lanes and congested_lanes[0][1] > 0:
            most_congested_id = congested_lanes[0][0]
            most_congested_name = self.lane_manager.lanes[most_congested_id]['name']
            cv2.putText(frame, f"Most Congested: {most_congested_name}", (300, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 2)
        
        # Instructions
        cv2.putText(frame, "Press 'q' to quit | 'p' to pause", (300, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return frame
    
    def process_frame(self, frame):
        """Process a single frame"""
        # Detect vehicles
        detections = self.vehicle_detector.detect_vehicles(frame)
        
        # Update lane manager with detections
        self.lane_manager.update_vehicle_counts(detections)
        
        # Update traffic signal controller with vehicle counts
        vehicle_counts = self.lane_manager.get_all_counts()
        self.traffic_signal_controller.update_vehicle_counts(vehicle_counts)
        
        # Draw detections on frame
        frame = self.vehicle_detector.draw_detections(frame, detections)
        
        # Draw lane regions
        frame = self.lane_manager.draw_lanes(frame)
        
        # Draw traffic signals
        frame = self.traffic_signal_controller.draw_signals(frame, self.lane_manager)
        
        # Draw info panel
        frame = self.draw_info_panel(frame)
        
        return frame
    
    def calculate_fps(self):
        """Calculate current FPS"""
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            self.fps = self.frame_count / elapsed_time
    
    def run(self):
        """Main execution loop"""
        try:
            # Initialize video capture
            self.initialize_video()
            
            # Start traffic signal controller
            self.traffic_signal_controller.start()
            print("Traffic signal controller started")
            
            # Create window
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.frame_width, self.frame_height + 120)
            
            paused = False
            
            while True:
                if not paused:
                    ret, frame = self.cap.read()
                    if not ret:
                        print("End of video or failed to read frame")
                        break
                    
                    # Process frame
                    processed_frame = self.process_frame(frame)
                    
                    # Calculate FPS
                    self.calculate_fps()
                    
                    # Display frame
                    cv2.imshow(self.window_name, processed_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('p'):
                    paused = not paused
                    print(f"Video {'paused' if paused else 'resumed'}")
                elif key == ord('r'):
                    # Reset video to beginning
                    if self.video_path:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        print("Video reset to beginning")
        
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            # Cleanup
            if self.cap:
                self.cap.release()
            self.traffic_signal_controller.stop()
            cv2.destroyAllWindows()
            print("System shutdown complete")

def main():
    parser = argparse.ArgumentParser(description='Smart Traffic Light Control System')
    parser.add_argument('--video', type=str, help='Path to traffic video file')
    parser.add_argument('--webcam', action='store_true', help='Use webcam instead of video file')
    
    args = parser.parse_args()
    
    # Determine video source
    video_path = None
    if args.webcam:
        video_path = None
    elif args.video:
        video_path = args.video
    else:
        # Default: look for sample video in current directory
        sample_videos = ['traffic.mp4', 'traffic_video.mp4', 'sample_traffic.mp4']
        for video in sample_videos:
            if os.path.exists(video):
                video_path = video
                break
    
    if video_path is None and not args.webcam:
        print("No video file found and webcam not specified.")
        print("Usage:")
        print("  python smart_traffic_system.py --video path/to/video.mp4")
        print("  python smart_traffic_system.py --webcam")
        print("  python smart_traffic_system.py  # Will look for traffic.mp4 in current directory")
        return
    
    # Create and run system
    system = SmartTrafficSystem(video_path)
    system.run()

if __name__ == "__main__":
    main()
