#!/usr/bin/env python3
"""Debug pose overlay to see what's happening."""

import cv2
import json
import sys

def debug_pose_overlay(video_path: str, pose_data_path: str):
    """Debug what's in the pose data."""
    
    # Load pose data
    with open(pose_data_path, 'r') as f:
        pose_data = json.load(f)
    
    print("Pose data keys:", pose_data.keys())
    
    # Check pose landmarks
    pose_landmarks = pose_data.get('pose_landmarks', {})
    print(f"Number of frames with pose data: {len(pose_landmarks)}")
    
    # Check if it's a list or dict
    if isinstance(pose_landmarks, list):
        print("pose_landmarks is a list")
        if len(pose_landmarks) > 0:
            print(f"First frame data: {pose_landmarks[0].keys()}")
            print(f"Number of landmarks in frame 0: {len(pose_landmarks[0].get('landmarks', []))}")
    else:
        print("pose_landmarks is a dict")
    
    # Check swing phases
    swing_phases = pose_data.get('swing_phases', {})
    print(f"Swing phases: {swing_phases.keys()}")
    for phase, data in swing_phases.items():
        print(f"  {phase}: frames {data.get('start', 0)} to {data.get('end', 0)}")
    
    # Test video reading
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"\nVideo info: {width}x{height} @ {fps}fps")
    
    # Test drawing on first frame
    ret, frame = cap.read()
    if ret:
        # Try to draw something simple
        cv2.circle(frame, (width//2, height//2), 50, (0, 255, 0), -1)
        cv2.putText(frame, "TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)
        
        # Save test frame
        cv2.imwrite("test_frame.jpg", frame)
        print("Saved test_frame.jpg with circle and text")
    
    cap.release()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_pose_overlay.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    pose_data_path = video_path.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    
    debug_pose_overlay(video_path, pose_data_path)