from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import base64
import threading
import time
import os
from datetime import datetime

app = Flask(__name__)

# Multi-lane system data
lanes_system = {
    'north': {
        'cap': None,
        'detector': None,
        'signal_controller': None,
        'is_running': False,
        'current_frame': None,
        'frame_count': 0,
        'video_path': None,
        'fps': 0,
        'start_time': time.time()
    },
    'east': {
        'cap': None,
        'detector': None,
        'signal_controller': None,
        'is_running': False,
        'current_frame': None,
        'frame_count': 0,
        'video_path': None,
        'fps': 0,
        'start_time': time.time()
    },
    'south': {
        'cap': None,
        'detector': None,
        'signal_controller': None,
        'is_running': False,
        'current_frame': None,
        'frame_count': 0,
        'video_path': None,
        'fps': 0,
        'start_time': time.time()
    },
    'west': {
        'cap': None,
        'detector': None,
        'signal_controller': None,
        'is_running': False,
        'current_frame': None,
        'frame_count': 0,
        'video_path': None,
        'fps': 0,
        'start_time': time.time()
    }
}

system_lock = threading.Lock()

@app.route('/')
def index():
    """Main page"""
    return render_template('multi_lane_index.html')

@app.route('/upload_multi_video', methods=['POST'])
def upload_multi_video():
    """Handle video upload for specific lane"""
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

@app.route('/start_multi_analysis', methods=['POST'])
def start_multi_analysis():
    """Start analysis for all lanes with videos"""
    try:
        with system_lock:
            started_lanes = []
            
            for lane_name, lane_data in lanes_system.items():
                if lane_data['video_path'] and not lane_data['is_running']:
                    # Import here to avoid issues
                    from vehicle_detector import VehicleDetector
                    from traffic_signal_controller import TrafficSignalController
                    
                    # Initialize video capture
                    lane_data['cap'] = cv2.VideoCapture(lane_data['video_path'])
                    if not lane_data['cap'].isOpened():
                        continue
                    
                    # Initialize detector and signal controller
                    lane_data['detector'] = VehicleDetector()
                    lane_data['signal_controller'] = TrafficSignalController()
                    lane_data['signal_controller'].start()
                    
                    # Reset counters
                    lane_data['frame_count'] = 0
                    lane_data['start_time'] = time.time()
                    lane_data['is_running'] = True
                    
                    started_lanes.append(lane_name)
            
            # Start processing threads for each lane
            for lane_name in started_lanes:
                thread = threading.Thread(
                    target=process_lane_video, 
                    args=(lane_name,), 
                    daemon=True
                )
                thread.start()
            
            return jsonify({
                'success': True, 
                'started_lanes': started_lanes,
                'message': f'Started analysis for {len(started_lanes)} lanes'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stop_multi_analysis', methods=['POST'])
def stop_multi_analysis():
    """Stop analysis for all lanes"""
    try:
        with system_lock:
            for lane_name, lane_data in lanes_system.items():
                lane_data['is_running'] = False
                
                if lane_data['signal_controller']:
                    lane_data['signal_controller'].stop()
                
                if lane_data['cap']:
                    lane_data['cap'].release()
                    lane_data['cap'] = None
        
        return jsonify({'success': True, 'message': 'All lanes stopped'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reset_multi_analysis', methods=['POST'])
def reset_multi_analysis():
    """Reset entire system"""
    try:
        stop_multi_analysis()
        
        with system_lock:
            for lane_name, lane_data in lanes_system.items():
                lane_data['video_path'] = None
                lane_data['current_frame'] = None
                lane_data['frame_count'] = 0
                lane_data['fps'] = 0
            
            # Clean uploads
            if os.path.exists('uploads'):
                for f in os.listdir('uploads'):
                    os.remove(os.path.join('uploads', f))
        
        return jsonify({'success': True, 'message': 'System reset'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_multi_frames')
def get_multi_frames():
    """Get current frames from all lanes"""
    try:
        with system_lock:
            response_data = {
                'success': True,
                'lanes': {}
            }
            
            for lane_name, lane_data in lanes_system.items():
                lane_info = {
                    'frame_count': lane_data['frame_count'],
                    'fps': round(lane_data['fps'], 1) if lane_data['fps'] > 0 else 0.0,
                    'is_running': lane_data['is_running']
                }
                
                if lane_data['current_frame'] is not None:
                    # Convert frame to base64
                    frame_rgb = cv2.cvtColor(lane_data['current_frame'], cv2.COLOR_BGR2RGB)
                    _, buffer = cv2.imencode('.jpg', frame_rgb)
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    lane_info['frame'] = frame_b64
                    
                    # Get vehicle count (simplified - just count detections)
                    if lane_data['detector']:
                        detections = lane_data['detector'].detect_vehicles(lane_data['current_frame'])
                        lane_info['vehicle_count'] = len(detections)
                        lane_info['total_vehicles'] = len(detections)
                        
                        # Simulate ambulance detection (random for demo)
                        lane_info['ambulance_detected'] = np.random.random() < 0.01  # 1% chance
                    else:
                        lane_info['vehicle_count'] = 0
                        lane_info['total_vehicles'] = 0
                        lane_info['ambulance_detected'] = False
                
                # Get signal state
                if lane_data['signal_controller']:
                    lane_info['countdown'] = lane_data['signal_controller'].countdown
                    
                    # Get signal color
                    signal_colors = lane_data['signal_controller'].get_signal_colors()
                    if signal_colors and len(signal_colors) > 0:
                        color = signal_colors[0]  # Get first (and only) signal
                        if color == (0, 0, 255):  # Red
                            lane_info['signal_state'] = 'red'
                        elif color == (0, 255, 255):  # Yellow
                            lane_info['signal_state'] = 'yellow'
                        elif color == (0, 255, 0):  # Green
                            lane_info['signal_state'] = 'green'
                        else:
                            lane_info['signal_state'] = 'red'
                    else:
                        lane_info['signal_state'] = 'red'
                else:
                    lane_info['signal_state'] = 'red'
                    lane_info['countdown'] = 0
                
                response_data['lanes'][lane_name] = lane_info
            
            return jsonify(response_data)
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def process_lane_video(lane_name):
    """Process video for a specific lane"""
    lane_data = lanes_system[lane_name]
    
    while lane_data['is_running']:
        try:
            if lane_data['cap'] and lane_data['is_running']:
                ret, frame = lane_data['cap'].read()
                if not ret:
                    lane_data['is_running'] = False
                    break
                
                # Process frame
                if lane_data['detector'] and lane_data['signal_controller']:
                    # Detect vehicles
                    detections = lane_data['detector'].detect_vehicles(frame)
                    
                    # Draw detections on frame
                    frame = lane_data['detector'].draw_detections(frame, detections)
                    
                    # Update signal controller with vehicle count
                    lane_data['signal_controller'].update_vehicle_counts({0: len(detections)})
                    
                    # Draw signal info on frame
                    frame = draw_lane_info(frame, lane_name, len(detections), lane_data['signal_controller'])
                
                lane_data['current_frame'] = frame.copy()
                lane_data['frame_count'] += 1
                
                # Update FPS
                elapsed = time.time() - lane_data['start_time']
                if elapsed > 0:
                    lane_data['fps'] = lane_data['frame_count'] / elapsed
                
        except Exception as e:
            print(f"Processing error in {lane_name}: {e}")
            break
        
        time.sleep(0.033)  # ~30 FPS

def draw_lane_info(frame, lane_name, vehicle_count, signal_controller):
    """Draw lane information on frame"""
    h, w = frame.shape[:2]
    
    # Draw semi-transparent overlay for info
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
    
    # Draw lane name
    cv2.putText(frame, f"{lane_name.upper()} LANE", (10, 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Draw vehicle count
    cv2.putText(frame, f"Vehicles: {vehicle_count}", (10, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Draw signal state
    if signal_controller:
        signal_colors = signal_controller.get_signal_colors()
        if signal_colors:
            color = signal_colors[0]
            if color == (0, 0, 255):
                signal_text = "RED"
                text_color = (0, 0, 255)
            elif color == (0, 255, 255):
                signal_text = "YELLOW"
                text_color = (0, 255, 255)
            elif color == (0, 255, 0):
                signal_text = "GREEN"
                text_color = (0, 255, 0)
            else:
                signal_text = "RED"
                text_color = (0, 0, 255)
            
            cv2.putText(frame, f"Signal: {signal_text}", (w - 150, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
            
            # Draw countdown
            cv2.putText(frame, f"Timer: {signal_controller.countdown}s", (w - 150, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return frame

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    print("Starting Multi-Lane Traffic Control System...")
    print("Open browser to: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
