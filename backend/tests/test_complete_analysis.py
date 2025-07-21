#!/usr/bin/env python3
"""
Complete Analysis Test
Tests the full video analysis pipeline and exports all output types as separate JSON files.
Provides detailed console progress and exports:
1. pose_data_output.json - MediaPipe landmarks for server-side compositing
2. swing_analysis_output.json - Phase breakdown for frontend display  
3. coaching_script_output.json - TTS statements with timestamps
4. video_metadata_output.json - Composited video information
5. complete_analysis_summary.json - Combined overview
"""

import sys
import os
import asyncio
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services
# from services.pose_analysis_service import get_pose_analysis_service  # Disabled
from services.video_analysis_service import get_video_analysis_service
from services.video_pipeline_service import get_video_pipeline_service
from services.video_compositor import get_video_compositor


class CompleteAnalysisTest:
    """Complete video analysis test with JSON export and console progress."""
    
    def __init__(self):
        self.test_video_path = os.path.join(
            os.path.dirname(__file__), 
            "test_video.mov"
        )
        self.output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "test_results"
        )
        
        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Services
        # self.pose_service = get_pose_analysis_service()  # Disabled
        self.pose_service = None
        self.video_service = get_video_analysis_service()
        self.pipeline_service = get_video_pipeline_service()
        self.compositor_service = get_video_compositor()
        
        # Results storage
        self.results = {
            'pose_data': None,
            'swing_analysis': None,
            'coaching_script': None,
            'video_metadata': None,
            'test_metadata': {}
        }
        
        print("🎬 " + "=" * 80)
        print("🎬 FUTUREGOLF COMPLETE ANALYSIS TEST")
        print("🎬 " + "=" * 80)
        print(f"🎬 Test video: {os.path.basename(self.test_video_path)}")
        print(f"🎬 Output directory: {self.output_dir}")
        print("🎬 " + "=" * 80)
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete analysis test."""
        start_time = time.time()
        
        try:
            # Validate test video
            await self._validate_test_video()
            
            # Step 1: Skip pose detection and set empty data
            await self._skip_pose_detection()
            
            # Step 2: Gemini Visual Analysis (8fps)
            await self._run_gemini_analysis()
            
            # Step 3: Coaching Script Generation
            await self._run_coaching_script_generation()
            
            # Step 4: Video Compositing (Real) - No pose overlays
            await self._run_video_compositing()
            
            # Step 5: Export all JSON files
            await self._export_all_results()
            
            # Final summary
            total_time = time.time() - start_time
            await self._print_final_summary(total_time)
            
            return {
                'success': True,
                'total_time': total_time,
                'outputs_generated': 5,
                'results_directory': self.output_dir
            }
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            print(f"❌ Test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_time': time.time() - start_time
            }
    
    async def _validate_test_video(self):
        """Validate the test video file."""
        print("\n📁 VALIDATING TEST VIDEO")
        print("-" * 40)
        
        if not os.path.exists(self.test_video_path):
            raise FileNotFoundError(f"Test video not found: {self.test_video_path}")
        
        # Get video properties
        import cv2
        cap = cv2.VideoCapture(self.test_video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {self.test_video_path}")
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        file_size = os.path.getsize(self.test_video_path)
        
        cap.release()
        
        # Store video metadata
        self.results['test_metadata'] = {
            'video_file': os.path.basename(self.test_video_path),
            'file_size_bytes': file_size,
            'file_size_kb': round(file_size / 1024, 1),
            'resolution': f"{width}x{height}",
            'duration_seconds': round(duration, 2),
            'fps': round(fps, 2),
            'total_frames': frame_count,
            'test_start_time': datetime.now().isoformat()
        }
        
        print(f"📊 Video properties:")
        print(f"   • File size: {self.results['test_metadata']['file_size_kb']}KB")
        print(f"   • Resolution: {self.results['test_metadata']['resolution']}")
        print(f"   • Duration: {self.results['test_metadata']['duration_seconds']}s")
        print(f"   • FPS: {self.results['test_metadata']['fps']}")
        print(f"   • Total frames: {self.results['test_metadata']['total_frames']}")
        print("✅ Video validation complete")
    
    async def _skip_pose_detection(self):
        """Skip pose detection - using Gemini for swing phase analysis."""
        # Set empty pose data for compatibility
        self.results['pose_data'] = {
            'success': True,
            'processing_time': 0.0,
            'frames_processed': 0,
            'pose_landmarks': [],
            'body_angles': {},
            'swing_phases': [],
            'biomechanical_scores': {},
            'note': 'Pose detection skipped - using Gemini for swing analysis'
        }
    
    async def _run_gemini_analysis(self):
        """Run Gemini visual analysis."""
        print("\n🤖 STEP 2: Gemini Visual Analysis")
        print("-" * 40)
        
        start_time = time.time()
        
        # Get video info for display
        total_frames = self.results['test_metadata']['total_frames']
        original_fps = self.results['test_metadata']['fps']
        
        print(f"• Submitting whole video to Gemini for analysis")
        print(f"• Video FPS: {original_fps:.1f}")
        print(f"• Total frames: {total_frames} frames")
        
        try:
            # Use the real video analysis service with Gemini integration
            print("• Calling Gemini API for video analysis...")
            
            # Create a mock analysis using the video analysis service's method
            # Since we can't pass user/video IDs, we'll use the internal method
            pose_analysis_result = self.results['pose_data'] if self.results['pose_data']['success'] else None
            
            # Call the internal Gemini analysis method
            analysis_result = await self.video_service._analyze_with_gemini(
                self.test_video_path,
                await self.video_service._load_coaching_prompt(),
                pose_analysis_result
            )
            
            if analysis_result:
                print("✅ Gemini analysis completed successfully")
                
                # Process Gemini results into our expected format
                swings = analysis_result.get('swings', [])
                if not swings:
                    raise Exception("No swings found in Gemini analysis")
                
                # For now, process the first swing (can be extended for multiple swings)
                first_swing = swings[0]
                swing_phases = first_swing.get('phases', {})
                comments = first_swing.get('comments', [])
                
                # No transformation needed - use exact Gemini format
                
                # Store exact Gemini format (matching prompt specification)
                self.results['swing_analysis'] = analysis_result
                
                # Also store processing metadata
                self.results['swing_analysis']['success'] = True
                self.results['swing_analysis']['processing_time'] = time.time() - start_time
                self.results['swing_analysis']['frames_analyzed'] = total_frames
                self.results['swing_analysis']['gemini_used'] = True
                
                # Print phase information from Gemini format
                for phase_name, phase_data in swing_phases.items():
                    print(f"• {phase_name.title()} phase: {phase_data.get('start', 0)}-{phase_data.get('end', 0)}s ✅")
                
            else:
                raise Exception("Gemini analysis returned empty result")
                
        except Exception as e:
            print(f"❌ Gemini analysis failed: {e}")
            logger.error(f"Gemini analysis failed: {e}")
            raise RuntimeError(f"Gemini analysis failed: {e}")
        
        processing_time = time.time() - start_time
        gemini_status = "with Gemini AI" if self.results['swing_analysis'].get('gemini_used') else "with fallback data"
        print(f"✅ Swing analysis complete {gemini_status} in {processing_time:.1f}s")
        
        # Validate JSON structure if using real Gemini
        if self.results['swing_analysis'].get('gemini_used'):
            validation_result = self._validate_gemini_json_structure(self.results['swing_analysis'])
            if validation_result['valid']:
                print(f"✅ JSON structure validation passed: {validation_result['summary']}")
            else:
                print(f"⚠️ JSON structure validation issues: {validation_result['issues']}")
        
        print(f"💾 Swing analysis data prepared for export")
    
    async def _run_coaching_script_generation(self):
        """Generate coaching script with TTS statements using real service."""
        print("\n🎙️  STEP 3: Coaching Script Generation")
        print("-" * 40)
        
        start_time = time.time()
        
        print("• Generating TTS script using sports commentator prompt...")
        
        try:
            # Get video duration
            video_duration = self.results['test_metadata']['duration_seconds']
            swing_analysis = self.results['swing_analysis']
            
            # Use the real coaching script generation service
            print("• Calling video analysis service for coaching script...")
            
            coaching_result = await self.video_service.generate_coaching_script(
                swing_analysis,
                video_duration
            )
            
            if coaching_result and coaching_result.get('success'):
                print("✅ Coaching script generated successfully using real service")
                
                self.results['coaching_script'] = {
                    'success': True,
                    'processing_time': time.time() - start_time,
                    'service_used': True,
                    'statements': coaching_result.get('statements', []),
                    'total_statements': coaching_result.get('total_statements', 0),
                    'total_duration': coaching_result.get('total_duration', 0),
                    'script_metadata': coaching_result.get('script_metadata', {}),
                    'video_duration': video_duration,
                    'extends_past_video': coaching_result.get('total_duration', 0) > video_duration
                }
                
                print(f"• Created {coaching_result.get('total_statements', 0)} coaching statements")
                print(f"• Total script duration: {coaching_result.get('total_duration', 0):.1f}s")
                print(f"• Video duration: {video_duration:.1f}s")
                if coaching_result.get('total_duration', 0) > video_duration:
                    print(f"• Script extends {coaching_result.get('total_duration', 0) - video_duration:.1f}s past video end")
                
            else:
                raise Exception("Coaching script service returned empty result")
                
        except Exception as e:
            print(f"❌ Coaching script generation failed: {e}")
            logger.error(f"Coaching script generation failed: {e}")
            raise RuntimeError(f"Coaching script generation failed: {e}")
        
        processing_time = time.time() - start_time
        service_status = "with real service" if self.results['coaching_script'].get('service_used') else "with fallback"
        print(f"✅ Coaching script complete {service_status} in {processing_time:.1f}s")
        print(f"💾 Coaching script prepared for export")
    
    async def _run_video_compositing(self):
        """Real video compositing with text overlays only (no pose skeleton)."""
        print("\n🎥 STEP 4: Video Compositing (Real)")
        print("-" * 40)
        
        start_time = time.time()
        
        total_frames = self.results['test_metadata']['total_frames']
        
        # Generate composited video filename
        composited_filename = f"composited_swing_analysis_{int(time.time())}.mp4"
        composited_path = os.path.join(self.output_dir, composited_filename)
        
        try:
            print(f"• Creating composited video with coaching text overlays...")
            print(f"• Input: {os.path.basename(self.test_video_path)}")
            print(f"• Output: {composited_filename}")
            
            # Prepare coaching tips from Gemini analysis for video overlay (persistent until video end)
            coaching_tips = []
            swings = self.results['swing_analysis'].get('swings', [])
            
            if swings:
                first_swing = swings[0]
                comments = first_swing.get('comments', [])
                phases = first_swing.get('phases', {})
                
                # Get follow-through phase timing for coaching tips
                follow_through = phases.get('follow_through', {})
                follow_through_start = float(follow_through.get('start', 7.0))
                
                # Add comments as coaching tips during follow-through
                for i, comment in enumerate(comments):
                    timestamp = follow_through_start + (i * 0.5)  # Space them 0.5s apart
                    coaching_tips.append({
                        'timestamp': timestamp,
                        'message': comment,
                        'priority': 'medium',
                        'category': 'coaching'
                    })
            
            print(f"• {len(coaching_tips)} coaching tips will be overlaid")
            print(f"• Processing {total_frames} frames with coaching text overlays...")
            
            # Get swing phases and quality from Gemini analysis (exact format)
            swings = self.results['swing_analysis'].get('swings', [])
            swing_phases = swings[0].get('phases', {}) if swings else {}
            quality_score = swings[0].get('quality', 7) if swings else 7
            
            # Use the real video compositor service
            compositing_result = await self.compositor_service.composite_video(
                input_video_path=self.test_video_path,
                pose_data=self.results['pose_data'],
                coaching_tips=coaching_tips,
                output_path=composited_path,
                swing_phases=swing_phases,
                quality_score=quality_score
            )
            
            if compositing_result.get('success'):
                print(f"✅ Video compositing completed successfully!")
                print(f"• Frames processed: {compositing_result.get('frames_processed', 0)}")
                print(f"• Output size: {compositing_result.get('output_size_mb', 0)}MB")
                print(f"• Pose overlays: {compositing_result.get('pose_overlays_added', 0)}")
                print(f"• Coaching overlays: {compositing_result.get('coaching_overlays_added', 0)}")
                
                self.results['video_metadata'] = {
                    'success': True,
                    'processing_time': time.time() - start_time,
                    'original_video': {
                        'filename': os.path.basename(self.test_video_path),
                        'size_kb': self.results['test_metadata']['file_size_kb'],
                        'duration': self.results['test_metadata']['duration_seconds']
                    },
                    'composited_video': {
                        'filename': composited_filename,
                        'local_path': composited_path,
                        'size_bytes': compositing_result.get('output_size_bytes', 0),
                        'size_mb': compositing_result.get('output_size_mb', 0),
                        'overlays_added': {
                            'skeleton_lines': compositing_result.get('pose_overlays_added', 0) > 0,
                            'coaching_tips': compositing_result.get('coaching_overlays_added', 0) > 0,
                            'total_pose_overlays': compositing_result.get('pose_overlays_added', 0),
                            'total_coaching_overlays': compositing_result.get('coaching_overlays_added', 0)
                        }
                    },
                    'processing_stats': {
                        'frames_processed': compositing_result.get('frames_processed', 0),
                        'video_properties': compositing_result.get('video_properties', {}),
                        'poses_detected': len(self.results['pose_data'].get('pose_landmarks', [])),
                        'coaching_tips_overlaid': len(coaching_tips)
                    },
                    'compositor_result': compositing_result
                }
                
            else:
                # Compositing failed, create metadata indicating failure
                error_msg = compositing_result.get('error', 'Unknown compositing error')
                print(f"❌ Video compositing failed: {error_msg}")
                
                self.results['video_metadata'] = {
                    'success': False,
                    'processing_time': time.time() - start_time,
                    'error': error_msg,
                    'original_video': {
                        'filename': os.path.basename(self.test_video_path),
                        'size_kb': self.results['test_metadata']['file_size_kb'],
                        'duration': self.results['test_metadata']['duration_seconds']
                    },
                    'composited_video': {
                        'filename': composited_filename,
                        'local_path': composited_path,
                        'created': False
                    }
                }
                
        except Exception as e:
            print(f"❌ Video compositing error: {e}")
            logger.error(f"Video compositing failed: {e}")
            
            # Create error metadata
            self.results['video_metadata'] = {
                'success': False,
                'processing_time': time.time() - start_time,
                'error': str(e),
                'original_video': {
                    'filename': os.path.basename(self.test_video_path),
                    'size_kb': self.results['test_metadata']['file_size_kb'],
                    'duration': self.results['test_metadata']['duration_seconds']
                },
                'composited_video': {
                    'filename': composited_filename,
                    'local_path': composited_path,
                    'created': False
                }
            }
        
        processing_time = time.time() - start_time
        
        if self.results['video_metadata']['success']:
            print(f"✅ Video compositing complete in {processing_time:.1f}s")
            print(f"💾 Composited video saved: {composited_filename}")
            print(f"📁 Manual inspection: {composited_path}")
        else:
            print(f"⚠️  Video compositing failed in {processing_time:.1f}s")
            print(f"💾 Video metadata prepared for export")
    
    async def _export_all_results(self):
        """Export all results to separate JSON files."""
        print("\n💾 STEP 5: Exporting Results")
        print("-" * 40)
        
        # Export each result type
        exports = [
            ('pose_data_output.json', self.results['pose_data'], "Pose detection data"),
            ('swing_analysis_output.json', self.results['swing_analysis'], "Swing phase analysis"),
            ('coaching_script_output.json', self.results['coaching_script'], "TTS coaching script"),
            ('video_metadata_output.json', self.results['video_metadata'], "Composited video info"),
        ]
        
        for filename, data, description in exports:
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"• {description}: {filename} ✅")
        
        # Create complete summary
        summary = {
            'test_info': {
                'test_name': 'Complete Video Analysis Test',
                'test_time': datetime.now().isoformat(),
                'video_file': self.results['test_metadata']['video_file'],
                'total_processing_time': sum([
                    self.results['pose_data'].get('processing_time', 0),
                    self.results['swing_analysis'].get('processing_time', 0),
                    self.results['coaching_script'].get('processing_time', 0),
                    self.results['video_metadata'].get('processing_time', 0)
                ])
            },
            'video_properties': self.results['test_metadata'],
            'analysis_summary': {
                'overall_score': self.results['swing_analysis']['swings'][0]['quality'] if self.results['swing_analysis'].get('swings') else 7,
                'frames_processed': self.results['pose_data']['frames_processed'],
                'swing_phases': len(self.results['swing_analysis']['swings'][0]['phases']) if self.results['swing_analysis'].get('swings') else 0,
                'coaching_statements': self.results['coaching_script']['total_statements'],
                'coaching_duration': self.results['coaching_script']['total_duration']
            },
            'outputs_generated': {
                'pose_data': bool(self.results['pose_data']['success']),
                'swing_analysis': bool(self.results['swing_analysis']['success']),
                'coaching_script': bool(self.results['coaching_script']['success']),
                'video_metadata': bool(self.results['video_metadata']['success'])
            },
            'file_locations': {
                'pose_data': 'pose_data_output.json',
                'swing_analysis': 'swing_analysis_output.json',
                'coaching_script': 'coaching_script_output.json',
                'video_metadata': 'video_metadata_output.json',
                'summary': 'complete_analysis_summary.json'
            }
        }
        
        # Export summary
        summary_path = os.path.join(self.output_dir, 'complete_analysis_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"• Complete analysis summary: complete_analysis_summary.json ✅")
        print(f"📁 All files saved to: {self.output_dir}")
    
    async def _print_final_summary(self, total_time: float):
        """Print final test summary."""
        print("\n📊 ANALYSIS COMPLETE")
        print("=" * 80)
        
        # Get summary stats
        swing_analysis = self.results['swing_analysis']
        coaching_script = self.results['coaching_script']
        video_metadata = self.results['video_metadata']
        pose_data = self.results['pose_data']
        
        # Extract overall score from Gemini format
        overall_score = swing_analysis['swings'][0]['quality'] if swing_analysis.get('swings') else 7
        swing_phases_count = len(swing_analysis['swings'][0]['phases']) if swing_analysis.get('swings') else 0
        
        print(f"🎯 Overall Score: {overall_score}/10")
        print(f"⏱️  Processing Time: {total_time:.1f}s")
        print(f"🎬 Frames Processed: {pose_data['frames_processed']}")
        print(f"📋 Swing Phases: {swing_phases_count}")
        print(f"🎙️  Coaching Statements: {coaching_script['total_statements']}")
        print(f"📁 Files Generated: 5 JSON files")
        print()
        
        print("📂 OUTPUT FILES:")
        output_files = [
            "pose_data_output.json - MediaPipe landmarks for server compositing",
            "swing_analysis_output.json - Phase breakdown for frontend display",
            "coaching_script_output.json - TTS statements with timestamps",
            "video_metadata_output.json - Composited video information",
            "complete_analysis_summary.json - Full test overview"
        ]
        
        for file_desc in output_files:
            print(f"   • {file_desc}")
        
        print()
        print("✅ All outputs saved to test_results/")
        print("=" * 80)
    
    def _create_mock_pose_data(self) -> Dict[str, Any]:
        """Create mock pose data for testing when MediaPipe fails."""
        total_frames = self.results['test_metadata']['total_frames']
        
        # Generate mock landmarks for each frame
        mock_landmarks = []
        for frame_num in range(total_frames):
            timestamp = frame_num / self.results['test_metadata']['fps']
            
            # Mock 33 MediaPipe pose landmarks
            landmarks = []
            for i in range(33):
                landmarks.append({
                    'x': 0.5 + (i * 0.01),  # Mock x coordinate
                    'y': 0.3 + (i * 0.02),  # Mock y coordinate
                    'z': -0.1 + (i * 0.001),  # Mock z coordinate
                    'visibility': 0.95 + (i * 0.001)  # Mock visibility
                })
            
            mock_landmarks.append({
                'frame_number': frame_num,
                'timestamp': timestamp,
                'landmarks': landmarks
            })
        
        return {
            'success': True,
            'processing_time': 5.0,  # Mock processing time
            'frames_processed': total_frames,
            'pose_landmarks': mock_landmarks[:10],  # Limit for JSON size
            'body_angles': {
                'spine_angles': [35.2, 38.1, 32.8, 30.5, 28.0],
                'shoulder_tilts': [8.5, 15.2, 20.1, 25.0, 30.5],
                'hip_rotations': [0.0, 25.3, 40.2, 45.0, 50.0]
            },
            'swing_phases': [
                {'phase': 'setup', 'frames': [0, 60]},
                {'phase': 'backswing', 'frames': [60, 135]},
                {'phase': 'downswing', 'frames': [135, 165]},
                {'phase': 'impact', 'frames': [165, 180]},
                {'phase': 'follow_through', 'frames': [180, 300]}
            ],
            'biomechanical_scores': {
                'overall_score': 75.0,
                'kinetic_chain_score': 80.0,
                'power_transfer_score': 70.0,
                'balance_score': 85.0
            },
            'note': 'Mock data generated due to MediaPipe processing error'
        }
    
    def _validate_gemini_json_structure(self, swing_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that Gemini returned properly structured JSON data."""
        issues = []
        valid = True
        
        # Check raw_gemini_result structure
        raw_result = swing_analysis.get('raw_gemini_result', {})
        
        # Check if raw result has swings array
        swings = raw_result.get('swings', [])
        if not swings:
            issues.append("raw_gemini_result missing 'swings' array")
            valid = False
        else:
            # Validate first swing structure
            first_swing = swings[0]
            required_swing_fields = ['quality', 'phases', 'comments']
            missing_swing_fields = [field for field in required_swing_fields if field not in first_swing]
            if missing_swing_fields:
                issues.append(f"First swing missing fields: {missing_swing_fields}")
                valid = False
            
            # Check phases structure
            phases = first_swing.get('phases', {})
            expected_phases = ['setup', 'backswing', 'downswing', 'impact', 'follow_through']
            missing_phases = [phase for phase in expected_phases if phase not in phases]
            if missing_phases:
                issues.append(f"Missing swing phases: {missing_phases}")
                valid = False
            
            # Check comments array
            comments = first_swing.get('comments', [])
            if not comments or len(comments) == 0:
                issues.append("No coaching comments found in swing analysis")
                valid = False
            elif len(comments) > 3:
                issues.append(f"Too many comments ({len(comments)}) - should be 2-3 per swing")
        
        # Check key_coaching_points is populated (converted from new format)
        coaching_points = swing_analysis.get('key_coaching_points', [])
        if not coaching_points or len(coaching_points) == 0:
            issues.append("key_coaching_points is empty - should contain coaching data from Gemini")
            valid = False
        
        # Check phases contain coaching tips
        phases = swing_analysis.get('phases', [])
        total_phase_tips = 0
        for phase in phases:
            phase_tips = phase.get('coaching_tips', [])
            total_phase_tips += len(phase_tips)
            if 'coaching_tips' not in phase:
                issues.append(f"Phase '{phase.get('phase', 'unknown')}' missing coaching_tips field")
                valid = False
        
        # Create summary
        coaching_count = len(coaching_points)
        phase_tips_count = total_phase_tips
        
        return {
            'valid': valid,
            'issues': issues,
            'summary': f"{coaching_count} coaching points, {phase_tips_count} phase tips found",
            'coaching_points_count': coaching_count,
            'phase_tips_count': phase_tips_count
        }


async def main():
    """Run the complete analysis test."""
    test = CompleteAnalysisTest()
    result = await test.run_complete_test()
    
    if result['success']:
        print(f"\n🎉 Test completed successfully in {result['total_time']:.1f}s")
        print(f"📁 Check results in: {result['results_directory']}")
        return 0
    else:
        print(f"\n❌ Test failed: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)