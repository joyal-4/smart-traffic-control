print("Testing imports...")

try:
    import cv2
    print("✓ cv2 imported successfully")
    print(f"OpenCV version: {cv2.__version__}")
except Exception as e:
    print(f"✗ Error importing cv2: {e}")

try:
    import numpy as np
    print("✓ numpy imported successfully")
except Exception as e:
    print(f"✗ Error importing numpy: {e}")

try:
    from traffic_lane_manager import TrafficLaneManager
    print("✓ TrafficLaneManager imported successfully")
except Exception as e:
    print(f"✗ Error importing TrafficLaneManager: {e}")

try:
    from traffic_signal_controller import TrafficSignalController
    print("✓ TrafficSignalController imported successfully")
except Exception as e:
    print(f"✗ Error importing TrafficSignalController: {e}")

print("Testing basic cv2 functionality...")
try:
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (10, 10), (50, 50), (255, 0, 0), -1)
    print("✓ cv2.rectangle works")
except Exception as e:
    print(f"✗ Error with cv2.rectangle: {e}")

print("Testing TrafficLaneManager instantiation...")
try:
    manager = TrafficLaneManager(640, 480)
    print("✓ TrafficLaneManager created successfully")
except Exception as e:
    print(f"✗ Error creating TrafficLaneManager: {e}")

print("Testing TrafficLaneManager.draw_lanes...")
try:
    manager = TrafficLaneManager(640, 480)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = manager.draw_lanes(frame)
    print("✓ TrafficLaneManager.draw_lanes works")
except Exception as e:
    print(f"✗ Error with TrafficLaneManager.draw_lanes: {e}")
    import traceback
    traceback.print_exc()
