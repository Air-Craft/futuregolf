#!/usr/bin/env python3
"""
Render full analysis: MediaPipe skeleton + Gemini coaching overlay.
Creates the complete "sciencey" golf analysis video.
"""

import cv2
import json
import numpy as np
import sys
import os
from typing import Dict, List, Tuple
import mediapipe as mp
import textwrap

# MediaPipe drawing utilities
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

def load_analysis_data(video_path: str) -> Tuple[Dict, Dict]:
    """Load both pose and AI analysis data."""
    pose_path = video_path.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    analysis_path = video_path.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    
    with open(pose_path, 'r') as f:
        pose_data = json.load(f)
    
    with open(analysis_path, 'r') as f:
        ai_data = json.load(f)
    
    return pose_data, ai_data

def get_color_for_status(status: str) -> Tuple[int, int, int]:
    """Get color based on analysis status."""
    if status == 'green':
        return (0, 255, 0)  # Green for good
    elif status == 'red':
        return (0, 0, 255)  # Red for needs work
    else:
        return (255, 255, 0)  # Yellow for neutral

def draw_text_with_background(img, text, pos, font_scale=0.7, thickness=2, 
                            text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    """Draw text with a background for better readability."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Draw background rectangle
    x, y = pos
    cv2.rectangle(img, (x - 5, y - text_height - 5), 
                  (x + text_width + 5, y + baseline + 5), bg_color, -1)
    
    # Draw text
    cv2.putText(img, text, pos, font, font_scale, text_color, thickness, cv2.LINE_AA)

def draw_multiline_text(img, lines, start_pos, font_scale=0.6, line_spacing=25,
                       text_color=(255, 255, 255), bg_color=(0, 0, 0, 180)):
    """Draw multiple lines of text with semi-transparent background."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    x, y = start_pos
    
    # Calculate total height needed
    total_height = len(lines) * line_spacing + 10
    max_width = 0
    
    for line in lines:
        (w, h), _ = cv2.getTextSize(line, font, font_scale, 1)
        max_width = max(max_width, w)
    
    # Create overlay for semi-transparent background
    overlay = img.copy()
    cv2.rectangle(overlay, (x - 10, y - 25), 
                  (x + max_width + 10, y + total_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
    
    # Draw each line
    for i, line in enumerate(lines):
        line_y = y + i * line_spacing
        cv2.putText(img, line, (x, line_y), font, font_scale, text_color, 1, cv2.LINE_AA)

def render_full_analysis(video_path: str, output_path: str):
    """Render video with both pose and AI analysis overlays."""
    
    print("Loading analysis data...")
    pose_data, ai_data = load_analysis_data(video_path)
    
    # Extract key data
    frame_poses = pose_data.get('pose_landmarks', [])
    angle_analysis = pose_data.get('angle_analysis', {})
    swing_phases = pose_data.get('swing_phases', {})
    
    # AI analysis data - extract from actual structure
    swings = ai_data.get('swings', [])
    coaching_script = ai_data.get('coaching_script', '')
    summary = ai_data.get('summary', {})
    
    # Get comments and score from first swing
    recommendations = []
    overall_quality = 'N/A'
    
    if swings:
        first_swing = swings[0]
        recommendations = first_swing.get('comments', [])
        overall_quality = f"{first_swing.get('score', 'N/A')}/10"
    
    # Extract highlights and improvements from summary
    highlights = summary.get('highlights', []) if isinstance(summary, dict) else []
    improvements = summary.get('improvements', []) if isinstance(summary, dict) else []
    key_issues = improvements  # Use improvements as key issues
    
    print(f"Found {len(key_issues)} issues and {len(recommendations)} recommendations")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_idx = 0
    connections = mp_pose.POSE_CONNECTIONS
    
    # Prepare coaching text - no need for issue_lines anymore
    # We'll use improvements directly
    
    rec_lines = []
    for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommendations
        wrapped = textwrap.wrap(f"{i}. {rec}", width=40)
        rec_lines.extend(wrapped)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 1. DRAW POSE SKELETON
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
                        
                        start_point = (int(start['x'] * width), int(start['y'] * height))
                        end_point = (int(end['x'] * width), int(end['y'] * height))
                        
                        cv2.line(frame, start_point, end_point, (0, 255, 255), 2)
                
                # Draw joint points
                for i, landmark in enumerate(landmarks):
                    x = int(landmark['x'] * width)
                    y = int(landmark['y'] * height)
                    
                    if i in [11, 12, 23, 24]:  # Key joints
                        cv2.circle(frame, (x, y), 8, (255, 0, 0), -1)
                    else:
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        
        # 2. DETERMINE CURRENT PHASE
        current_time = frame_idx / fps
        current_phase = None
        for phase, time_range in swing_phases.items():
            if time_range['start'] <= current_time <= time_range['end']:
                current_phase = phase
                break
        
        # 3. DRAW PHASE AND ANGLE INFO (top left)
        if current_phase:
            phase_text = f"Phase: {current_phase.replace('_', ' ').title()}"
            draw_text_with_background(frame, phase_text, (20, 40))
            
            # Spine angle
            if current_phase in angle_analysis.get('spine_angle', {}):
                spine_data = angle_analysis['spine_angle'][current_phase]
                angle = spine_data['angle']
                status = spine_data['status']
                color = get_color_for_status(status)
                
                angle_text = f"Spine Angle: {angle:.1f}°"
                cv2.putText(frame, angle_text, (20, 80), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
        
        # 4. DRAW OVERALL QUALITY (top right)
        quality_text = f"Score: {overall_quality}"
        try:
            score = float(overall_quality.split('/')[0])
            quality_color = (0, 255, 0) if score >= 7 else (0, 165, 255) if score >= 5 else (0, 0, 255)
        except:
            quality_color = (0, 165, 255)
        draw_text_with_background(frame, quality_text, (width - 200, 40), 
                                 text_color=quality_color)
        
        # 5. DRAW IMPROVEMENTS (bottom left)
        if improvements and frame_idx > 30:
            improvement_lines = ["IMPROVEMENTS:"]
            for i, imp in enumerate(improvements[:2], 1):
                wrapped = textwrap.wrap(f"{i}. {imp}", width=40)
                improvement_lines.extend(wrapped[:2])
            draw_multiline_text(frame, improvement_lines, 
                              (20, height - 150), font_scale=0.5)
        
        # 6. DRAW RECOMMENDATIONS (bottom right)
        if recommendations and frame_idx > 60:  # Show after 2 seconds
            rec_display = ["COACH TIPS:"]
            for i, rec in enumerate(recommendations[:2], 1):
                wrapped = textwrap.wrap(f"{i}. {rec}", width=35)
                rec_display.extend(wrapped[:2])
            start_x = width - 350
            draw_multiline_text(frame, rec_display, 
                              (start_x, height - 150), font_scale=0.5)
        
        # 7. DRAW HIGHLIGHTS (top center) - what's good
        if highlights and frame_idx > 90:  # Show after 3 seconds
            highlight_text = "GOOD: " + ", ".join(highlights)
            wrapped_highlights = textwrap.wrap(highlight_text, width=50)
            for i, line in enumerate(wrapped_highlights[:2]):
                draw_text_with_background(frame, line, (width//2 - 150, 100 + i*30),
                                        text_color=(0, 255, 0))
        
        # 8. ADD WATERMARK
        cv2.putText(frame, "MediaPipe + Gemini AI Analysis", (width - 300, height - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Write frame
        out.write(frame)
        frame_idx += 1
    
    # Release everything
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print(f"✅ Full analysis video created: {output_path}")
    print(f"   - {frame_idx} frames with pose skeleton")
    print(f"   - {len(key_issues)} coaching issues highlighted")
    print(f"   - {len(recommendations)} tips displayed")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render_full_analysis.py <video_path>")
        print("   Expects both _pose.json and _analysis.json files")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_path = video_path.replace('.mp4', '_full_analysis.mp4').replace('.mov', '_full_analysis.mp4')
    
    # Check required files exist
    pose_path = video_path.replace('.mp4', '_pose.json').replace('.mov', '_pose.json')
    analysis_path = video_path.replace('.mp4', '_analysis.json').replace('.mov', '_analysis.json')
    
    if not os.path.exists(pose_path):
        print(f"❌ Pose data not found: {pose_path}")
        sys.exit(1)
    
    if not os.path.exists(analysis_path):
        print(f"❌ AI analysis not found: {analysis_path}")
        print("   Run analyze_video_v2.py first")
        sys.exit(1)
    
    render_full_analysis(video_path, output_path)