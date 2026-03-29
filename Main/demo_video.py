import cv2
import numpy as np
import os

def create_demo_traffic_video():
    """
    Create a synthetic traffic video for demonstration purposes
    This generates a simple simulation of vehicles moving in different lanes
    """
    
    # Video parameters
    width, height = 640, 480
    fps = 30
    duration = 30  # seconds
    total_frames = fps * duration
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('demo_traffic.mp4', fourcc, fps, (width, height))
    
    # Vehicle objects (simplified rectangles)
    vehicles = []
    
    # Initialize vehicles for each lane
    def add_vehicle(lane, y_pos, speed, size=(40, 20)):
        vehicles.append({
            'lane': lane,
            'x': -size[0] if lane in [1, 3] else np.random.randint(0, width),
            'y': y_pos,
            'speed': speed,
            'size': size,
            'color': (np.random.randint(50, 255), np.random.randint(50, 255), np.random.randint(50, 255))
        })
    
    # Add initial vehicles
    for frame in range(total_frames):
        # Create blank frame
        frame_img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Draw road background
        frame_img[:] = (80, 80, 80)  # Gray road
        
        # Draw lane markings
        # Horizontal lanes (North-South)
        cv2.rectangle(frame_img, (width//3 - 2, 0), (width//3 + 2, height), (255, 255, 255), -1)
        cv2.rectangle(frame_img, (2*width//3 - 2, 0), (2*width//3 + 2, height), (255, 255, 255), -1)
        
        # Vertical lanes (East-West)  
        cv2.rectangle(frame_img, (0, height//3 - 2), (width, height//3 + 2), (255, 255, 255), -1)
        cv2.rectangle(frame_img, (0, 2*height//3 - 2), (width, 2*height//3 + 2), (255, 255, 255), -1)
        
        # Add new vehicles randomly
        if frame % 30 == 0:  # Add vehicle every second
            lane = np.random.randint(0, 4)
            if lane == 0:  # North (going south)
                add_vehicle(lane, height//6, np.random.randint(2, 5))
            elif lane == 1:  # East (going west)
                add_vehicle(lane, height//2, -np.random.randint(2, 5))
            elif lane == 2:  # South (going north)
                add_vehicle(lane, 5*height//6, -np.random.randint(2, 5))
            else:  # West (going east)
                add_vehicle(lane, height//2, np.random.randint(2, 5))
        
        # Update and draw vehicles
        vehicles_to_remove = []
        for i, vehicle in enumerate(vehicles):
            # Update position
            vehicle['x'] += vehicle['speed']
            
            # Remove vehicles that have left the frame
            if (vehicle['speed'] > 0 and vehicle['x'] > width) or \
               (vehicle['speed'] < 0 and vehicle['x'] < -vehicle['size'][0]):
                vehicles_to_remove.append(i)
            else:
                # Draw vehicle
                x, y = int(vehicle['x']), int(vehicle['y'])
                w, h = vehicle['size']
                cv2.rectangle(frame_img, (x, y), (x + w, y + h), vehicle['color'], -1)
                cv2.rectangle(frame_img, (x, y), (x + w, y + h), (0, 0, 0), 2)
        
        # Remove off-screen vehicles
        for i in reversed(vehicles_to_remove):
            vehicles.pop(i)
        
        # Add frame number
        cv2.putText(frame_img, f"Frame: {frame}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Write frame
        out.write(frame_img)
        
        # Progress indicator
        if frame % 30 == 0:
            print(f"Generated frame {frame}/{total_frames}")
    
    # Release video writer
    out.release()
    print(f"Demo video 'demo_traffic.mp4' created successfully!")
    print(f"Duration: {duration} seconds, FPS: {fps}, Total frames: {total_frames}")

if __name__ == "__main__":
    create_demo_traffic_video()
