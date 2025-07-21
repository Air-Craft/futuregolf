"""
Video Compositor Service
Creates composited golf swing videos with MediaPipe skeleton lines and coaching text overlays.
"""

import cv2
import numpy as np
import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoCompositor:
    """Service for compositing golf swing videos with pose overlays and text."""
    
    def __init__(self):
        # MediaPipe pose connections for drawing skeleton
        self.pose_connections = [
            # Face
            (0, 1), (1, 2), (2, 3), (3, 7),
            (0, 4), (4, 5), (5, 6), (6, 8),
            # Torso
            (9, 10),
            (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
            (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
            (11, 23), (12, 24), (23, 24),
            # Left leg
            (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
            # Right leg
            (24, 26), (26, 28), (28, 30), (28, 32), (30, 32)
        ]
        
        # Colors for different body parts (BGR format)
        self.colors = {
            'head': (255, 255, 0),     # Cyan
            'torso': (0, 255, 0),      # Green
            'left_arm': (255, 0, 0),   # Blue
            'right_arm': (0, 0, 255),  # Red
            'left_leg': (255, 255, 0), # Yellow
            'right_leg': (255, 0, 255) # Magenta
        }
    
    async def composite_video(
        self, 
        input_video_path: str, 
        pose_data: Dict[str, Any], 
        coaching_tips: List[Dict[str, Any]],
        output_path: str,
        swing_phases: Dict[str, Any] = None,
        quality_score: int = None
    ) -> Dict[str, Any]:
        """
        Create composited video with pose skeleton and coaching text overlays.
        
        Args:
            input_video_path: Path to original video
            pose_data: MediaPipe pose detection results
            coaching_tips: List of coaching tips with timestamps
            output_path: Path for output composited video
            
        Returns:
            Dict with compositing results and metadata
        """
        try:
            logger.info(f"Starting video compositing: {input_video_path} -> {output_path}")
            
            # Open input video
            cap = cv2.VideoCapture(input_video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {input_video_path}")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"Video properties: {width}x{height}, {fps}fps, {total_frames} frames")
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Get pose landmarks data (handle None case)
            pose_landmarks = pose_data.get('pose_landmarks', []) if pose_data else []
            pose_by_frame = {landmark['frame_number']: landmark for landmark in pose_landmarks}
            
            # Process each frame
            frame_number = 0
            frames_processed = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate timestamp
                timestamp = frame_number / fps
                
                # Skip pose skeleton drawing - only using text overlays
                
                # Determine current swing phase
                current_phase = self._get_current_phase(timestamp, coaching_tips, swing_phases)
                
                # Add coaching text overlays with phase indicator and quality score
                frame = self._add_coaching_text(frame, coaching_tips, timestamp, width, height, current_phase, quality_score)
                
                # Write frame
                out.write(frame)
                frames_processed += 1
                
                # Progress logging
                if frames_processed % 30 == 0:  # Log every 30 frames
                    progress = (frames_processed / total_frames) * 100
                    logger.info(f"Compositing progress: {progress:.1f}% ({frames_processed}/{total_frames} frames)")
                
                frame_number += 1
            
            # Cleanup
            cap.release()
            out.release()
            
            # Verify output file
            if not os.path.exists(output_path):
                raise RuntimeError("Failed to create composited video file")
            
            output_size = os.path.getsize(output_path)
            
            result = {
                "success": True,
                "output_path": output_path,
                "output_size_bytes": output_size,
                "output_size_mb": round(output_size / (1024 * 1024), 2),
                "frames_processed": frames_processed,
                "pose_overlays_added": 0,  # No pose overlays since we skipped pose detection
                "coaching_overlays_added": len(coaching_tips),
                "video_properties": {
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "duration_seconds": total_frames / fps
                }
            }
            
            logger.info(f"Video compositing completed: {frames_processed} frames, {output_size} bytes")
            return result
            
        except Exception as e:
            logger.error(f"Video compositing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output_path": output_path
            }
    
    def _draw_pose_skeleton(self, frame: np.ndarray, pose_data: Dict[str, Any], width: int, height: int) -> np.ndarray:
        """Draw MediaPipe pose skeleton on frame."""
        try:
            landmarks = pose_data.get('landmarks', [])
            if not landmarks or len(landmarks) != 33:
                return frame
            
            # Convert normalized coordinates to pixel coordinates
            points = []
            for landmark in landmarks:
                x = int(landmark.get('x', 0) * width)
                y = int(landmark.get('y', 0) * height)
                visibility = landmark.get('visibility', 0)
                points.append((x, y, visibility))
            
            # Draw connections
            for connection in self.pose_connections:
                start_idx, end_idx = connection
                if start_idx < len(points) and end_idx < len(points):
                    start_point = points[start_idx]
                    end_point = points[end_idx]
                    
                    # Only draw if both points are visible enough
                    if start_point[2] > 0.5 and end_point[2] > 0.5:
                        color = self._get_connection_color(start_idx, end_idx)
                        cv2.line(frame, 
                                (start_point[0], start_point[1]), 
                                (end_point[0], end_point[1]), 
                                color, 3)
            
            # Draw key points
            key_points = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]  # Important body landmarks
            for idx in key_points:
                if idx < len(points) and points[idx][2] > 0.5:
                    cv2.circle(frame, (points[idx][0], points[idx][1]), 5, (0, 255, 255), -1)
            
            return frame
            
        except Exception as e:
            logger.warning(f"Failed to draw pose skeleton: {e}")
            return frame
    
    def _get_connection_color(self, start_idx: int, end_idx: int) -> Tuple[int, int, int]:
        """Get color for pose connection based on body part."""
        # Face connections
        if start_idx < 11 and end_idx < 11:
            return self.colors['head']
        
        # Left arm connections
        elif (start_idx in [11, 13, 15] and end_idx in [11, 13, 15]) or \
             (start_idx in [15, 17, 19, 21] and end_idx in [15, 17, 19, 21]):
            return self.colors['left_arm']
        
        # Right arm connections  
        elif (start_idx in [12, 14, 16] and end_idx in [12, 14, 16]) or \
             (start_idx in [16, 18, 20, 22] and end_idx in [16, 18, 20, 22]):
            return self.colors['right_arm']
        
        # Left leg connections
        elif start_idx in [23, 25, 27, 29, 31] and end_idx in [23, 25, 27, 29, 31]:
            return self.colors['left_leg']
        
        # Right leg connections
        elif start_idx in [24, 26, 28, 30, 32] and end_idx in [24, 26, 28, 30, 32]:
            return self.colors['right_leg']
        
        # Torso connections
        else:
            return self.colors['torso']
    
    def _wrap_text(self, text: str, font, font_scale: float, max_width: int, thickness: int = 1) -> List[str]:
        """Wrap text to fit within max_width pixels."""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            # Test adding this word to current line
            test_line = ' '.join(current_line + [word])
            text_size = cv2.getTextSize(test_line, font, font_scale, thickness)[0]
            
            if text_size[0] <= max_width:
                # Word fits, add it
                current_line.append(word)
            else:
                # Word doesn't fit, start new line
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def _add_coaching_text(
        self, 
        frame: np.ndarray, 
        coaching_tips: List[Dict[str, Any]], 
        timestamp: float,
        width: int,
        height: int,
        current_phase: str = None,
        quality_score: int = None
    ) -> np.ndarray:
        """Add coaching text overlays at appropriate timestamps."""
        try:
            # Find active coaching tips for this timestamp (show from timestamp until video end)
            active_tips = []
            for tip in coaching_tips:
                tip_start = float(tip.get('timestamp', 0))
                
                if tip_start <= timestamp:
                    active_tips.append(tip)
                    # Debug logging (reduced frequency)
                    if int(timestamp * 10) % 10 == 0:  # Log only every second
                        logger.info(f"Active tip at {timestamp:.2f}s: {tip.get('coaching_tip') or tip.get('message', '') or tip.get('text', '')}")
            
            # Add swing phase indicator (top left, title case)
            if current_phase:
                phase_text = f"Swing Phase: {current_phase.replace('_', ' ').title()}"
                phase_y = 35
                phase_scale = 0.7  # Bigger for better readability
                
                # Phase indicator background
                phase_size = cv2.getTextSize(phase_text, cv2.FONT_HERSHEY_SIMPLEX, phase_scale, 1)[0]
                phase_bg_x1 = 10
                phase_bg_y1 = phase_y - 20
                phase_bg_x2 = 20 + phase_size[0] + 10
                phase_bg_y2 = phase_y + 10
                
                # Draw phase background
                overlay = frame.copy()
                cv2.rectangle(overlay, (phase_bg_x1, phase_bg_y1), (phase_bg_x2, phase_bg_y2), (50, 50, 50), -1)
                frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
                
                # Draw phase text (left aligned) with antialiasing
                cv2.putText(frame, phase_text, (20, phase_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, phase_scale, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Add quality score indicator (under swing phase, only during follow-through)
            if quality_score is not None and current_phase == "follow_through":
                quality_text = f"Quality: {quality_score}"
                quality_scale = 0.5  # 30% smaller as requested
                quality_y = 65  # Position under the swing phase indicator
                
                # Quality indicator background
                quality_size = cv2.getTextSize(quality_text, cv2.FONT_HERSHEY_SIMPLEX, quality_scale, 1)[0]
                quality_bg_x1 = 10
                quality_bg_y1 = quality_y - 15
                quality_bg_x2 = 20 + quality_size[0] + 10
                quality_bg_y2 = quality_y + 8
                
                # Draw quality background
                overlay = frame.copy()
                cv2.rectangle(overlay, (quality_bg_x1, quality_bg_y1), (quality_bg_x2, quality_bg_y2), (50, 50, 50), -1)
                frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
                
                # Draw quality text (left aligned under phase) with antialiasing
                cv2.putText(frame, quality_text, (20, quality_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, quality_scale, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Draw active tips at bottom of screen (better readability)
            if active_tips:
                # Sort by priority (high priority tips shown first)
                active_tips.sort(key=lambda x: 0 if x.get('priority') == 'high' else 1)
                
                # Text rendering parameters
                text_scale = 0.4  # 20% smaller
                line_height = 20
                margin_x = 20
                margin_bottom = 20
                max_text_width = width - (margin_x * 2)  # Leave margins on both sides
                font = cv2.FONT_HERSHEY_SIMPLEX
                
                # Calculate total height needed for all tips
                all_wrapped_lines = []
                for tip in active_tips[:3]:  # Show max 3 tips at once
                    text = tip.get('coaching_tip') or tip.get('message', '') or tip.get('text', '')
                    if text:
                        wrapped_lines = self._wrap_text(text, font, text_scale, max_text_width, 1)
                        all_wrapped_lines.append({
                            'lines': wrapped_lines,
                            'tip': tip,
                            'text': text
                        })
                
                # Calculate starting Y position from bottom
                total_lines = sum(len(item['lines']) for item in all_wrapped_lines)
                # Add spacing between tips
                total_height = total_lines * line_height + (len(all_wrapped_lines) - 1) * 10
                y_start = height - margin_bottom - total_height
                
                # Draw each tip
                current_y = y_start
                for item_idx, item in enumerate(all_wrapped_lines):
                    tip = item['tip']
                    lines = item['lines']
                    priority = tip.get('priority', 'normal')
                    
                    # Choose color based on priority
                    if priority == 'high':
                        color = (0, 0, 255)  # Red
                        thickness = 1
                    elif priority == 'medium':
                        color = (0, 165, 255)  # Orange
                        thickness = 1
                    else:
                        color = (255, 255, 255)  # White
                        thickness = 1
                    
                    # Calculate background for all lines of this tip
                    max_line_width = max(cv2.getTextSize(line, font, text_scale, thickness)[0][0] for line in lines)
                    bg_height = len(lines) * line_height + 5
                    
                    # Draw semi-transparent background for this tip
                    overlay = frame.copy()
                    bg_x1 = margin_x - 10
                    bg_y1 = current_y - 15
                    bg_x2 = margin_x + max_line_width + 10
                    bg_y2 = current_y + bg_height - 10
                    cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
                    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
                    
                    # Draw each line of wrapped text
                    for line_idx, line in enumerate(lines):
                        y_pos = current_y + (line_idx * line_height)
                        cv2.putText(frame, line, (margin_x, y_pos), font, text_scale, color, thickness, cv2.LINE_AA)
                    
                    # Move to next tip position with spacing
                    current_y += len(lines) * line_height + 10
            
            return frame
            
        except Exception as e:
            logger.warning(f"Failed to add coaching text: {e}")
            return frame
    
    def _get_current_phase(self, timestamp: float, coaching_tips: List[Dict[str, Any]], swing_phases: Dict = None) -> str:
        """Determine the current swing phase based on timestamp and swing phase data."""
        # If swing phases data is provided (from Gemini), use that
        if swing_phases:
            for phase_name, phase_data in swing_phases.items():
                start_time = float(phase_data.get('start', 0))
                end_time = float(phase_data.get('end', 0))
                if start_time <= timestamp <= end_time:
                    return phase_name
        
        # Fallback to simple time-based approach
        # if timestamp <= 2.0:
        return "none"
        
    
    async def create_preview_frame(
        self, 
        video_path: str, 
        timestamp: float, 
        pose_data: Dict[str, Any],
        output_path: str
    ) -> Dict[str, Any]:
        """Create a preview frame with pose overlay at specific timestamp."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            
            # Seek to specific frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                raise ValueError(f"Cannot read frame at timestamp {timestamp}")
            
            # Add pose overlay if available
            pose_landmarks = pose_data.get('pose_landmarks', [])
            pose_by_frame = {landmark['frame_number']: landmark for landmark in pose_landmarks}
            
            if frame_number in pose_by_frame:
                height, width = frame.shape[:2]
                frame = self._draw_pose_skeleton(frame, pose_by_frame[frame_number], width, height)
            
            # Save preview frame
            cv2.imwrite(output_path, frame)
            
            return {
                "success": True,
                "preview_path": output_path,
                "timestamp": timestamp,
                "frame_number": frame_number
            }
            
        except Exception as e:
            logger.error(f"Failed to create preview frame: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global service instance
video_compositor = None

def get_video_compositor():
    """Get the global video compositor instance."""
    global video_compositor
    if video_compositor is None:
        video_compositor = VideoCompositor()
    return video_compositor