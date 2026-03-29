import cv2
import numpy as np
import time
from traffic_lane_manager import TrafficLaneManager
from traffic_signal_controller import TrafficSignalController

def test_basic_functionality():
    print("Starting minimal test...")
    
    # Create frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (80, 80, 80)  # Gray background
    
    # Create managers
    lane_manager = TrafficLaneManager(640, 480)
    signal_controller = TrafficSignalController()
    
    print("Managers created successfully")
    
    # Test lane drawing
    try:
        frame = lane_manager.draw_lanes(frame)
        print("✓ Lane drawing works")
    except Exception as e:
        print(f"✗ Lane drawing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test signal drawing
    try:
        frame = signal_controller.draw_signals(frame, lane_manager)
        print("✓ Signal drawing works")
    except Exception as e:
        print(f"✗ Signal drawing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test with signal controller running
    try:
        signal_controller.start()
        print("✓ Signal controller started")
        
        time.sleep(2)  # Let it run for 2 seconds
        
        frame = signal_controller.draw_signals(frame, lane_manager)
        print("✓ Signal drawing with controller running works")
        
        signal_controller.stop()
        print("✓ Signal controller stopped")
        
    except Exception as e:
        print(f"✗ Signal controller test failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("✓ All tests passed!")

if __name__ == "__main__":
    test_basic_functionality()
