#!/usr/bin/env python3
"""
Video Pipeline Demonstration Script
Shows the complete video analysis workflow in action with detailed logging.
"""

import asyncio
import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'pipeline_demo_{int(time.time())}.log')
    ]
)
logger = logging.getLogger(__name__)

# Import services
from services.video_pipeline_service import get_video_pipeline_service
from database.config import get_db_session
from models.user import User
from models.video import Video
from models.video_analysis import VideoAnalysis


class VideoPipelineDemo:
    """Demonstration of the complete video processing pipeline."""
    
    def __init__(self):
        self.pipeline_service = get_video_pipeline_service()
        self.demo_user_id = None
        self.test_video_path = os.path.join(
            os.path.dirname(__file__), 
            "tests", 
            "test_video.mov"
        )
        
        # Progress tracking for demo
        self.progress_log = []
        
    async def run_demo(self) -> Dict[str, Any]:
        """Run the complete pipeline demonstration."""
        print("🎬 " + "=" * 78)
        print("🎬 FUTUREGOLF VIDEO ANALYSIS PIPELINE DEMONSTRATION")
        print("🎬 " + "=" * 78)
        
        demo_results = {
            'demo_started': datetime.now().isoformat(),
            'steps': [],
            'overall_success': True,
            'demo_completed': None
        }
        
        try:
            # Step 1: Setup demonstration environment
            print("\n📋 STEP 1: Setting up demonstration environment")
            await self._setup_demo_environment()
            demo_results['steps'].append('Demo environment setup complete')
            
            # Step 2: Pipeline health check
            print("\n🔍 STEP 2: Checking pipeline health")
            health_status = await self._demonstrate_health_check()
            demo_results['steps'].append(f'Health check: {health_status}')
            
            # Step 3: Video file validation
            print("\n🎞️ STEP 3: Validating test video")
            video_info = await self._validate_test_video()
            demo_results['steps'].append(f'Video validation: {video_info}')
            
            # Step 4: Complete pipeline execution with live progress
            print("\n🚀 STEP 4: Executing complete video analysis pipeline")
            pipeline_result = await self._demonstrate_complete_pipeline()
            demo_results['steps'].append(f'Pipeline execution: {pipeline_result["success"]}')
            
            # Step 5: Detailed results analysis
            print("\n📊 STEP 5: Analyzing results")
            results_analysis = await self._analyze_pipeline_results(pipeline_result)
            demo_results['steps'].append(f'Results analysis: {results_analysis["success"]}')
            
            # Step 6: Database verification
            print("\n🗄️ STEP 6: Verifying database storage")
            db_verification = await self._verify_database_storage()
            demo_results['steps'].append(f'Database verification: {db_verification["success"]}')
            
            # Step 7: API endpoint simulation
            print("\n🔗 STEP 7: Demonstrating API integration")
            api_demo = await self._demonstrate_api_integration()
            demo_results['steps'].append(f'API integration: {api_demo["success"]}')
            
            demo_results['demo_completed'] = datetime.now().isoformat()
            
            # Final summary
            print("\n" + "=" * 80)
            print("🎉 DEMONSTRATION COMPLETE!")
            print("=" * 80)
            
            return demo_results
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            demo_results['overall_success'] = False
            demo_results['error'] = str(e)
            demo_results['demo_completed'] = datetime.now().isoformat()
            return demo_results
    
    async def _setup_demo_environment(self):
        """Setup the demonstration environment."""
        print("   📝 Creating demo user account...")
        
        # Create demo user
        session_gen = get_db_session()
        session = await session_gen.__anext__()
        try:
            from sqlalchemy import select
            
            # Check for existing demo user
            result = await session.execute(
                select(User).filter(User.email == "demo@futuregolf.com")
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    email="demo@futuregolf.com",
                    username="demouser",
                    first_name="Demo",
                    last_name="User",
                    password_hash="demo_hash"
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            self.demo_user_id = user.id
            print(f"   ✅ Demo user ready (ID: {self.demo_user_id})")
        finally:
            await session_gen.aclose()
        
        print("   📂 Checking test video file...")
        if os.path.exists(self.test_video_path):
            file_size = os.path.getsize(self.test_video_path)
            print(f"   ✅ Test video found ({file_size / 1024:.1f} KB)")
        else:
            raise FileNotFoundError(f"Test video not found: {self.test_video_path}")
    
    async def _demonstrate_health_check(self) -> str:
        """Demonstrate pipeline health check."""
        print("   🔍 Checking all pipeline components...")
        
        health_status = await self.pipeline_service.validate_pipeline_health()
        
        print(f"   📊 Pipeline Health: {'✅ HEALTHY' if health_status['pipeline_healthy'] else '❌ UNHEALTHY'}")
        
        # Show component status
        for component, status in health_status['components'].items():
            icon = "✅" if status['healthy'] else "❌"
            print(f"   {icon} {component.upper()}: {status['message']}")
        
        return "healthy" if health_status['pipeline_healthy'] else "unhealthy"
    
    async def _validate_test_video(self) -> str:
        """Validate the test video file."""
        print("   🎞️ Analyzing test video properties...")
        
        # Basic file validation
        if not os.path.exists(self.test_video_path):
            raise FileNotFoundError("Test video not found")
        
        file_size = os.path.getsize(self.test_video_path)
        file_name = os.path.basename(self.test_video_path)
        
        print(f"   📁 File: {file_name}")
        print(f"   📏 Size: {file_size / 1024:.1f} KB")
        print(f"   📍 Path: {self.test_video_path}")
        
        # Try to get video info with opencv
        try:
            import cv2
            cap = cv2.VideoCapture(self.test_video_path)
            if cap.isOpened():
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = frame_count / fps if fps > 0 else 0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                print(f"   🎬 Duration: {duration:.1f} seconds")
                print(f"   📐 Resolution: {width}x{height}")
                print(f"   🎪 FPS: {fps:.1f}")
                print(f"   📹 Frames: {frame_count}")
                
                cap.release()
            else:
                print("   ⚠️ Could not open video file with OpenCV")
        except Exception as e:
            print(f"   ⚠️ Video analysis failed: {e}")
        
        return "valid"
    
    async def _demonstrate_complete_pipeline(self) -> Dict[str, Any]:
        """Demonstrate the complete pipeline with live progress."""
        print("   🚀 Starting complete video analysis pipeline...")
        
        # Progress tracking
        progress_updates = []
        
        async def demo_progress_callback(progress_data):
            progress_updates.append(progress_data)
            progress = progress_data['progress']
            message = progress_data['message']
            
            # Create progress bar
            bar_length = 40
            filled_length = int(bar_length * progress / 100)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            print(f"   📊 [{bar}] {progress:3.0f}% - {message}")
            
            # Add small delay to show progress
            await asyncio.sleep(0.1)
        
        # Execute pipeline
        start_time = time.time()
        pipeline_result = await self.pipeline_service.process_video_complete(
            self.test_video_path,
            self.demo_user_id,
            "Demo Golf Swing Analysis",
            demo_progress_callback
        )
        duration = time.time() - start_time
        
        print(f"   ⏱️ Pipeline execution time: {duration:.2f} seconds")
        print(f"   📋 Progress updates received: {len(progress_updates)}")
        
        if pipeline_result['success']:
            print("   ✅ Pipeline execution completed successfully!")
            print(f"   📊 Pipeline ID: {pipeline_result['pipeline_id']}")
            print(f"   🎞️ Video ID: {pipeline_result['video_id']}")
            print(f"   📈 Analysis ID: {pipeline_result['analysis_id']}")
        else:
            print("   ❌ Pipeline execution failed!")
            print(f"   🚨 Error: {pipeline_result.get('error', 'Unknown error')}")
        
        return pipeline_result
    
    async def _analyze_pipeline_results(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the pipeline results in detail."""
        print("   📊 Analyzing pipeline results...")
        
        if not pipeline_result['success']:
            print("   ❌ Cannot analyze results - pipeline failed")
            return {'success': False, 'reason': 'Pipeline failed'}
        
        results = pipeline_result.get('results', {})
        
        print("   📋 Result Components:")
        
        # Video info
        video_info = results.get('video_info', {})
        if video_info:
            print(f"   📹 Video Record: ID {video_info.get('id')}, Title: '{video_info.get('title')}'")
        
        # Analysis info
        analysis_info = results.get('analysis_info', {})
        if analysis_info:
            print(f"   📈 Analysis Record: ID {analysis_info.get('id')}, Status: {analysis_info.get('status')}")
        
        # AI Analysis
        ai_analysis = results.get('ai_analysis', {})
        if ai_analysis:
            print(f"   🤖 AI Analysis: Score {ai_analysis.get('overall_score', 0)}/10")
            print(f"   📊 Confidence: {ai_analysis.get('confidence', 0):.1%}")
            coaching_points = ai_analysis.get('coaching_points', [])
            print(f"   💡 Coaching Points: {len(coaching_points)}")
        
        # Pose Analysis
        pose_analysis = results.get('pose_analysis', {})
        if pose_analysis and pose_analysis.get('success'):
            print(f"   🏃 Pose Analysis: {pose_analysis.get('analysis_metadata', {}).get('total_frames', 0)} frames")
            biomech_scores = pose_analysis.get('biomechanical_efficiency', {})
            if biomech_scores:
                overall_score = biomech_scores.get('overall_score', 0)
                print(f"   💪 Biomechanical Score: {overall_score:.1f}/100")
        
        # Summary
        summary = results.get('summary', {})
        if summary:
            print(f"   📝 Summary: {len(summary.get('key_insights', []))} insights, {len(summary.get('recommendations', []))} recommendations")
        
        print("   ✅ Results analysis complete!")
        return {'success': True, 'components_analyzed': len(results)}
    
    async def _verify_database_storage(self) -> Dict[str, Any]:
        """Verify that all data was stored correctly in the database."""
        print("   🗄️ Verifying database storage...")
        
        try:
            session_gen = get_db_session()
            session = await session_gen.__anext__()
            try:
                from sqlalchemy import select
                
                # Check video records
                video_result = await session.execute(
                    select(Video).filter(Video.user_id == self.demo_user_id)
                    .order_by(Video.created_at.desc())
                )
                videos = video_result.scalars().all()
                
                # Check analysis records
                analysis_result = await session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.user_id == self.demo_user_id)
                    .order_by(VideoAnalysis.created_at.desc())
                )
                analyses = analysis_result.scalars().all()
            finally:
                await session_gen.aclose()
                
                print(f"   📊 Total videos in database: {len(videos)}")
                print(f"   📈 Total analyses in database: {len(analyses)}")
                
                if videos:
                    latest_video = videos[0]
                    print(f"   🎞️ Latest video: ID {latest_video.id}, '{latest_video.title}'")
                    print(f"   📂 Blob name: {latest_video.blob_name}")
                    print(f"   📏 File size: {latest_video.file_size} bytes")
                
                if analyses:
                    latest_analysis = analyses[0]
                    print(f"   📈 Latest analysis: ID {latest_analysis.id}, Status: {latest_analysis.status.value}")
                    print(f"   🤖 Has AI analysis: {'Yes' if latest_analysis.ai_analysis else 'No'}")
                    print(f"   🏃 Has pose data: {'Yes' if latest_analysis.pose_data else 'No'}")
                    print(f"   💪 Has body angles: {'Yes' if latest_analysis.body_position_data else 'No'}")
                    print(f"   📊 Has swing metrics: {'Yes' if latest_analysis.swing_metrics else 'No'}")
                    print(f"   🎯 Confidence: {latest_analysis.analysis_confidence or 0:.1%}")
                
                print("   ✅ Database verification complete!")
                return {'success': True, 'videos': len(videos), 'analyses': len(analyses)}
                
        except Exception as e:
            print(f"   ❌ Database verification failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _demonstrate_api_integration(self) -> Dict[str, Any]:
        """Demonstrate API integration capabilities."""
        print("   🔗 Demonstrating API integration...")
        
        try:
            # Get the video analysis service
            from services.video_analysis_service import get_video_analysis_service
            video_analysis_service = get_video_analysis_service()
            
            # Find the latest analysis
            session_gen = get_db_session()
            session = await session_gen.__anext__()
            try:
                from sqlalchemy import select
                
                analysis_result = await session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.user_id == self.demo_user_id)
                    .order_by(VideoAnalysis.created_at.desc())
                )
                latest_analysis = analysis_result.scalar_one_or_none()
                
                if not latest_analysis:
                    print("   ❌ No analysis found for API demo")
                    return {'success': False, 'reason': 'No analysis found'}
                
                print(f"   📊 Testing API with analysis ID: {latest_analysis.id}")
                
                # Test API methods
                api_results = {}
                
                # Test 1: Get analysis status
                print("   🔍 Testing analysis status retrieval...")
                status = await video_analysis_service.get_analysis_status(
                    latest_analysis.id, self.demo_user_id
                )
                api_results['status_retrieval'] = bool(status)
                print(f"   ✅ Status: {status.get('status', 'unknown')}")
                
                # Test 2: Get analysis results (if completed)
                if latest_analysis.is_completed:
                    print("   📊 Testing analysis results retrieval...")
                    results = await video_analysis_service.get_analysis_results(
                        latest_analysis.id, self.demo_user_id
                    )
                    api_results['results_retrieval'] = bool(results)
                    print(f"   ✅ Results retrieved: {len(results)} keys")
                else:
                    print("   ⏳ Analysis not completed - skipping results retrieval")
                    api_results['results_retrieval'] = True  # Skip this test
                
                # Test 3: Simulate API endpoints
                print("   🌐 Simulating API endpoint responses...")
                
                # Simulate what the API endpoints would return
                endpoint_simulations = {
                    'GET /api/v1/video-analysis/status/{id}': {
                        'success': True,
                        'status': status
                    },
                    'GET /api/v1/video-analysis/video/{video_id}': {
                        'success': True,
                        'analysis': {
                            'id': latest_analysis.id,
                            'status': latest_analysis.status.value,
                            'has_results': latest_analysis.is_completed
                        }
                    }
                }
            finally:
                await session_gen.aclose()
                
                for endpoint, response in endpoint_simulations.items():
                    print(f"   🎯 {endpoint}: {'✅ Success' if response['success'] else '❌ Failed'}")
                
                print("   ✅ API integration demonstration complete!")
                return {'success': True, 'api_tests': api_results}
                
        except Exception as e:
            print(f"   ❌ API integration demo failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def save_demo_results(self, results: Dict[str, Any]):
        """Save demonstration results to file."""
        try:
            results_file = os.path.join(
                os.path.dirname(__file__), 
                f"pipeline_demo_results_{int(time.time())}.json"
            )
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"📄 Demo results saved to: {results_file}")
            
        except Exception as e:
            print(f"❌ Failed to save demo results: {e}")


async def main():
    """Run the video pipeline demonstration."""
    demo = VideoPipelineDemo()
    
    # Run the demonstration
    results = await demo.run_demo()
    
    # Save results
    await demo.save_demo_results(results)
    
    # Final summary
    print("\n🎬 " + "=" * 78)
    print("🎬 DEMONSTRATION SUMMARY")
    print("🎬 " + "=" * 78)
    
    print(f"🏁 Overall Result: {'✅ SUCCESS' if results['overall_success'] else '❌ FAILED'}")
    print(f"⏰ Started: {results['demo_started']}")
    print(f"🏁 Completed: {results.get('demo_completed', 'N/A')}")
    print(f"📝 Steps Completed: {len(results['steps'])}")
    
    print("\n📋 Step Details:")
    for i, step in enumerate(results['steps'], 1):
        print(f"   {i}. {step}")
    
    if 'error' in results:
        print(f"\n🚨 Error: {results['error']}")
    
    print("\n🎬 " + "=" * 78)
    print("🎬 Thank you for watching the FutureGolf Pipeline Demo!")
    print("🎬 " + "=" * 78)
    
    return results['overall_success']


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)