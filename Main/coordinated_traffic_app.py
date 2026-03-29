from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import base64
import threading
import time
import os
from datetime import datetime
import random

# Import ML Optimizer
from traffic_optimizer import TrafficOptimizer

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
        'is_active': False,
        'last_processed': time.time(),
        'video_length': 0,
        'total_frames': 0,
        'fps': 30,
        'analyzed': False,
        'traffic_score': 0
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
        'last_processed': time.time(),
        'video_length': 0,
        'total_frames': 0,
        'fps': 30,
        'analyzed': False,
        'traffic_score': 0
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
        'last_processed': time.time(),
        'video_length': 0,
        'total_frames': 0,
        'fps': 30,
        'analyzed': False,
        'traffic_score': 0
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
        'last_processed': time.time(),
        'video_length': 0,
        'total_frames': 0,
        'fps': 30,
        'analyzed': False,
        'traffic_score': 0
    }
}

# Coordinated system state
coordinator = {
    'active_lane': None,
    'green_timer': 0,
    'min_green_time': 8,  # Minimum green time in seconds
    'max_green_time': 60,  # Maximum green time in seconds
    'cycle_count': 0,
    'last_switch': time.time(),
    'analysis_interval': 3,  # Analyze traffic every 3 seconds
    'last_analysis': time.time(),
    'ml_enabled': True,  # Machine Learning enabled
    'ml_accuracy': 0.0,
    'analysis_phase': True,  # Initial analysis phase
    'all_analyzed': False,
    'rotation_mode': False  # Systematic rotation mode
}

# Initialize ML Optimizer
traffic_optimizer = TrafficOptimizer()

system_lock = threading.Lock()

@app.route('/')
def index():
    """Main page"""
    return render_template('coordinated_index_standard.html')

@app.route('/upload_coordinated_video', methods=['POST'])
def upload_coordinated_video():
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
            lanes_system[lane]['analyzed'] = False
            lanes_system[lane]['traffic_score'] = 0
            # Reset analysis phase when new video uploaded
            coordinator['analysis_phase'] = True
            coordinator['all_analyzed'] = False
            coordinator['rotation_mode'] = False
        
        # Start video analysis in background
        threading.Thread(target=analyze_video_traffic, args=(lane, filepath), daemon=True).start()
        
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
                        print(f"❌ Could not open video for {lane_name}")
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
                # Reset coordinator state
                coordinator['analysis_phase'] = True
                coordinator['all_analyzed'] = False
                coordinator['rotation_mode'] = False
                coordinator['active_lane'] = None
                coordinator['cycle_count'] = 0
                coordinator['green_timer'] = 0
                
                # Start processing threads for all lanes
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
                    'cycle_count': coordinator['cycle_count'],
                    'ml_enabled': coordinator['ml_enabled'],
                    'ml_accuracy': coordinator['ml_accuracy'],
                    'analysis_phase': coordinator['analysis_phase'],
                    'rotation_mode': coordinator['rotation_mode'],
                    'all_analyzed': coordinator['all_analyzed']
                }
            }
            
            for lane_name, lane_data in lanes_system.items():
                lane_info = {
                    'frame_count': lane_data['frame_count'],
                    'vehicle_count': lane_data['vehicle_count'],
                    'traffic_density': lane_data['traffic_density'],
                    'signal_state': lane_data['signal_state'],
                    'is_active': lane_data['is_active'],
                    'is_running': lane_data['is_running'],
                    'analyzed': lane_data['analyzed'],
                    'traffic_score': lane_data['traffic_score'],
                    'video_length': lane_data['video_length']
                }
                
                # Show video frame for all lanes (both active and inactive)
                if lane_data['current_frame'] is not None:
                    # Convert frame to base64
                    frame_rgb = cv2.cvtColor(lane_data['current_frame'], cv2.COLOR_BGR2RGB)
                    
                    # Add overlay for inactive lanes in rotation mode
                    if coordinator['rotation_mode'] and not lane_data['is_active']:
                        h, w = frame_rgb.shape[:2]
                        overlay = frame_rgb.copy()
                        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
                        frame_rgb = cv2.addWeighted(overlay, 0.6, frame_rgb, 0.4, 0)
                        
                        # Add "WAITING" overlay
                        cv2.putText(frame_rgb, "WAITING", (w//2 - 60, h//2), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3)
                        cv2.putText(frame_rgb, f"Vehicles: {lane_data['vehicle_count']}", (w//2 - 80, h//2 + 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        cv2.putText(frame_rgb, f"Score: {lane_data['traffic_score']:.1f}", (w//2 - 60, h//2 + 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
                        
                        # Add signal indicator
                        cv2.circle(frame_rgb, (50, 50), 20, (0, 0, 255), -1)
                        cv2.putText(frame_rgb, "STOP", (35, 90), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    elif coordinator['rotation_mode'] and lane_data['is_active']:
                        # Add "ACTIVE" overlay for active lane
                        h, w = frame_rgb.shape[:2]
                        cv2.putText(frame_rgb, "🟢 ACTIVE", (w//2 - 60, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                        cv2.putText(frame_rgb, f"Vehicles: {lane_data['vehicle_count']}", (w//2 - 80, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        
                        # Add signal indicator
                        cv2.circle(frame_rgb, (50, 50), 20, (0, 255, 0), -1)
                        cv2.putText(frame_rgb, "GO", (35, 90), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    _, buffer = cv2.imencode('.jpg', frame_rgb)
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    lane_info['frame'] = frame_b64
                
                response_data['lanes'][lane_name] = lane_info
            
            return jsonify(response_data)
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_ml_report')
def get_ml_report():
    """Get Machine Learning performance report"""
    try:
        report = traffic_optimizer.get_performance_report()
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/toggle_ml', methods=['POST'])
def toggle_ml():
    """Toggle Machine Learning on/off"""
    try:
        coordinator['ml_enabled'] = not coordinator['ml_enabled']
        status = "enabled" if coordinator['ml_enabled'] else "disabled"
        return jsonify({'success': True, 'ml_enabled': coordinator['ml_enabled'], 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def traffic_coordinator():
    """Main traffic coordination logic"""
    while True:
        try:
            with system_lock:
                current_time = time.time()
                
                # Check if it's time to analyze traffic
                if current_time - coordinator['last_analysis'] >= coordinator['analysis_interval']:
                    if coordinator['analysis_phase']:
                        # Check if all videos are analyzed
                        all_analyzed = all(lanes_system[lane]['analyzed'] for lane in lanes_system if lanes_system[lane]['video_path'])
                        if all_analyzed:
                            coordinator['analysis_phase'] = False
                            coordinator['all_analyzed'] = True
                            coordinator['rotation_mode'] = True
                            print("🎯 All videos analyzed! Starting systematic rotation...")
                            start_systematic_rotation()
                    else:
                        analyze_all_lanes()
                    coordinator['last_analysis'] = current_time
                
                # Check if it's time to switch lanes (only in rotation mode)
                if coordinator['rotation_mode'] and coordinator['green_timer'] <= 0:
                    rotate_to_next_lane()
                    coordinator['last_switch'] = current_time
                    coordinator['cycle_count'] += 1
                elif coordinator['rotation_mode']:
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
    """Switch to specific lane with ML optimization"""
    if not lane_name or lane_name == coordinator['active_lane']:
        return
    
    print(f"🤖 Switching from {coordinator['active_lane']} to {lane_name}")
    
    # Calculate wait time for previous lane
    previous_lane_wait = 0
    if coordinator['active_lane']:
        previous_lane_data = lanes_system[coordinator['active_lane']]
        previous_lane_wait = coordinator.get('total_wait_time', 0)
        
        # Record performance data for ML
        efficiency = calculate_lane_efficiency(coordinator['active_lane'])
        traffic_optimizer.record_traffic_data(
            coordinator['active_lane'],
            previous_lane_data['vehicle_count'],
            coordinator['green_timer'],
            previous_lane_wait,
            efficiency
        )
    
    # Deactivate current lane
    if coordinator['active_lane']:
        lanes_system[coordinator['active_lane']]['signal_state'] = 'red'
        lanes_system[coordinator['active_lane']]['is_active'] = False
    
    # Activate new lane
    coordinator['active_lane'] = lane_name
    lanes_system[lane_name]['signal_state'] = 'green'
    lanes_system[lane_name]['is_active'] = True
    
    # Get ML-optimized green time
    vehicle_count = lanes_system[lane_name]['vehicle_count']
    
    if coordinator['ml_enabled']:
        # Use ML optimization
        optimized_time = traffic_optimizer.get_optimal_green_time(vehicle_count, lane_name)
        coordinator['green_timer'] = optimized_time
        print(f"🤖 ML Optimized green time: {optimized_time}s for {vehicle_count} vehicles")
    else:
        # Use rule-based timing
        if vehicle_count <= 2:
            coordinator['green_timer'] = coordinator['min_green_time']
        elif vehicle_count <= 5:
            coordinator['green_timer'] = coordinator['min_green_time'] + 5
        elif vehicle_count <= 10:
            coordinator['green_timer'] = coordinator['min_green_time'] + 10
        else:
            coordinator['green_timer'] = coordinator['max_green_time']
        print(f"📊 Rule-based green time: {coordinator['green_timer']}s for {vehicle_count} vehicles")
    
    # Update ML accuracy
    coordinator['ml_accuracy'] = traffic_optimizer.calculate_model_accuracy()

def calculate_lane_efficiency(lane_name):
    """Calculate efficiency score for a lane"""
    lane_data = lanes_system[lane_name]
    
    if not lane_data['is_running'] or lane_data['vehicle_count'] == 0:
        return 0.5  # Default efficiency
    
    # Efficiency based on vehicle throughput vs time
    vehicles_processed = lane_data['vehicle_count']
    time_used = coordinator['green_timer']
    
    if time_used > 0:
        throughput = vehicles_processed / time_used
        # Normalize efficiency (0-1 scale)
        efficiency = min(1.0, throughput / 0.5)  # 0.5 vehicles/second is good
        return max(0.1, efficiency)  # Minimum 0.1 efficiency
    
    return 0.5

def analyze_video_traffic(lane_name, video_path):
    """Analyze video traffic density and calculate traffic score"""
    try:
        print(f"🔍 Analyzing traffic for {lane_name} lane...")
        
        # Open video for analysis
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video for {lane_name}")
            return
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_length = total_frames / fps if fps > 0 else 0
        
        # Import detector
        from vehicle_detector import VehicleDetector
        detector = VehicleDetector()
        
        # Sample frames for analysis (every 30th frame)
        sample_interval = max(1, total_frames // 30)
        total_vehicles = 0
        samples_analyzed = 0
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % sample_interval == 0:
                # Detect vehicles in sample frame
                detections = detector.detect_vehicles(frame)
                vehicle_count = len(detections)
                total_vehicles += vehicle_count
                samples_analyzed += 1
                
                # Draw detections for analysis visualization
                frame = detector.draw_detections(frame, detections)
                
                # Save sample frame for display
                if frame_count == sample_interval:  # First sample
                    with system_lock:
                        lanes_system[lane_name]['current_frame'] = frame.copy()
            
            frame_count += 1
            
            # Limit analysis time
            if frame_count > 1000:  # Analyze max 1000 frames
                break
        
        cap.release()
        
        # Calculate traffic metrics
        avg_vehicles_per_sample = total_vehicles / samples_analyzed if samples_analyzed > 0 else 0
        estimated_total_vehicles = avg_vehicles_per_sample * (total_frames / sample_interval)
        
        # Calculate traffic score (0-100) based on density
        traffic_score = min(100, (avg_vehicles_per_sample / 10) * 100)  # Scale to 0-100
        
        # Update lane data
        with system_lock:
            lanes_system[lane_name]['video_length'] = video_length
            lanes_system[lane_name]['total_frames'] = total_frames
            lanes_system[lane_name]['fps'] = fps
            lanes_system[lane_name]['vehicle_count'] = int(estimated_total_vehicles)
            lanes_system[lane_name]['traffic_score'] = traffic_score
            lanes_system[lane_name]['analyzed'] = True
            
            # Update traffic density
            if avg_vehicles_per_sample <= 2:
                lanes_system[lane_name]['traffic_density'] = 'Low'
            elif avg_vehicles_per_sample <= 5:
                lanes_system[lane_name]['traffic_density'] = 'Medium'
            elif avg_vehicles_per_sample <= 10:
                lanes_system[lane_name]['traffic_density'] = 'High'
            else:
                lanes_system[lane_name]['traffic_density'] = 'Critical'
        
        print(f"✅ {lane_name} analysis complete:")
        print(f"   📹 Video length: {video_length:.1f}s")
        print(f"   🚗 Estimated vehicles: {int(estimated_total_vehicles)}")
        print(f"   📊 Traffic score: {traffic_score:.1f}/100")
        print(f"   📈 Density: {lanes_system[lane_name]['traffic_density']}")
        
    except Exception as e:
        print(f"❌ Error analyzing {lane_name}: {e}")
        with system_lock:
            lanes_system[lane_name]['analyzed'] = True  # Mark as analyzed even if failed
            lanes_system[lane_name]['traffic_score'] = 0

def start_systematic_rotation():
    """Start systematic rotation based on traffic analysis"""
    # Sort lanes by traffic score (highest first)
    lane_scores = []
    for lane_name, lane_data in lanes_system.items():
        if lane_data['video_path'] and lane_data['analyzed']:
            lane_scores.append((lane_name, lane_data['traffic_score']))
    
    # Sort by score descending
    lane_scores.sort(key=lambda x: x[1], reverse=True)
    
    print("🔄 Lane priority order (by traffic density):")
    for i, (lane, score) in enumerate(lane_scores):
        print(f"   {i+1}. {lane.upper()}: {score:.1f}/100")
    
    # Start with highest traffic lane
    if lane_scores:
        first_lane = lane_scores[0][0]
        activate_lane_with_timing(first_lane)

def rotate_to_next_lane():
    """Rotate to next lane based on traffic priority"""
    # Get all analyzed lanes
    analyzed_lanes = []
    for lane_name, lane_data in lanes_system.items():
        if lane_data['video_path'] and lane_data['analyzed']:
            analyzed_lanes.append((lane_name, lane_data['traffic_score']))
    
    # Sort by traffic score
    analyzed_lanes.sort(key=lambda x: x[1], reverse=True)
    
    if not analyzed_lanes:
        return
    
    # Find current lane in priority list
    current_index = 0
    for i, (lane, score) in enumerate(analyzed_lanes):
        if lane == coordinator['active_lane']:
            current_index = i
            break
    
    # Move to next lane in priority
    next_index = (current_index + 1) % len(analyzed_lanes)
    next_lane = analyzed_lanes[next_index][0]
    
    activate_lane_with_timing(next_lane)

def activate_lane_with_timing(lane_name):
    """Activate a lane with calculated timing based on traffic and video length"""
    if not lane_name or lane_name == coordinator['active_lane']:
        return
    
    lane_data = lanes_system[lane_name]
    
    # Deactivate current lane
    if coordinator['active_lane']:
        lanes_system[coordinator['active_lane']]['signal_state'] = 'red'
        lanes_system[coordinator['active_lane']]['is_active'] = False
        print(f"🔴 Deactivating {coordinator['active_lane']} lane")
    
    # Activate new lane
    coordinator['active_lane'] = lane_name
    lanes_system[lane_name]['signal_state'] = 'green'
    lanes_system[lane_name]['is_active'] = True
    print(f"🟢 Activating {lane_name} lane")
    
    # Calculate green time based on traffic score and video length
    traffic_score = lane_data['traffic_score']
    video_length = lane_data['video_length']
    
    # Base time calculation
    if coordinator['ml_enabled']:
        # Use ML optimization
        optimized_time = traffic_optimizer.get_optimal_green_time(lane_data['vehicle_count'], lane_name)
        base_time = optimized_time
    else:
        # Rule-based timing
        if traffic_score >= 80:
            base_time = 30  # High traffic
        elif traffic_score >= 60:
            base_time = 25  # Medium-high traffic
        elif traffic_score >= 40:
            base_time = 20  # Medium traffic
        elif traffic_score >= 20:
            base_time = 15  # Low-medium traffic
        else:
            base_time = 10  # Low traffic
    
    # Adjust based on video length (longer videos get more time)
    if video_length > 0:
        video_factor = min(1.5, video_length / 30)  # Scale by video length, max 1.5x
        final_time = base_time * video_factor
    else:
        final_time = base_time
    
    # Ensure bounds
    final_time = max(coordinator['min_green_time'], min(coordinator['max_green_time'], final_time))
    
    coordinator['green_timer'] = final_time
    
    print(f"⏱️ {lane_name} green time: {final_time:.1f}s (Traffic: {traffic_score:.1f}, Video: {video_length:.1f}s)")

def process_lane_video_coordinated(lane_name):
    """Process video for coordinated system with controlled playback"""
    lane_data = lanes_system[lane_name]
    
    while lane_data['is_running']:
        try:
            if lane_data['cap'] and lane_data['is_running']:
                ret, frame = lane_data['cap'].read()
                if not ret:
                    # End of video - reset to beginning for continuous playback
                    lane_data['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = lane_data['cap'].read()
                    if not ret:
                        lane_data['is_running'] = False
                        break
                
                # Always process frame to keep video running
                if lane_data['detector']:
                    # Detect vehicles
                    detections = lane_data['detector'].detect_vehicles(frame)
                    lane_data['vehicle_count'] = len(detections)
                    
                    # Draw detections on frame
                    frame = lane_data['detector'].draw_detections(frame, detections)
                
                # Draw lane info
                frame = draw_coordinated_lane_info(frame, lane_name, lane_data)
                lane_data['current_frame'] = frame
                
                # Update frame count
                lane_data['frame_count'] += 1
                
                # Record performance data for ML (only in rotation mode)
                if coordinator['ml_enabled'] and coordinator['rotation_mode'] and coordinator['cycle_count'] > 0:
                    efficiency = calculate_lane_efficiency(lane_name)
                    traffic_optimizer.record_traffic_data(
                        lane_name,
                        lane_data['vehicle_count'],
                        coordinator['green_timer'],
                        0,  # No wait time in rotation mode
                        efficiency
                    )
                
                # Handle video position for inactive lanes
                if not lane_data['is_active'] and coordinator['rotation_mode']:
                    # For inactive lanes, slowly advance video to prevent getting stuck
                    current_pos = lane_data['cap'].get(cv2.CAP_PROP_POS_FRAMES)
                    total_frames = lane_data['cap'].get(cv2.CAP_PROP_FRAME_COUNT)
                    
                    # Advance video slowly (every 10 frames) for inactive lanes
                    if lane_data['frame_count'] % 10 == 0 and total_frames > 0:
                        next_pos = (current_pos + 1) % total_frames
                        lane_data['cap'].set(cv2.CAP_PROP_POS_FRAMES, next_pos)
                
                lane_data['last_processed'] = time.time()
                
        except Exception as e:
            print(f"Error processing {lane_name}: {e}")
            lane_data['is_running'] = False
            break
        
        time.sleep(0.033)  # Process at ~30 FPS for smoother video

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
