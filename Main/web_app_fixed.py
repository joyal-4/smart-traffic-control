from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import base64
import threading
import time
import os
from datetime import datetime

app = Flask(__name__)

# Global variables
traffic_system = {
    'cap': None,
    'is_running': False,
    'current_frame': None,
    'frame_count': 0,
    'video_path': None,
    'detector': None,
    'lane_manager': None,
    'signal_controller': None
}

system_lock = threading.Lock()

@app.route('/')
def index():
    """Main page"""
    return render_template('simple_index.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Handle video upload"""
    try:
        if 'video' not in request.files:
            return jsonify({'success': False, 'message': 'No video file'})
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        # Save file
        filename = f"traffic_{datetime.now().strftime('%H%M%S')}.mp4"
        os.makedirs('uploads', exist_ok=True)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        with system_lock:
            traffic_system['video_path'] = filepath
        
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Start analysis"""
    try:
        with system_lock:
            if traffic_system['is_running']:
                return jsonify({'success': False, 'message': 'Already running'})
            
            if not traffic_system['video_path']:
                return jsonify({'success': False, 'message': 'No video loaded'})
            
            # Import here to avoid issues
            from vehicle_detector import VehicleDetector
            from traffic_lane_manager import TrafficLaneManager
            from traffic_signal_controller import TrafficSignalController
            
            # Initialize components
            traffic_system['cap'] = cv2.VideoCapture(traffic_system['video_path'])
            if not traffic_system['cap'].isOpened():
                return jsonify({'success': False, 'message': 'Cannot open video'})
            
            traffic_system['detector'] = VehicleDetector()
            w = int(traffic_system['cap'].get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(traffic_system['cap'].get(cv2.CAP_PROP_FRAME_HEIGHT))
            traffic_system['lane_manager'] = TrafficLaneManager(w, h)
            traffic_system['signal_controller'] = TrafficSignalController()
            traffic_system['signal_controller'].start()
            
            traffic_system['is_running'] = True
            traffic_system['frame_count'] = 0
            
            # Start processing thread
            thread = threading.Thread(target=process_video, daemon=True)
            thread.start()
            
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stop_analysis', methods=['POST'])
def stop_analysis():
    """Stop analysis"""
    try:
        with system_lock:
            traffic_system['is_running'] = False
            
            if traffic_system['signal_controller']:
                traffic_system['signal_controller'].stop()
            
            if traffic_system['cap']:
                traffic_system['cap'].release()
                traffic_system['cap'] = None
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reset_analysis', methods=['POST'])
def reset_analysis():
    """Reset system"""
    try:
        stop_analysis()
        
        with system_lock:
            traffic_system['video_path'] = None
            traffic_system['current_frame'] = None
            
            # Clean uploads
            if os.path.exists('uploads'):
                for f in os.listdir('uploads'):
                    os.remove(os.path.join('uploads', f))
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_frame')
def get_frame():
    """Get current frame"""
    try:
        with system_lock:
            if traffic_system['current_frame'] is None:
                return jsonify({'success': False, 'message': 'No frame'})
            
            # Convert frame to base64
            frame_rgb = cv2.cvtColor(traffic_system['current_frame'], cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', frame_rgb)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            
            data = {
                'success': True,
                'frame': frame_b64,
                'frame_count': traffic_system['frame_count']
            }
            
            # Add lane data
            if traffic_system['lane_manager']:
                counts = traffic_system['lane_manager'].get_all_counts()
                data['vehicle_counts'] = counts
                data['total_vehicles'] = sum(counts.values())
            
            # Add signal data
            if traffic_system['signal_controller']:
                data['countdown'] = traffic_system['signal_controller'].countdown
                
                # Get signal states
                signal_colors = traffic_system['signal_controller'].get_signal_colors()
                states = []
                for color in signal_colors:
                    if color == (0, 0, 255):
                        states.append('red')
                    elif color == (0, 255, 255):
                        states.append('yellow')
                    else:
                        states.append('green')
                data['signal_states'] = states
                
                # Active lane
                if traffic_system['lane_manager']:
                    active_id = traffic_system['signal_controller'].current_lane
                    active_name = traffic_system['lane_manager'].lanes[active_id]['name']
                    data['active_lane'] = active_name
            
            return jsonify(data)
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_status')
def get_status():
    """Get system status"""
    with system_lock:
        return jsonify({
            'is_running': traffic_system['is_running'],
            'video_loaded': traffic_system['video_path'] is not None
        })

def process_video():
    """Process video in background"""
    while traffic_system['is_running']:
        try:
            if traffic_system['cap'] and traffic_system['is_running']:
                ret, frame = traffic_system['cap'].read()
                if not ret:
                    traffic_system['is_running'] = False
                    break
                
                # Process frame
                if traffic_system['detector'] and traffic_system['lane_manager'] and traffic_system['signal_controller']:
                    # Detect vehicles
                    detections = traffic_system['detector'].detect_vehicles(frame)
                    
                    # Update lane manager
                    traffic_system['lane_manager'].update_vehicle_counts(detections)
                    
                    # Update signal controller
                    counts = traffic_system['lane_manager'].get_all_counts()
                    traffic_system['signal_controller'].update_vehicle_counts(counts)
                    
                    # Draw everything
                    frame = traffic_system['detector'].draw_detections(frame, detections)
                    frame = traffic_system['lane_manager'].draw_lanes(frame)
                    frame = traffic_system['signal_controller'].draw_signals(frame, traffic_system['lane_manager'])
                
                traffic_system['current_frame'] = frame.copy()
                traffic_system['frame_count'] += 1
                
        except Exception as e:
            print(f"Processing error: {e}")
            break
        
        time.sleep(0.033)  # ~30 FPS

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    print("Starting Smart Traffic Control System...")
    print("Open browser to: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
