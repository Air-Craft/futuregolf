#!/usr/bin/env python3
"""Test MediaPipe installation on Apple Silicon."""
import sys
import platform

print("System Info:")
print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Machine: {platform.machine()}")
print(f"Processor: {platform.processor()}")
print()

# Try importing MediaPipe
try:
    import mediapipe as mp
    print("✅ MediaPipe imported successfully!")
    print(f"   Version: {mp.__version__ if hasattr(mp, '__version__') else 'Unknown'}")
    
    # Try initializing pose
    try:
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(static_image_mode=True)
        print("✅ MediaPipe Pose initialized successfully!")
        
        # Try with a simple test
        import numpy as np
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        results = pose.process(test_image)
        print("✅ MediaPipe can process images!")
        
    except Exception as e:
        print(f"❌ Error initializing Pose: {e}")
        
except ImportError as e:
    print(f"❌ Failed to import MediaPipe: {e}")
    print("\nTrying to install MediaPipe for Apple Silicon...")
    print("Run: pip install mediapipe-silicon")
    print("Or try: pip install mediapipe --upgrade")