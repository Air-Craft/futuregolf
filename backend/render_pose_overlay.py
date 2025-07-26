#!/usr/bin/env python3
"""
Render MediaPipe pose data as overlay on video.
Creates the "sciencey" visualization with skeleton and angle measurements.
"""

import cv2
import json
import numpy as np
import sys
import os
from typing import Dict, List, Tuple
import mediapipe as mp

# MediaPipe drawing utilities
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

def load_pose_data(pose_json_path: str) -> Dict:
    """Load pose analysis data from JSON."""
    with open(pose_json_path, 'r') as f:
        return json.load(f)

def draw_angle_arc(img, center, angle, radius=50, color=(0, 255, 0), thickness=2):
    """Draw an arc showing the angle measurement."""
    # Draw the arc
    axes = (radius, radius)
    start_angle = -90  # Start from vertical
    end_angle = start_angle + angle
    cv2.ellipse(img, center, axes, 0, start_angle, end_angle, color, thickness)
    
    # Draw angle text
    text = f"{angle:.1f}°"
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 0.6, 2)[0]
    text_x = center[0] - text_size[0] // 2
    text_y = center[1] + radius + 20
    cv2.putText(img, text, (text_x, text_y), font, 0.6, color, 2, cv2.LINE_AA)

def get_color_for_status(status: str) -> Tuple[int, int, int]:
    """Get color based on analysis status."""
    if status == 'green':
        return (0, 255, 0)  # Green for good
    elif status == 'red':
        return (0, 0, 255)  # Red for needs work
    else:
        return (255, 255, 0)  # Yellow for neutral

def render_pose_overlay(video_path: str, pose_data_path: str, output_path: str):
    """Render video with MediaPipe pose overlay."""
    
    # Load pose data
    pose_data = load_pose_data(pose_data_path)
    
    # Extract key data
    frame_poses = pose_data.get('pose_landmarks', [])
    angle_analysis = pose_data.get('angle_analysis', {})
    swing_phases = pose_data.get('swing_phases', {})
    
    print(f"Loaded {len(frame_poses)} frames of pose data")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_idx = 0
    
    # Create pose connections for drawing skeleton
    connections = mp_pose.POSE_CONNECTIONS
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Get pose data for this frame
        if frame_idx < len(frame_poses):
            frame_pose = frame_poses[frame_idx]
            landmarks = frame_pose.get('landmarks', [])
            
            if landmarks:
                # Draw skeleton connections
                for connection in connections:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    
                    if start_idx < len(landmarks) and end_idx < len(landmarks):
                        start = landmarks[start_idx]
                        end = landmarks[end_idx]
                        
                        # Convert normalized coordinates to pixel coordinates
                        start_point = (int(start['x'] * width), int(start['y'] * height))
                        end_point = (int(end['x'] * width), int(end['y'] * height))
                        
                        # Draw connection line
                        cv2.line(frame, start_point, end_point, (0, 255, 255), 2)
                
                # Draw landmark points
                for i, landmark in enumerate(landmarks):
                    x = int(landmark['x'] * width)
                    y = int(landmark['y'] * height)
                    
                    # Draw larger points for key joints
                    if i in [11, 12, 23, 24]:  # Shoulders and hips
                        cv2.circle(frame, (x, y), 8, (255, 0, 0), -1)
                    else:
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            
        # Determine current swing phase
        current_phase = None
        current_time = frame_idx / fps  # Convert frame to seconds
        for phase, time_range in swing_phases.items():
            if time_range['start'] <= current_time <= time_range['end']:
                current_phase = phase
                break
            
            # Draw phase and angle info
            if current_phase:
                # Phase text
                phase_text = f"Phase: {current_phase.replace('_', ' ').title()}"
                cv2.putText(frame, phase_text, (20, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Spine angle for this phase
                if current_phase in angle_analysis.get('spine_angle', {}):
                    spine_data = angle_analysis['spine_angle'][current_phase]
                    angle = spine_data['angle']
                    status = spine_data['status']
                    color = get_color_for_status(status)
                    
                    # Draw spine angle visualization
                    if landmarks and len(landmarks) > 24:
                        # Get shoulder and hip centers
                        left_shoulder = landmarks[11]
                        right_shoulder = landmarks[12]
                        left_hip = landmarks[23]
                        right_hip = landmarks[24]
                        
                        shoulder_center = (
                            int((left_shoulder['x'] + right_shoulder['x']) * width / 2),
                            int((left_shoulder['y'] + right_shoulder['y']) * height / 2)
                        )
                        hip_center = (
                            int((left_hip['x'] + right_hip['x']) * width / 2),
                            int((left_hip['y'] + right_hip['y']) * height / 2)
                        )
                        
                        # Draw spine line
                        cv2.line(frame, shoulder_center, hip_center, color, 4)
                        
                        # Draw angle arc at hip
                        draw_angle_arc(frame, hip_center, angle, color=color)
                    
                    # Angle text in corner
                    angle_text = f"Spine Angle: {angle:.1f}°"
                    cv2.putText(frame, angle_text, (20, 80), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
        
        # Add MediaPipe branding
        cv2.putText(frame, "MediaPipe Pose Analysis", (width - 250, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Write frame
        out.write(frame)
        frame_idx += 1
    
    # Release everything
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print(f"✅ Pose overlay video created: {output_path}")
    print(f"   - Rendered {frame_idx} frames with skeleton overlay")
    print(f"   - Showing spine angles and phase detection")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_pose_overlay.py <video_path>")
        print("   Expects matching _pose.json file to exist")
        sys.exit(1)
    
    video_path = sys.argv[1]
    pose_data_path = video_path.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    output_path = video_path.replace('.mp4', '_pose_overlay.mp4').replace('.mov', '_pose_overlay.mp4')
    
    if not os.path.exists(pose_data_path):
        print(f"❌ Pose data not found: {pose_data_path}")
        print("   Run analyze_full_pipeline.py first to generate pose data")
        sys.exit(1)
    
    render_pose_overlay(video_path, pose_data_path, output_path)