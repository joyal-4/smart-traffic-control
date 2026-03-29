import cv2
import numpy as np
import random
import os

def create_lane_video(lane_name, output_path, duration=30, fps=30):
    """Create a sample traffic video for a specific lane"""
    
    width, height = 640, 480
    total_frames = duration * fps
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Lane-specific configurations
    lane_configs = {
        'north': {
            'bg_color': (40, 40, 60),  # Dark blue-gray
            'vehicle_color': (0, 100, 200),  # Blue vehicles
            'traffic_flow': 'south',  # Vehicles moving down
            'vehicle_density': 0.7,  # High density
            'text_color': (200, 200, 255)
        },
        'east': {
            'bg_color': (60, 40, 40),  # Dark red-gray
            'vehicle_color': (0, 200, 100),  # Green vehicles
            'traffic_flow': 'west',  # Vehicles moving left
            'vehicle_density': 0.4,  # Medium density
            'text_color': (255, 200, 200)
        },
        'south': {
            'bg_color': (40, 60, 40),  # Dark green-gray
            'vehicle_color': (200, 100, 0),  # Orange vehicles
            'traffic_flow': 'north',  # Vehicles moving up
            'vehicle_density': 0.5,  # Medium density
            'text_color': (200, 255, 200)
        },
        'west': {
            'bg_color': (60, 60, 40),  # Dark yellow-gray
            'vehicle_color': (200, 0, 100),  # Purple vehicles
            'traffic_flow': 'east',  # Vehicles moving right
            'vehicle_density': 0.3,  # Low density
            'text_color': (255, 255, 200)
        }
    }
    
    config = lane_configs[lane_name]
    vehicles = []
    
    print(f"Creating {lane_name} lane video: {output_path}")
    
    for frame_num in range(total_frames):
        # Create background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = config['bg_color']
        
        # Draw road markings
        draw_road_markings(frame, lane_name)
        
        # Add new vehicles randomly based on density
        if random.random() < config['vehicle_density'] / 10:
            add_vehicle(vehicles, lane_name, config)
        
        # Update and draw vehicles
        vehicles_to_remove = []
        for i, vehicle in enumerate(vehicles):
            # Update position based on traffic flow
            if config['traffic_flow'] == 'south':
                vehicle['y'] += vehicle['speed']
            elif config['traffic_flow'] == 'north':
                vehicle['y'] -= vehicle['speed']
            elif config['traffic_flow'] == 'west':
                vehicle['x'] -= vehicle['speed']
            elif config['traffic_flow'] == 'east':
                vehicle['x'] += vehicle['speed']
            
            # Remove vehicles that have left the frame
            if (vehicle['x'] < -50 or vehicle['x'] > width + 50 or 
                vehicle['y'] < -50 or vehicle['y'] > height + 50):
                vehicles_to_remove.append(i)
            else:
                # Draw vehicle
                draw_vehicle(frame, vehicle, config['vehicle_color'])
        
        # Remove off-screen vehicles
        for i in reversed(vehicles_to_remove):
            vehicles.pop(i)
        
        # Draw lane information
        draw_lane_info(frame, lane_name, len(vehicles), frame_num, config['text_color'])
        
        # Add some traffic lights for realism
        if frame_num % 60 == 0:  # Change lights every 2 seconds
            draw_traffic_lights(frame, lane_name, frame_num // 60)
        
        # Write frame
        out.write(frame)
        
        # Progress indicator
        if frame_num % 30 == 0:
            print(f"  Frame {frame_num}/{total_frames} - Vehicles: {len(vehicles)}")
    
    # Release video writer
    out.release()
    print(f"✅ {lane_name} video completed: {output_path}")

def draw_road_markings(frame, lane_name):
    """Draw road markings for the lane"""
    h, w = frame.shape[:2]
    
    # Draw lane lines
    if lane_name in ['north', 'south']:
        # Vertical road
        cv2.line(frame, (w//3, 0), (w//3, h), (255, 255, 255), 2)
        cv2.line(frame, (2*w//3, 0), (2*w//3, h), (255, 255, 255), 2)
        
        # Center dashed line
        for y in range(0, h, 40):
            cv2.line(frame, (w//2, y), (w//2, min(y + 20, h)), (255, 255, 0), 2)
    else:
        # Horizontal road
        cv2.line(frame, (0, h//3), (w, h//3), (255, 255, 255), 2)
        cv2.line(frame, (0, 2*h//3), (w, 2*h//3), (255, 255, 255), 2)
        
        # Center dashed line
        for x in range(0, w, 40):
            cv2.line(frame, (x, h//2), (min(x + 20, w), h//2), (255, 255, 0), 2)

def add_vehicle(vehicles, lane_name, config):
    """Add a new vehicle to the lane"""
    w, h = 640, 480
    
    # Random vehicle size
    vehicle_types = [
        {'width': 40, 'height': 20, 'speed': 3},  # Car
        {'width': 50, 'height': 25, 'speed': 2},  # Truck
        {'width': 30, 'height': 15, 'speed': 4},  # Motorcycle
        {'width': 60, 'height': 25, 'speed': 2},  # Bus
    ]
    
    vehicle_type = random.choice(vehicle_types)
    
    # Set initial position based on traffic flow
    if config['traffic_flow'] == 'south':
        x = random.randint(w//3 + 20, 2*w//3 - 60)
        y = -vehicle_type['height']
    elif config['traffic_flow'] == 'north':
        x = random.randint(w//3 + 20, 2*w//3 - 60)
        y = h
    elif config['traffic_flow'] == 'west':
        x = w
        y = random.randint(h//3 + 20, 2*h//3 - 40)
    else:  # east
        x = -vehicle_type['width']
        y = random.randint(h//3 + 20, 2*h//3 - 40)
    
    vehicles.append({
        'x': x,
        'y': y,
        'width': vehicle_type['width'],
        'height': vehicle_type['height'],
        'speed': vehicle_type['speed'] + random.uniform(-1, 1)
    })

def draw_vehicle(frame, vehicle, color):
    """Draw a vehicle on the frame"""
    x, y = vehicle['x'], vehicle['y']
    w, h = vehicle['width'], vehicle['height']
    
    # Draw vehicle body
    cv2.rectangle(frame, (int(x), int(y)), (int(x + w), int(y + h)), color, -1)
    cv2.rectangle(frame, (int(x), int(y)), (int(x + w), int(y + h)), (0, 0, 0), 2)
    
    # Draw windows (simplified)
    window_color = (100, 100, 100)
    if w > 40:  # Car or larger
        cv2.rectangle(frame, (int(x + 5), int(y + 3)), (int(x + w - 5), int(y + 10)), window_color, -1)
    
    # Draw headlights
    if vehicle['speed'] > 0:
        headlight_color = (255, 255, 200)
        if vehicle['speed'] > 0:  # Moving forward
            if 'south' in str(vehicle) or 'east' in str(vehicle):
                cv2.circle(frame, (int(x + w - 5), int(y + 5)), 3, headlight_color, -1)
                cv2.circle(frame, (int(x + w - 5), int(y + h - 5)), 3, headlight_color, -1)

def draw_lane_info(frame, lane_name, vehicle_count, frame_num, text_color):
    """Draw lane information on the frame"""
    h, w = frame.shape[:2]
    
    # Draw semi-transparent overlay for info
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
    
    # Draw lane name
    cv2.putText(frame, f"{lane_name.upper()} LANE", (10, 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
    
    # Draw vehicle count
    cv2.putText(frame, f"Vehicles: {vehicle_count}", (10, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Draw frame number
    cv2.putText(frame, f"Frame: {frame_num}", (10, 75), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    # Draw timestamp
    time_seconds = frame_num // 30
    cv2.putText(frame, f"Time: {time_seconds:02d}s", (w - 120, 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)

def draw_traffic_lights(frame, lane_name, light_cycle):
    """Draw traffic lights for the lane"""
    h, w = frame.shape[:2]
    
    # Traffic light positions
    positions = {
        'north': (w - 80, 100),
        'east': (80, h - 100),
        'south': (80, 100),
        'west': (w - 80, h - 100)
    }
    
    x, y = positions[lane_name]
    
    # Draw traffic light box
    cv2.rectangle(frame, (x - 20, y - 50), (x + 20, y + 50), (50, 50, 50), -1)
    cv2.rectangle(frame, (x - 20, y - 50), (x + 20, y + 50), (200, 200, 200), 2)
    
    # Draw lights (red, yellow, green)
    lights = ['red', 'yellow', 'green']
    light_colors = [(0, 0, 255), (0, 255, 255), (0, 255, 0)]
    
    current_light = light_cycle % 3
    
    for i, (light_name, color) in enumerate(zip(lights, light_colors)):
        light_y = y - 30 + i * 30
        
        if i == current_light:
            # Active light
            cv2.circle(frame, (x, light_y), 8, color, -1)
            cv2.circle(frame, (x, light_y), 8, color, 2)
        else:
            # Inactive light
            cv2.circle(frame, (x, light_y), 8, (40, 40, 40), -1)
            cv2.circle(frame, (x, light_y), 8, (60, 60, 60), 1)

def main():
    """Create all sample videos"""
    print("🚦 Creating Sample Traffic Videos for Multi-Lane System")
    print("=" * 60)
    
    # Create output directory
    os.makedirs('sample_videos', exist_ok=True)
    
    # Create videos for each lane
    lanes = ['north', 'east', 'south', 'west']
    
    for lane in lanes:
        output_path = f'sample_videos/{lane}_traffic.mp4'
        create_lane_video(lane, output_path, duration=30, fps=30)
    
    print("\n" + "=" * 60)
    print("✅ All sample videos created successfully!")
    print("📁 Videos saved in 'sample_videos' directory:")
    
    for lane in lanes:
        print(f"  - {lane}_traffic.mp4")
    
    print("\n🚀 Ready to use with the Multi-Lane Traffic Control System!")
    print("📱 Upload these videos to test each lane independently.")

if __name__ == "__main__":
    main()
