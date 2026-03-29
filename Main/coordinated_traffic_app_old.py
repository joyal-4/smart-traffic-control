from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import base64
import threading
import time
import os
from datetime import datetime
import random

app = Flask(__name__)

# Coordinated traffic system data
lanes_system = {
    'north': {
        'cap': None,
        'detector': None,
        'is_running': False,
        'current_frame': None,
        'frame_count': 0,
        'video_path': None,
        'vehicle_count': 0,
        'traffic_density': 0,
        'signal_state': 'red',
        'is_active': False,  # Whether this lane is currently green
        'last_processed': time.time()
    },
    'east': {
        'cap': None,
        'detector': None,
        'is_running': False,
        'current_frame': None,
        'frame_count': 0,
        'video_path': None,
        'vehicle_count': 0,
        'traffic_density': 0,
        'signal_state': 'red',
        'is_active': False,
        'last_processed': time.time()
    },
    'south': {
        'cap': None,
        'detector': None,
        'is_running': False,
        'current_frame': None,
        'frame_count': 0,
        'video_path': None,
        'vehicle_count': 0,
        'traffic_density': 0,
        'signal_state': 'red',
        'is_active': False,
        'last_processed': time.time()
    },
    'west': {
        'cap': None,
        'detector': None,
        'is_running': False,
        'current_frame': None,
        'frame_count': 0,
        'video_path': None,
        'vehicle_count': 0,
        'traffic_density': 0,
        'signal_state': 'red',
        'is_active': False,
        'last_processed': time.time()
    }
}

# Coordinated system state
coordinator = {
    'active_lane': None,
    'green_timer': 0,
    'min_green_time': 10,  # Minimum green time in seconds
    'max_green_time': 30,  # Maximum green time in seconds
    'cycle_count': 0,
    'last_switch': time.time(),
    'analysis_interval': 3,  # Analyze traffic every 3 seconds
    'last_analysis': time.time()
}

system_lock = threading.Lock()

@app.route('/')
def index():
    """Main page"""
    return render_template('coordinated_index.html')

@app.route('/upload_coordinated_video', methods=['POST'])
def upload_coordinated_video():
    """Handle video upload for coordinated system"""
    try:
        if 'video' not in request.files:
            return jsonify({'success': False, 'message': 'No video file'})
        
        file = request.files['video']
        lane = request.form.get('lane', 'unknown')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        # Save file with lane prefix
        filename = f"{lane}_{datetime.now().strftime('%H%M%S')}_{file.filename}"
        os.makedirs('uploads', exist_ok=True)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        with system_lock:
            lanes_system[lane]['video_path'] = filepath
        
        return jsonify({'success': True, 'filename': filename, 'lane': lane})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/start_coordinated_analysis', methods=['POST'])
def start_coordinated_analysis():
    """Start coordinated traffic analysis"""
    try:
        with system_lock:
            started_lanes = []
            
            for lane_name, lane_data in lanes_system.items():
                if lane_data['video_path'] and not lane_data['is_running']:
                    # Import here to avoid issues
                    from vehicle_detector import VehicleDetector
                    
                    # Initialize video capture
                    lane_data['cap'] = cv2.VideoCapture(lane_data['video_path'])
                    if not lane_data['cap'].isOpened():
                        continue
                    
                    # Initialize detector
                    lane_data['detector'] = VehicleDetector()
                    
                    # Reset counters
                    lane_data['frame_count'] = 0
                    lane_data['vehicle_count'] = 0
                    lane_data['is_running'] = True
                    lane_data['signal_state'] = 'red'
                    lane_data['is_active'] = False
                    
                    started_lanes.append(lane_name)
            
            if started_lanes:
                # Start coordinator thread
                coordinator['active_lane'] = started_lanes[0]  # Start with first lane
                coordinator['green_timer'] = coordinator['min_green_time']
                coordinator['last_switch'] = time.time()
                coordinator['last_analysis'] = time.time()
                
                # Start processing threads
                for lane_name in started_lanes:
                    thread = threading.Thread(
                        target=process_lane_video_coordinated, 
                        args=(lane_name,), 
                        daemon=True
                    )
                    thread.start()
                
                # Start coordinator thread
                coord_thread = threading.Thread(
                    target=traffic_coordinator,
                    daemon=True
                )
                coord_thread.start()
            
            return jsonify({
                'success': True, 
                'started_lanes': started_lanes,
                'active_lane': coordinator['active_lane']
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stop_coordinated_analysis', methods=['POST'])
def stop_coordinated_analysis():
    """Stop coordinated analysis"""
    try:
        with system_lock:
            for lane_name, lane_data in lanes_system.items():
                lane_data['is_running'] = False
                lane_data['is_active'] = False
                
                if lane_data['cap']:
                    lane_data['cap'].release()
                    lane_data['cap'] = None
            
            # Reset coordinator
            coordinator['active_lane'] = None
            coordinator['green_timer'] = 0
        
        return jsonify({'success': True, 'message': 'Coordinated system stopped'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reset_coordinated_analysis', methods=['POST'])
def reset_coordinated_analysis():
    """Reset coordinated system"""
    try:
        stop_coordinated_analysis()
        
        with system_lock:
            for lane_name, lane_data in lanes_system.items():
                lane_data['video_path'] = None
                lane_data['current_frame'] = None
                lane_data['frame_count'] = 0
                lane_data['vehicle_count'] = 0
                lane_data['traffic_density'] = 0
                lane_data['signal_state'] = 'red'
                lane_data['is_active'] = False
            
            # Reset coordinator
            coordinator['cycle_count'] = 0
            coordinator['last_switch'] = time.time()
            coordinator['last_analysis'] = time.time()
            
            # Clean uploads
            if os.path.exists('uploads'):
                for f in os.listdir('uploads'):
                    os.remove(os.path.join('uploads', f))
        
        return jsonify({'success': True, 'message': 'Coordinated system reset'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_coordinated_frames')
def get_coordinated_frames():
    """Get current frames from coordinated system"""
    try:
        with system_lock:
            response_data = {
                'success': True,
                'lanes': {},
                'coordinator': {
                    'active_lane': coordinator['active_lane'],
                    'green_timer': coordinator['green_timer'],
                    'cycle_count': coordinator['cycle_count']
                }
            }
            
            for lane_name, lane_data in lanes_system.items():
                lane_info = {
                    'frame_count': lane_data['frame_count'],
                    'vehicle_count': lane_data['vehicle_count'],
                    'traffic_density': lane_data['traffic_density'],
                    'signal_state': lane_data['signal_state'],
                    'is_active': lane_data['is_active'],
                    'is_running': lane_data['is_running']
                }
                
                # Only show video frame for active lane
                if lane_data['current_frame'] is not None and lane_data['is_active']:
                    # Convert frame to base64
                    frame_rgb = cv2.cvtColor(lane_data['current_frame'], cv2.COLOR_BGR2RGB)
                    _, buffer = cv2.imencode('.jpg', frame_rgb)
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    lane_info['frame'] = frame_b64
                elif lane_data['current_frame'] is not None and not lane_data['is_active']:
                    # Show paused frame for inactive lanes
                    frame_rgb = cv2.cvtColor(lane_data['current_frame'], cv2.COLOR_BGR2RGB)
                    # Add "PAUSED" overlay
                    h, w = frame_rgb.shape[:2]
                    overlay = frame_rgb.copy()
                    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
                    frame_rgb = cv2.addWeighted(overlay, 0.7, frame_rgb, 0.3, 0)
                    cv2.putText(frame_rgb, "PAUSED", (w//2 - 80, h//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                    cv2.putText(frame_rgb, f"Vehicles: {lane_data['vehicle_count']}", (w//2 - 100, h//2 + 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                    _, buffer = cv2.imencode('.jpg', frame_rgb)
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    lane_info['frame'] = frame_b64
                
                response_data['lanes'][lane_name] = lane_info
            
            return jsonify(response_data)
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def calculate_wait_time(lane_name):
    """Calculate wait time for each lane"""
    if lane_name == coordinator['active_lane']:
        return 0
    
    # Estimate wait time based on position in queue
    total_vehicles = sum(lanes_system[lane]['vehicle_count'] for lane in lanes_system.values() if lanes_system[lane]['is_running'])
    current_vehicles = lanes_system[lane_name]['vehicle_count']
    
    if total_vehicles == 0:
        return 0
    
    # Simple priority calculation
    priority_factor = current_vehicles / max(total_vehicles, 1)
    estimated_wait = max(0, (coordinator['green_timer'] + coordinator['yellow_timer'])) * (1 - priority_factor)
    
    return round(estimated_wait, 1)

def get_lane_priority(lane_name):
    """Get priority level for lane"""
    vehicle_count = lanes_system[lane_name]['vehicle_count']
    
    if vehicle_count >= 10:
        return "HIGH"
    elif vehicle_count >= 5:
        return "MEDIUM"
    elif vehicle_count >= 2:
        return "LOW"
    else:
        return "MINIMAL"

def traffic_coordinator():
    """Main traffic coordination logic"""
    while True:
        try:
            with system_lock:
                current_time = time.time()
                
                # Check if it's time to analyze traffic
                if current_time - coordinator['last_analysis'] >= coordinator['analysis_interval']:
                    analyze_all_lanes()
                    coordinator['last_analysis'] = current_time
                
                # Check if it's time to switch lanes
                if coordinator['green_timer'] <= 0:
                    switch_to_best_lane()
                    coordinator['last_switch'] = current_time
                    coordinator['cycle_count'] += 1
                else:
                    coordinator['green_timer'] -= 0.1  # Decrease timer
                
        except Exception as e:
            print(f"Coordinator error: {e}")
        
        time.sleep(0.1)  # Run every 100ms

def analyze_all_lanes():
    """Analyze traffic in all lanes and determine best lane"""
    max_vehicles = 0
    best_lane = None
    
    for lane_name, lane_data in lanes_system.items():
        if lane_data['is_running']:
            # Update traffic density based on vehicle count
            if lane_data['vehicle_count'] <= 2:
                lane_data['traffic_density'] = 'Low'
            elif lane_data['vehicle_count'] <= 5:
                lane_data['traffic_density'] = 'Medium'
            elif lane_data['vehicle_count'] <= 10:
                lane_data['traffic_density'] = 'High'
            else:
                lane_data['traffic_density'] = 'Critical'
            
            # Find lane with highest vehicle count
            if lane_data['vehicle_count'] > max_vehicles:
                max_vehicles = lane_data['vehicle_count']
                best_lane = lane_name
    
    # Only switch if current lane has had minimum green time
    if best_lane and best_lane != coordinator['active_lane']:
        if coordinator['green_timer'] <= coordinator['min_green_time']:
            switch_to_lane(best_lane)

def switch_to_best_lane():
    """Switch to the lane with highest traffic"""
    max_vehicles = 0
    best_lane = None
    
    for lane_name, lane_data in lanes_system.items():
        if lane_data['is_running'] and lane_data['vehicle_count'] > max_vehicles:
            max_vehicles = lane_data['vehicle_count']
            best_lane = lane_name
    
    if best_lane:
        switch_to_lane(best_lane)

def switch_to_lane(lane_name):
    """Switch to specific lane"""
    if not lane_name or lane_name == coordinator['active_lane']:
        return
    
    print(f"Switching from {coordinator['active_lane']} to {lane_name}")
    
    # Deactivate current lane
    if coordinator['active_lane']:
        lanes_system[coordinator['active_lane']]['signal_state'] = 'red'
        lanes_system[coordinator['active_lane']]['is_active'] = False
    
    # Activate new lane
    coordinator['active_lane'] = lane_name
    lanes_system[lane_name]['signal_state'] = 'green'
    lanes_system[lane_name]['is_active'] = True
    
    # Set green time based on traffic density
    vehicle_count = lanes_system[lane_name]['vehicle_count']
    if vehicle_count <= 2:
        coordinator['green_timer'] = coordinator['min_green_time']
    elif vehicle_count <= 5:
        coordinator['green_timer'] = coordinator['min_green_time'] + 5
    elif vehicle_count <= 10:
        coordinator['green_timer'] = coordinator['min_green_time'] + 10
    else:
        coordinator['green_timer'] = coordinator['max_green_time']

def process_lane_video_coordinated(lane_name):
    """Process video for coordinated system"""
    lane_data = lanes_system[lane_name]
    
    while lane_data['is_running']:
        try:
            if lane_data['cap'] and lane_data['is_running']:
                ret, frame = lane_data['cap'].read()
                if not ret:
                    lane_data['is_running'] = False
                    break
                
                # Only process if lane is active (green)
                if lane_data['is_active']:
                    if lane_data['detector']:
                        # Detect vehicles
                        detections = lane_data['detector'].detect_vehicles(frame)
                        lane_data['vehicle_count'] = len(detections)
                        
                        # Draw detections on frame
                        frame = lane_data['detector'].draw_detections(frame, detections)
                    
                    # Draw lane info
                    frame = draw_coordinated_lane_info(frame, lane_name, lane_data)
                    lane_data['current_frame'] = frame
                else:
                    # Still count vehicles even when inactive
                    if lane_data['detector']:
                        detections = lane_data['detector'].detect_vehicles(frame)
                        lane_data['vehicle_count'] = len(detections)
                    
                    lane_data['current_frame'] = frame
                
                lane_data['frame_count'] += 1
                lane_data['last_processed'] = time.time()
                
        except Exception as e:
            print(f"Error processing {lane_name}: {e}")
            lane_data['is_running'] = False
            break
        
        time.sleep(0.05)  # Process at ~20 FPS

def draw_coordinated_lane_info(frame, lane_name, lane_data):
    """Draw lane information on frame"""
    h, w = frame.shape[:2]
    
    # Draw lane name
    cv2.putText(frame, lane_name.upper(), (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Draw vehicle count
    cv2.putText(frame, f"Vehicles: {lane_data['vehicle_count']}", (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw signal state
    signal_color = (0, 255, 0) if lane_data['signal_state'] == 'green' else (0, 0, 255)
    cv2.circle(frame, (w - 50, 50), 20, signal_color, -1)
    cv2.putText(frame, lane_data['signal_state'].upper(), (w - 100, 90), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, signal_color, 2)
    
    return frame

if __name__ == '__main__':
    print("🚦 Coordinated Traffic Control System")
    print("📱 Open browser to: http://127.0.0.1:5000")
    print("🎯 Only one lane gets green at a time!")
    app.run(host='127.0.0.1', port=5000, debug=False)
    if coordinator['active_lane']:
        lanes_system[coordinator['active_lane']]['signal_state'] = 'red'
        lanes_system[coordinator['active_lane']]['is_active'] = False
    
    # Activate new lane
    coordinator['active_lane'] = lane_name
    lanes_system[lane_name]['signal_state'] = 'green'
    lanes_system[lane_name]['is_active'] = True
    
    # Set green time based on traffic density
    vehicle_count = lanes_system[lane_name]['vehicle_count']
    if vehicle_count <= 2:
        coordinator['green_timer'] = coordinator['min_green_time']
    elif vehicle_count <= 5:
        coordinator['green_timer'] = coordinator['min_green_time'] + 5
    elif vehicle_count <= 10:
        coordinator['green_timer'] = coordinator['min_green_time'] + 10
    else:
        coordinator['green_timer'] = coordinator['max_green_time']

def process_lane_video_coordinated(lane_name):
    """Process video for coordinated system"""
    lane_data = lanes_system[lane_name]
    
    while lane_data['is_running']:
        try:
            if lane_data['cap'] and lane_data['is_running']:
                ret, frame = lane_data['cap'].read()
                if not ret:
                    lane_data['is_running'] = False
                    break
                
                # Only process if lane is active (green)
                if lane_data['is_active']:
                    if lane_data['detector']:
                        # Detect vehicles
                        detections = lane_data['detector'].detect_vehicles(frame)
                        lane_data['vehicle_count'] = len(detections)
                        
                        # Draw detections on frame
                        frame = lane_data['detector'].draw_detections(frame, detections)
                    
                    # Draw lane info
                    frame = draw_coordinated_lane_info(frame, lane_name, lane_data['vehicle_count'], lane_data['signal_state'])
                else:
                    # For inactive lanes, just count vehicles without processing
                    if lane_data['detector']:
                        detections = lane_data['detector'].detect_vehicles(frame)
                        lane_data['vehicle_count'] = len(detections)
                
                lane_data['current_frame'] = frame.copy()
                lane_data['frame_count'] += 1
                
        except Exception as e:
            print(f"Processing error in {lane_name}: {e}")
            break
        
        time.sleep(0.033)  # ~30 FPS

def draw_coordinated_lane_info(frame, lane_name, vehicle_count, signal_state):
    """Draw coordinated lane information on frame"""
    h, w = frame.shape[:2]
    
    # Draw semi-transparent overlay for info
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
    
    # Draw lane name
    cv2.putText(frame, f"{lane_name.upper()} LANE", (10, 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Draw vehicle count
    cv2.putText(frame, f"Vehicles: {vehicle_count}", (10, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Draw signal state
    signal_color = (0, 255, 0) if signal_state == 'green' else (0, 0, 255)
    cv2.putText(frame, f"Signal: {signal_state.upper()}", (10, 75), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, signal_color, 2)
    
    # Draw active indicator
    if signal_state == 'green':
        cv2.putText(frame, "ACTIVE", (w - 120, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
    
    return frame

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    print("Starting Coordinated Traffic Control System...")
    print("Open browser to: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
