from flask import Flask, render_template, request, jsonify, send_file
import cv2
import numpy as np
import base64
import threading
import time
import os
from datetime import datetime
from vehicle_detector import VehicleDetector
from traffic_lane_manager import TrafficLaneManager
from traffic_signal_controller import TrafficSignalController
import json

app = Flask(__name__)

# Global variables for traffic analysis
traffic_system = {
    'detector': None,
    'lane_manager': None,
    'signal_controller': None,
    'cap': None,
    'is_running': False,
    'is_paused': False,
    'current_frame': None,
    'frame_width': 640,
    'frame_height': 480,
    'fps': 0,
    'frame_count': 0,
    'start_time': time.time(),
    'video_path': None,
    'analysis_thread': None
}

# Lock for thread safety
system_lock = threading.Lock()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Handle video file upload"""
    if 'video' not in request.files:
        return jsonify({'success': False, 'message': 'No video file provided'})
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    try:
        # Save uploaded file
        filename = f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(filepath)
        
        with system_lock:
            traffic_system['video_path'] = filepath
        
        return jsonify({
            'success': True, 
            'message': 'Video uploaded successfully',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Start traffic analysis"""
    with system_lock:
        if traffic_system['is_running']:
            return jsonify({'success': False, 'message': 'Analysis already running'})
        
        if not traffic_system['video_path']:
            return jsonify({'success': False, 'message': 'No video loaded'})
        
        try:
            # Initialize video capture
            traffic_system['cap'] = cv2.VideoCapture(traffic_system['video_path'])
            if not traffic_system['cap'].isOpened():
                raise Exception("Could not open video file")
            
            # Get video dimensions
            traffic_system['frame_width'] = int(traffic_system['cap'].get(cv2.CAP_PROP_FRAME_WIDTH))
            traffic_system['frame_height'] = int(traffic_system['cap'].get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Initialize components
            traffic_system['detector'] = VehicleDetector()
            traffic_system['lane_manager'] = TrafficLaneManager(
                traffic_system['frame_width'], 
                traffic_system['frame_height']
            )
            traffic_system['signal_controller'] = TrafficSignalController()
            traffic_system['signal_controller'].start()
            
            # Reset metrics
            traffic_system['frame_count'] = 0
            traffic_system['start_time'] = time.time()
            traffic_system['is_running'] = True
            traffic_system['is_paused'] = False
            
            # Start analysis thread
            traffic_system['analysis_thread'] = threading.Thread(
                target=analysis_loop, daemon=True
            )
            traffic_system['analysis_thread'].start()
            
            return jsonify({'success': True, 'message': 'Analysis started'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/stop_analysis', methods=['POST'])
def stop_analysis():
    """Stop traffic analysis"""
    with system_lock:
        traffic_system['is_running'] = False
        traffic_system['is_paused'] = False
        
        if traffic_system['signal_controller']:
            traffic_system['signal_controller'].stop()
        
        if traffic_system['cap']:
            traffic_system['cap'].release()
            traffic_system['cap'] = None
        
        return jsonify({'success': True, 'message': 'Analysis stopped'})

@app.route('/reset_analysis', methods=['POST'])
def reset_analysis():
    """Reset analysis"""
    stop_analysis()
    
    with system_lock:
        traffic_system['video_path'] = None
        traffic_system['current_frame'] = None
        traffic_system['fps'] = 0
        traffic_system['frame_count'] = 0
        
        # Clean up uploaded files
        if os.path.exists('uploads'):
            for file in os.listdir('uploads'):
                os.remove(os.path.join('uploads', file))
    
    return jsonify({'success': True, 'message': 'System reset'})

@app.route('/get_frame')
def get_frame():
    """Get current processed frame"""
    with system_lock:
        if traffic_system['current_frame'] is None:
            return jsonify({'success': False, 'message': 'No frame available'})
        
        # Convert frame to base64
        frame_rgb = cv2.cvtColor(traffic_system['current_frame'], cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', frame_rgb)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Get system data
        data = {
            'success': True,
            'frame': frame_base64,
            'fps': round(traffic_system['fps'], 1),
            'frame_count': traffic_system['frame_count']
        }
        
        # Add lane data if available
        if traffic_system['lane_manager']:
            vehicle_counts = traffic_system['lane_manager'].get_all_counts()
            data['vehicle_counts'] = vehicle_counts
            data['total_vehicles'] = sum(vehicle_counts.values())
            
            # Get most congested lane
            congested_lanes = traffic_system['lane_manager'].get_congested_lanes()
            if congested_lanes and congested_lanes[0][1] > 0:
                most_congested_id = congested_lanes[0][0]
                most_congested_name = traffic_system['lane_manager'].lanes[most_congested_id]['name']
                data['most_congested'] = most_congested_name
            else:
                data['most_congested'] = 'None'
        
        # Add signal data if available
        if traffic_system['signal_controller']:
            data['countdown'] = traffic_system['signal_controller'].countdown
            data['active_lane'] = traffic_system['lane_manager'].lanes[
                traffic_system['signal_controller'].current_lane
            ]['name'] if traffic_system['lane_manager'] else 'None'
            
            # Get signal states
            signal_colors = traffic_system['signal_controller'].get_signal_colors()
            data['signal_states'] = []
            for i, color in enumerate(signal_colors):
                if color == (0, 0, 255):  # Red
                    state = 'red'
                elif color == (0, 255, 255):  # Yellow
                    state = 'yellow'
                elif color == (0, 255, 0):  # Green
                    state = 'green'
                else:
                    state = 'red'
                data['signal_states'].append(state)
        
        return jsonify(data)

@app.route('/get_status')
def get_status():
    """Get system status"""
    with system_lock:
        status = {
            'is_running': traffic_system['is_running'],
            'is_paused': traffic_system['is_paused'],
            'video_loaded': traffic_system['video_path'] is not None,
            'video_name': os.path.basename(traffic_system['video_path']) if traffic_system['video_path'] else None
        }
        return jsonify(status)

def analysis_loop():
    """Main analysis loop"""
    while traffic_system['is_running']:
        if not traffic_system['is_paused'] and traffic_system['cap']:
            ret, frame = traffic_system['cap'].read()
            if not ret:
                traffic_system['is_running'] = False
                break
            
            # Process frame
            process_frame(frame)
            
            # Update FPS
            traffic_system['frame_count'] += 1
            elapsed = time.time() - traffic_system['start_time']
            if elapsed > 0:
                traffic_system['fps'] = traffic_system['frame_count'] / elapsed
        
        time.sleep(0.033)  # ~30 FPS

def process_frame(frame):
    """Process a single frame"""
    # Detect vehicles
    detections = traffic_system['detector'].detect_vehicles(frame)
    
    # Update lane manager
    traffic_system['lane_manager'].update_vehicle_counts(detections)
    
    # Update signal controller
    vehicle_counts = traffic_system['lane_manager'].get_all_counts()
    traffic_system['signal_controller'].update_vehicle_counts(vehicle_counts)
    
    # Draw everything on frame
    frame = traffic_system['detector'].draw_detections(frame, detections)
    frame = traffic_system['lane_manager'].draw_lanes(frame)
    frame = traffic_system['signal_controller'].draw_signals(frame, traffic_system['lane_manager'])
    
    # Store current frame
    traffic_system['current_frame'] = frame.copy()

if __name__ == '__main__':
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
