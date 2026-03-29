import numpy as np
import json
import time
from datetime import datetime, timedelta
from collections import deque
import pickle
import os

class TrafficOptimizer:
    """Machine Learning Traffic Signal Optimizer"""
    
    def __init__(self):
        self.model_data = {
            'traffic_history': deque(maxlen=1000),  # Store last 1000 data points
            'timing_patterns': {},  # Learned optimal timings
            'performance_metrics': deque(maxlen=100),  # Recent performance
            'learning_rate': 0.01,
            'model_file': 'traffic_model.pkl'
        }
        
        # Load existing model if available
        self.load_model()
        
        # Initialize with some basic patterns
        self.initialize_patterns()
    
    def initialize_patterns(self):
        """Initialize basic timing patterns"""
        base_patterns = {
            'low_traffic': {'vehicles': 5, 'green_time': 10, 'efficiency': 0.8},
            'medium_traffic': {'vehicles': 15, 'green_time': 20, 'efficiency': 0.7},
            'high_traffic': {'vehicles': 30, 'green_time': 35, 'efficiency': 0.6},
            'critical_traffic': {'vehicles': 50, 'green_time': 45, 'efficiency': 0.5}
        }
        
        for pattern, data in base_patterns.items():
            self.model_data['timing_patterns'][pattern] = data
    
    def record_traffic_data(self, lane_name, vehicle_count, green_time, wait_time, efficiency):
        """Record traffic data for learning"""
        timestamp = datetime.now()
        
        data_point = {
            'timestamp': timestamp,
            'lane': lane_name,
            'vehicle_count': vehicle_count,
            'green_time': green_time,
            'wait_time': wait_time,
            'efficiency': efficiency,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday()
        }
        
        self.model_data['traffic_history'].append(data_point)
        
        # Update performance metrics
        self.model_data['performance_metrics'].append({
            'timestamp': timestamp,
            'efficiency': efficiency,
            'avg_wait_time': wait_time
        })
        
        # Trigger learning every 50 data points
        if len(self.model_data['traffic_history']) % 50 == 0:
            self.optimize_patterns()
    
    def optimize_patterns(self):
        """Optimize timing patterns based on collected data"""
        if len(self.model_data['traffic_history']) < 20:
            return
        
        # Group recent data by traffic level
        recent_data = list(self.model_data['traffic_history'])[-100:]
        
        # Analyze patterns and optimize
        traffic_groups = self.group_by_traffic_level(recent_data)
        
        for level, data in traffic_groups.items():
            if len(data) >= 5:  # Need enough data for optimization
                optimal_time = self.calculate_optimal_green_time(data)
                
                if level in self.model_data['timing_patterns']:
                    old_efficiency = self.model_data['timing_patterns'][level]['efficiency']
                    new_efficiency = np.mean([d['efficiency'] for d in data])
                    
                    # Update if new pattern is better
                    if new_efficiency > old_efficiency:
                        self.model_data['timing_patterns'][level] = {
                            'vehicles': np.mean([d['vehicle_count'] for d in data]),
                            'green_time': optimal_time,
                            'efficiency': new_efficiency,
                            'sample_size': len(data)
                        }
        
        # Save updated model
        self.save_model()
    
    def group_by_traffic_level(self, data):
        """Group data by traffic level"""
        groups = {
            'low_traffic': [],
            'medium_traffic': [],
            'high_traffic': [],
            'critical_traffic': []
        }
        
        for point in data:
            vehicles = point['vehicle_count']
            if vehicles <= 5:
                groups['low_traffic'].append(point)
            elif vehicles <= 15:
                groups['medium_traffic'].append(point)
            elif vehicles <= 30:
                groups['high_traffic'].append(point)
            else:
                groups['critical_traffic'].append(point)
        
        return groups
    
    def calculate_optimal_green_time(self, data):
        """Calculate optimal green time using weighted average"""
        if not data:
            return 20  # Default
        
        # Weight by efficiency (higher efficiency = better timing)
        weights = [d['efficiency'] for d in data]
        times = [d['green_time'] for d in data]
        
        if sum(weights) == 0:
            return np.mean(times)
        
        optimal_time = np.average(times, weights=weights)
        
        # Add some learning adjustment
        avg_efficiency = np.mean(weights)
        if avg_efficiency < 0.6:  # Poor performance
            optimal_time *= 1.1  # Increase time slightly
        elif avg_efficiency > 0.8:  # Good performance
            optimal_time *= 0.95  # Decrease time slightly
        
        # Ensure reasonable bounds
        optimal_time = max(8, min(60, optimal_time))
        
        return round(optimal_time, 1)
    
    def get_optimal_green_time(self, vehicle_count, lane_name=None):
        """Get ML-optimized green time for current traffic"""
        # Determine traffic level
        if vehicle_count <= 5:
            level = 'low_traffic'
        elif vehicle_count <= 15:
            level = 'medium_traffic'
        elif vehicle_count <= 30:
            level = 'high_traffic'
        else:
            level = 'critical_traffic'
        
        # Get base timing from learned patterns
        if level in self.model_data['timing_patterns']:
            pattern = self.model_data['timing_patterns'][level]
            base_time = pattern['green_time']
        else:
            # Fallback to rule-based timing
            base_time = self.rule_based_timing(vehicle_count)
        
        # Apply time-based adjustments
        current_hour = datetime.now().hour
        time_factor = self.get_time_factor(current_hour)
        
        # Apply lane-specific adjustments if we have data
        lane_factor = self.get_lane_factor(lane_name, vehicle_count)
        
        # Calculate final optimized time
        optimized_time = base_time * time_factor * lane_factor
        
        # Ensure bounds
        optimized_time = max(8, min(60, optimized_time))
        
        return round(optimized_time, 1)
    
    def rule_based_timing(self, vehicle_count):
        """Fallback rule-based timing"""
        if vehicle_count <= 2:
            return 10
        elif vehicle_count <= 5:
            return 15
        elif vehicle_count <= 10:
            return 25
        elif vehicle_count <= 20:
            return 35
        else:
            return 45
    
    def get_time_factor(self, hour):
        """Get time-based adjustment factor"""
        # Rush hours: 7-9 AM, 5-7 PM
        if (7 <= hour <= 9) or (17 <= hour <= 19):
            return 1.2  # 20% more time during rush hours
        # Late night: 10 PM - 5 AM
        elif hour >= 22 or hour <= 5:
            return 0.8  # 20% less time during low traffic
        # Normal hours
        else:
            return 1.0
    
    def get_lane_factor(self, lane_name, vehicle_count):
        """Get lane-specific adjustment factor"""
        if not lane_name:
            return 1.0
        
        # Analyze historical performance for this lane
        lane_data = [d for d in self.model_data['traffic_history'] 
                     if d['lane'] == lane_name and 
                     abs(d['vehicle_count'] - vehicle_count) <= 5]
        
        if len(lane_data) >= 3:
            avg_efficiency = np.mean([d['efficiency'] for d in lane_data])
            
            # Adjust based on historical performance
            if avg_efficiency > 0.8:
                return 0.95  # This lane performs well, can use less time
            elif avg_efficiency < 0.6:
                return 1.1   # This lane needs more time
            else:
                return 1.0
        
        return 1.0
    
    def get_performance_report(self):
        """Get current performance metrics"""
        if not self.model_data['performance_metrics']:
            return "No data available yet"
        
        recent_metrics = list(self.model_data['performance_metrics'])[-20:]
        
        avg_efficiency = np.mean([m['efficiency'] for m in recent_metrics])
        avg_wait_time = np.mean([m['avg_wait_time'] for m in recent_metrics])
        
        total_cycles = len(self.model_data['traffic_history'])
        learned_patterns = len(self.model_data['timing_patterns'])
        
        report = {
            'total_cycles': total_cycles,
            'learned_patterns': learned_patterns,
            'avg_efficiency': round(avg_efficiency, 3),
            'avg_wait_time': round(avg_wait_time, 1),
            'model_accuracy': self.calculate_model_accuracy()
        }
        
        return report
    
    def calculate_model_accuracy(self):
        """Calculate how well the model is performing"""
        if len(self.model_data['performance_metrics']) < 10:
            return 0.5  # Default accuracy
        
        recent_metrics = list(self.model_data['performance_metrics'])[-10:]
        efficiencies = [m['efficiency'] for m in recent_metrics]
        
        # Accuracy based on efficiency improvement
        if len(efficiencies) >= 2:
            improvement = efficiencies[-1] - efficiencies[0]
            accuracy = 0.5 + (improvement * 2)  # Scale to 0-1 range
            return max(0, min(1, accuracy))
        
        return 0.5
    
    def save_model(self):
        """Save the trained model"""
        try:
            with open(self.model_data['model_file'], 'wb') as f:
                pickle.dump(self.model_data, f)
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self):
        """Load existing trained model"""
        try:
            if os.path.exists(self.model_data['model_file']):
                with open(self.model_data['model_file'], 'rb') as f:
                    loaded_data = pickle.load(f)
                    self.model_data.update(loaded_data)
                    print("✅ ML Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("🤖 Starting with fresh ML model")
    
    def export_training_data(self):
        """Export training data for analysis"""
        data = {
            'traffic_history': list(self.model_data['traffic_history']),
            'timing_patterns': self.model_data['timing_patterns'],
            'performance_metrics': list(self.model_data['performance_metrics']),
            'export_timestamp': datetime.now().isoformat()
        }
        
        filename = f"traffic_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return filename
