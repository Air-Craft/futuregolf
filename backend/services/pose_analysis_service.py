"""
MediaPipe pose analysis service for golf swing body angle detection.
Extracts pose landmarks and calculates golf-specific body angles.
"""

import os
import cv2
import numpy as np
import logging
import tempfile
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import json
import math

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logging.warning("MediaPipe not available. Install mediapipe package.")

logger = logging.getLogger(__name__)


class PoseAnalysisService:
    """Service for analyzing golf swing pose using MediaPipe."""
    
    def __init__(self):
        if not MEDIAPIPE_AVAILABLE:
            logger.warning("MediaPipe not available. Pose analysis will return mock data.")
            return
            
        # Initialize MediaPipe pose detection
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # Higher complexity for more accurate pose detection
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Define key pose landmarks for golf analysis
        self.key_landmarks = {
            'head': [self.mp_pose.PoseLandmark.NOSE],
            'shoulders': [
                self.mp_pose.PoseLandmark.LEFT_SHOULDER,
                self.mp_pose.PoseLandmark.RIGHT_SHOULDER
            ],
            'hips': [
                self.mp_pose.PoseLandmark.LEFT_HIP,
                self.mp_pose.PoseLandmark.RIGHT_HIP
            ],
            'spine': [
                self.mp_pose.PoseLandmark.LEFT_SHOULDER,
                self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
                self.mp_pose.PoseLandmark.LEFT_HIP,
                self.mp_pose.PoseLandmark.RIGHT_HIP
            ],
            'knees': [
                self.mp_pose.PoseLandmark.LEFT_KNEE,
                self.mp_pose.PoseLandmark.RIGHT_KNEE
            ],
            'ankles': [
                self.mp_pose.PoseLandmark.LEFT_ANKLE,
                self.mp_pose.PoseLandmark.RIGHT_ANKLE
            ],
            'arms': [
                self.mp_pose.PoseLandmark.LEFT_ELBOW,
                self.mp_pose.PoseLandmark.RIGHT_ELBOW,
                self.mp_pose.PoseLandmark.LEFT_WRIST,
                self.mp_pose.PoseLandmark.RIGHT_WRIST
            ]
        }
        
        # Golf-specific optimal angle ranges
        self.optimal_ranges = {
            'spine_angle': {'min': 30, 'max': 45},  # degrees from vertical
            'shoulder_tilt': {'min': 5, 'max': 15},  # degrees (right shoulder lower)
            'hip_rotation': {'min': 30, 'max': 45},  # degrees open at impact
            'head_movement': {'lateral': 50, 'vertical': 25}  # mm
        }
        
        logger.info("MediaPipe pose analysis service initialized")
    
    async def analyze_video_pose(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze pose landmarks throughout a golf swing video.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict containing pose analysis results
        """
        if not MEDIAPIPE_AVAILABLE:
            return await self._generate_mock_pose_analysis()
        
        try:
            # Extract pose landmarks from video
            pose_data = await self._extract_pose_landmarks(video_path)
            
            # Calculate golf-specific angles
            angle_analysis = await self._calculate_golf_angles(pose_data)
            
            # Analyze swing phases
            swing_phases = await self._detect_swing_phases(pose_data)
            
            # Generate frame-by-frame status
            frame_status = await self._generate_frame_status(pose_data, angle_analysis)
            
            # Calculate biomechanical efficiency
            efficiency_scores = await self._calculate_biomechanical_efficiency(
                pose_data, angle_analysis
            )
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                angle_analysis, efficiency_scores
            )
            
            return {
                'success': True,
                'pose_landmarks': pose_data,
                'angle_analysis': angle_analysis,
                'swing_phases': swing_phases,
                'frame_by_frame_status': frame_status,
                'optimal_ranges': self.optimal_ranges,
                'biomechanical_efficiency': efficiency_scores,
                'recommendations': recommendations,
                'analysis_metadata': {
                    'total_frames': len(pose_data),
                    'video_duration': len(pose_data) / 30.0,  # Assume 30 FPS
                    'confidence_threshold': 0.5
                }
            }
            
        except Exception as e:
            logger.error(f"Pose analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'pose_landmarks': [],
                'angle_analysis': {}
            }
    
    async def _extract_pose_landmarks(self, video_path: str) -> List[Dict[str, Any]]:
        """Extract pose landmarks from video frames."""
        pose_data = []
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process frame with MediaPipe
                results = self.pose.process(rgb_frame)
                
                frame_data = {
                    'frame_number': frame_count,
                    'timestamp': frame_count / fps,
                    'landmarks': [],
                    'visibility': [],
                    'presence': []
                }
                
                if results.pose_landmarks:
                    # Extract landmark coordinates
                    for landmark in results.pose_landmarks.landmark:
                        frame_data['landmarks'].append({
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z,
                            'visibility': landmark.visibility if hasattr(landmark, 'visibility') else 1.0
                        })
                        frame_data['visibility'].append(
                            landmark.visibility if hasattr(landmark, 'visibility') else 1.0
                        )
                        frame_data['presence'].append(
                            landmark.presence if hasattr(landmark, 'presence') else 1.0
                        )
                
                pose_data.append(frame_data)
                frame_count += 1
                
        finally:
            cap.release()
        
        logger.info(f"Extracted pose landmarks from {frame_count} frames")
        return pose_data
    
    async def _calculate_golf_angles(self, pose_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate golf-specific body angles from pose landmarks."""
        if not pose_data:
            return {}
        
        angle_analysis = {
            'spine_angle': {},
            'shoulder_tilt': {},
            'hip_rotation': {},
            'head_position': {}
        }
        
        # Calculate angles for key swing phases
        phases = ['setup', 'backswing_top', 'impact', 'follow_through']
        phase_frames = self._get_phase_frames(pose_data, phases)
        
        for phase, frame_idx in phase_frames.items():
            if frame_idx >= len(pose_data) or not pose_data[frame_idx]['landmarks']:
                continue
                
            landmarks = pose_data[frame_idx]['landmarks']
            
            # Calculate spine angle
            spine_angle = self._calculate_spine_angle(landmarks)
            angle_analysis['spine_angle'][phase] = {
                'angle': spine_angle,
                'optimal': self._is_angle_optimal(spine_angle, 'spine_angle'),
                'status': 'green' if self._is_angle_optimal(spine_angle, 'spine_angle') else 'red'
            }
            
            # Calculate shoulder tilt
            shoulder_tilt = self._calculate_shoulder_tilt(landmarks)
            angle_analysis['shoulder_tilt'][phase] = {
                'angle': shoulder_tilt,
                'optimal': self._is_angle_optimal(shoulder_tilt, 'shoulder_tilt'),
                'status': 'green' if self._is_angle_optimal(shoulder_tilt, 'shoulder_tilt') else 'red'
            }
            
            # Calculate hip rotation
            hip_rotation = self._calculate_hip_rotation(landmarks)
            angle_analysis['hip_rotation'][phase] = {
                'angle': hip_rotation,
                'optimal': self._is_angle_optimal(hip_rotation, 'hip_rotation'),
                'status': 'green' if self._is_angle_optimal(hip_rotation, 'hip_rotation') else 'red'
            }
        
        # Calculate head position stability
        head_stability = self._calculate_head_stability(pose_data)
        angle_analysis['head_position'] = {
            'stability_score': head_stability['score'],
            'lateral_movement': head_stability['lateral_movement'],
            'vertical_movement': head_stability['vertical_movement'],
            'status': 'green' if head_stability['score'] > 70 else 'red'
        }
        
        return angle_analysis
    
    def _calculate_spine_angle(self, landmarks: List[Dict[str, float]]) -> float:
        """Calculate spine angle from vertical."""
        if len(landmarks) < 24:  # Ensure we have enough landmarks
            return 0.0
        
        # Use shoulder and hip landmarks to calculate spine angle
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # Calculate midpoints
        shoulder_mid = {
            'x': (left_shoulder['x'] + right_shoulder['x']) / 2,
            'y': (left_shoulder['y'] + right_shoulder['y']) / 2
        }
        hip_mid = {
            'x': (left_hip['x'] + right_hip['x']) / 2,
            'y': (left_hip['y'] + right_hip['y']) / 2
        }
        
        # Calculate angle from vertical
        dx = shoulder_mid['x'] - hip_mid['x']
        dy = shoulder_mid['y'] - hip_mid['y']
        angle = math.degrees(math.atan2(abs(dx), abs(dy)))
        
        return angle
    
    def _calculate_shoulder_tilt(self, landmarks: List[Dict[str, float]]) -> float:
        """Calculate shoulder tilt angle."""
        if len(landmarks) < 12:
            return 0.0
        
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        
        # Calculate tilt angle
        dx = right_shoulder['x'] - left_shoulder['x']
        dy = right_shoulder['y'] - left_shoulder['y']
        angle = math.degrees(math.atan2(dy, dx))
        
        return abs(angle)
    
    def _calculate_hip_rotation(self, landmarks: List[Dict[str, float]]) -> float:
        """Calculate hip rotation angle."""
        if len(landmarks) < 24:
            return 0.0
        
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # Calculate rotation angle (simplified - would need more sophisticated calculation)
        dx = right_hip['x'] - left_hip['x']
        dy = right_hip['y'] - left_hip['y']
        angle = math.degrees(math.atan2(dy, dx))
        
        return abs(angle)
    
    def _calculate_head_stability(self, pose_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate head position stability throughout swing."""
        if not pose_data:
            return {'score': 0, 'lateral_movement': 0, 'vertical_movement': 0}
        
        head_positions = []
        for frame_data in pose_data:
            if frame_data['landmarks']:
                nose = frame_data['landmarks'][self.mp_pose.PoseLandmark.NOSE.value]
                head_positions.append({'x': nose['x'], 'y': nose['y']})
        
        if len(head_positions) < 2:
            return {'score': 0, 'lateral_movement': 0, 'vertical_movement': 0}
        
        # Calculate movement range
        x_positions = [pos['x'] for pos in head_positions]
        y_positions = [pos['y'] for pos in head_positions]
        
        lateral_movement = (max(x_positions) - min(x_positions)) * 1000  # Convert to mm
        vertical_movement = (max(y_positions) - min(y_positions)) * 1000
        
        # Calculate stability score (inverse of movement)
        stability_score = max(0, 100 - (lateral_movement + vertical_movement))
        
        return {
            'score': stability_score,
            'lateral_movement': lateral_movement,
            'vertical_movement': vertical_movement
        }
    
    def _is_angle_optimal(self, angle: float, angle_type: str) -> bool:
        """Check if angle is within optimal range."""
        if angle_type not in self.optimal_ranges:
            return True
        
        range_info = self.optimal_ranges[angle_type]
        return range_info['min'] <= angle <= range_info['max']
    
    def _get_phase_frames(self, pose_data: List[Dict[str, Any]], phases: List[str]) -> Dict[str, int]:
        """Get frame indices for different swing phases."""
        total_frames = len(pose_data)
        if total_frames == 0:
            return {}
        
        # Simple phase detection based on frame distribution
        # In a real implementation, this would analyze pose changes
        return {
            'setup': 0,
            'backswing_top': total_frames // 3,
            'impact': total_frames * 2 // 3,
            'follow_through': total_frames - 1
        }
    
    async def _detect_swing_phases(self, pose_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect swing phases based on pose analysis."""
        if not pose_data:
            return {}
        
        total_frames = len(pose_data)
        fps = 30.0  # Assume 30 FPS
        
        # Simple phase detection - in production, would use more sophisticated analysis
        phases = {
            'setup': {'start': 0.0, 'end': 1.0},
            'backswing': {'start': 1.0, 'end': total_frames / fps * 0.4},
            'downswing': {'start': total_frames / fps * 0.4, 'end': total_frames / fps * 0.6},
            'impact': {'start': total_frames / fps * 0.6, 'end': total_frames / fps * 0.65},
            'follow_through': {'start': total_frames / fps * 0.65, 'end': total_frames / fps}
        }
        
        return phases
    
    async def _generate_frame_status(self, pose_data: List[Dict[str, Any]], 
                                   angle_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate frame-by-frame status for pose analysis."""
        frame_status = []
        
        for i, frame_data in enumerate(pose_data):
            if not frame_data['landmarks']:
                continue
                
            # Simple status determination - would be more sophisticated in production
            overall_status = 'green'  # Default
            
            frame_status.append({
                'frame': i,
                'timestamp': frame_data['timestamp'],
                'overall_status': overall_status,
                'angle_statuses': {
                    'spine': 'green',
                    'shoulders': 'green',
                    'hips': 'green',
                    'head': 'green'
                }
            })
        
        return frame_status
    
    async def _calculate_biomechanical_efficiency(self, pose_data: List[Dict[str, Any]], 
                                                angle_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate biomechanical efficiency scores."""
        # Simplified scoring - would use more sophisticated analysis in production
        return {
            'overall_score': 75.0,
            'kinetic_chain_score': 80.0,
            'power_transfer_score': 70.0,
            'balance_score': 85.0
        }
    
    async def _generate_recommendations(self, angle_analysis: Dict[str, Any], 
                                      efficiency_scores: Dict[str, float]) -> List[Dict[str, str]]:
        """Generate coaching recommendations based on pose analysis."""
        recommendations = []
        
        # Check spine angle
        spine_issues = []
        for phase, data in angle_analysis.get('spine_angle', {}).items():
            if not data.get('optimal', True):
                spine_issues.append(phase)
        
        if spine_issues:
            recommendations.append({
                'body_part': 'spine',
                'issue': f'Spine angle not optimal in {", ".join(spine_issues)}',
                'correction': 'Maintain consistent spine angle throughout swing',
                'drill_suggestion': 'Practice with alignment stick across back'
            })
        
        # Check head stability
        head_data = angle_analysis.get('head_position', {})
        if head_data.get('stability_score', 100) < 70:
            recommendations.append({
                'body_part': 'head',
                'issue': 'Excessive head movement during swing',
                'correction': 'Keep head stable and eyes focused on ball',
                'drill_suggestion': 'Practice with head against wall'
            })
        
        return recommendations
    
    async def _generate_mock_pose_analysis(self) -> Dict[str, Any]:
        """Generate mock pose analysis for development/testing."""
        return {
            'success': True,
            'pose_landmarks': [],
            'angle_analysis': {
                'spine_angle': {
                    'setup': {'angle': 35.0, 'optimal': True, 'status': 'green'},
                    'backswing_top': {'angle': 38.0, 'optimal': True, 'status': 'green'},
                    'impact': {'angle': 32.0, 'optimal': True, 'status': 'green'},
                    'follow_through': {'angle': 30.0, 'optimal': True, 'status': 'green'}
                },
                'shoulder_tilt': {
                    'setup': {'angle': 8.0, 'optimal': True, 'status': 'green'},
                    'backswing_top': {'angle': 12.0, 'optimal': True, 'status': 'green'},
                    'impact': {'angle': 6.0, 'optimal': True, 'status': 'green'}
                },
                'hip_rotation': {
                    'setup': {'angle': 0.0, 'optimal': True, 'status': 'green'},
                    'backswing_top': {'angle': 15.0, 'optimal': True, 'status': 'green'},
                    'impact': {'angle': 35.0, 'optimal': True, 'status': 'green'}
                },
                'head_position': {
                    'stability_score': 85.0,
                    'lateral_movement': 15.0,
                    'vertical_movement': 8.0,
                    'status': 'green'
                }
            },
            'swing_phases': {
                'setup': {'start': 0.0, 'end': 1.0},
                'backswing': {'start': 1.0, 'end': 2.5},
                'downswing': {'start': 2.5, 'end': 3.0},
                'impact': {'start': 3.0, 'end': 3.2},
                'follow_through': {'start': 3.2, 'end': 5.0}
            },
            'frame_by_frame_status': [],
            'optimal_ranges': self.optimal_ranges,
            'biomechanical_efficiency': {
                'overall_score': 82.0,
                'kinetic_chain_score': 78.0,
                'power_transfer_score': 85.0,
                'balance_score': 88.0
            },
            'recommendations': [
                {
                    'body_part': 'shoulders',
                    'issue': 'Slight over-rotation at top of backswing',
                    'correction': 'Limit shoulder turn to 90 degrees',
                    'drill_suggestion': 'Practice with restricted shoulder turn'
                }
            ],
            'analysis_metadata': {
                'total_frames': 150,
                'video_duration': 5.0,
                'confidence_threshold': 0.5
            }
        }


# Global service instance
pose_analysis_service = None

def get_pose_analysis_service():
    """Get the global pose analysis service instance."""
    global pose_analysis_service
    if pose_analysis_service is None:
        pose_analysis_service = PoseAnalysisService()
    return pose_analysis_service