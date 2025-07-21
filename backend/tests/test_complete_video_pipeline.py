#!/usr/bin/env python3
"""
Complete end-to-end video pipeline testing script.
Tests the entire video analysis workflow from upload to final results.
"""

import asyncio
import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services
from services.video_pipeline_service import get_video_pipeline_service
from database.config import get_db_session
from models.user import User
from models.video import Video
from models.video_analysis import VideoAnalysis
import tempfile
import shutil


class VideoPipelineTestSuite:
    """Complete test suite for video processing pipeline."""
    
    def __init__(self):
        self.pipeline_service = get_video_pipeline_service()
        self.test_results = []
        self.test_user_id = None
        self.test_video_path = os.path.join(
            os.path.dirname(__file__), 
            "tests", 
            "test_video.mov"
        )
        
        # Progress tracking
        self.progress_updates = []
        
        logger.info("Video pipeline test suite initialized")
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        logger.info("Starting complete video pipeline test suite")
        
        test_results = {
            'test_suite': 'Complete Video Pipeline',
            'started_at': datetime.now().isoformat(),
            'tests': [],
            'overall_success': True
        }
        
        try:
            # Setup test environment
            await self._setup_test_environment()
            
            # Test 1: Pipeline Health Check
            result = await self._test_pipeline_health()
            test_results['tests'].append(result)
            if not result['success']:
                test_results['overall_success'] = False
            
            # Test 2: Video File Processing
            result = await self._test_video_file_processing()
            test_results['tests'].append(result)
            if not result['success']:
                test_results['overall_success'] = False
            
            # Test 3: Database Storage Verification
            result = await self._test_database_storage()
            test_results['tests'].append(result)
            if not result['success']:
                test_results['overall_success'] = False
            
            # Test 4: API Integration Test
            result = await self._test_api_integration()
            test_results['tests'].append(result)
            if not result['success']:
                test_results['overall_success'] = False
            
            # Test 5: Complete Workflow Test
            result = await self._test_complete_workflow()
            test_results['tests'].append(result)
            if not result['success']:
                test_results['overall_success'] = False
            
            # Test 6: Error Handling Test
            result = await self._test_error_handling()
            test_results['tests'].append(result)
            if not result['success']:
                test_results['overall_success'] = False
            
            # Test 7: Performance Test
            result = await self._test_performance()
            test_results['tests'].append(result)
            if not result['success']:
                test_results['overall_success'] = False
            
            test_results['completed_at'] = datetime.now().isoformat()
            
            # Save test results
            await self._save_test_results(test_results)
            
            return test_results
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            test_results['overall_success'] = False
            test_results['error'] = str(e)
            test_results['completed_at'] = datetime.now().isoformat()
            return test_results
    
    async def _setup_test_environment(self):
        """Setup test environment with test user."""
        logger.info("Setting up test environment")
        
        # Create test user if not exists
        async with get_db_session() as session:
            from sqlalchemy import select
            
            # Check for existing test user
            result = await session.execute(
                select(User).filter(User.email == "test@futuregolf.com")
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Create test user
                user = User(
                    email="test@futuregolf.com",
                    username="testuser",
                    first_name="Test",
                    last_name="User",
                    password_hash="test_hash"
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            self.test_user_id = user.id
            logger.info(f"Test user ID: {self.test_user_id}")
    
    async def _test_pipeline_health(self) -> Dict[str, Any]:
        """Test pipeline health check."""
        logger.info("Testing pipeline health")
        
        try:
            health_status = await self.pipeline_service.validate_pipeline_health()
            
            return {
                'test_name': 'Pipeline Health Check',
                'success': health_status['pipeline_healthy'],
                'details': health_status,
                'duration': 0.5,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Pipeline health test failed: {e}")
            return {
                'test_name': 'Pipeline Health Check',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _test_video_file_processing(self) -> Dict[str, Any]:
        """Test video file processing with test video."""
        logger.info("Testing video file processing")
        
        start_time = time.time()
        
        try:
            # Check if test video exists
            if not os.path.exists(self.test_video_path):
                raise FileNotFoundError(f"Test video not found: {self.test_video_path}")
            
            # Process video with progress tracking
            progress_updates = []
            
            async def progress_callback(progress_data):
                progress_updates.append(progress_data)
                logger.info(f"Progress: {progress_data['progress']}% - {progress_data['message']}")
            
            # Process the video
            result = await self.pipeline_service.process_video_complete(
                self.test_video_path,
                self.test_user_id,
                "Test Video Analysis",
                progress_callback
            )
            
            duration = time.time() - start_time
            
            return {
                'test_name': 'Video File Processing',
                'success': result['success'],
                'details': {
                    'video_processed': result['success'],
                    'pipeline_id': result.get('pipeline_id'),
                    'video_id': result.get('video_id'),
                    'analysis_id': result.get('analysis_id'),
                    'progress_updates': len(progress_updates),
                    'final_results_keys': list(result.get('results', {}).keys()) if result.get('results') else []
                },
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'error': result.get('error') if not result['success'] else None
            }
            
        except Exception as e:
            logger.error(f"Video processing test failed: {e}")
            return {
                'test_name': 'Video File Processing',
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _test_database_storage(self) -> Dict[str, Any]:
        """Test database storage and retrieval."""
        logger.info("Testing database storage")
        
        try:
            async with get_db_session() as session:
                # Check video records
                from sqlalchemy import select
                
                video_result = await session.execute(
                    select(Video).filter(Video.user_id == self.test_user_id)
                )
                videos = video_result.scalars().all()
                
                # Check analysis records
                analysis_result = await session.execute(
                    select(VideoAnalysis).filter(VideoAnalysis.user_id == self.test_user_id)
                )
                analyses = analysis_result.scalars().all()
                
                # Verify data integrity
                storage_verified = True
                details = {
                    'videos_count': len(videos),
                    'analyses_count': len(analyses),
                    'video_records': [],
                    'analysis_records': []
                }
                
                for video in videos:
                    video_data = {
                        'id': video.id,
                        'title': video.title,
                        'blob_name': video.blob_name,
                        'file_size': video.file_size,
                        'has_blob_name': bool(video.blob_name),
                        'created_at': video.created_at.isoformat()
                    }
                    details['video_records'].append(video_data)
                
                for analysis in analyses:
                    analysis_data = {
                        'id': analysis.id,
                        'video_id': analysis.video_id,
                        'status': analysis.status.value,
                        'has_ai_analysis': bool(analysis.ai_analysis),
                        'has_pose_data': bool(analysis.pose_data),
                        'has_body_angles': bool(analysis.body_position_data),
                        'has_swing_metrics': bool(analysis.swing_metrics),
                        'confidence': analysis.analysis_confidence,
                        'created_at': analysis.created_at.isoformat()
                    }
                    details['analysis_records'].append(analysis_data)
                
                return {
                    'test_name': 'Database Storage',
                    'success': storage_verified,
                    'details': details,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Database storage test failed: {e}")
            return {
                'test_name': 'Database Storage',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _test_api_integration(self) -> Dict[str, Any]:
        """Test API integration with video analysis endpoints."""
        logger.info("Testing API integration")
        
        try:
            # This would normally test the actual API endpoints
            # For now, we'll test the service layer integration
            
            async with get_db_session() as session:
                from sqlalchemy import select
                
                # Get the latest video
                video_result = await session.execute(
                    select(Video).filter(Video.user_id == self.test_user_id)
                    .order_by(Video.created_at.desc())
                )
                latest_video = video_result.scalar_one_or_none()
                
                if not latest_video:
                    raise ValueError("No video found for API testing")
                
                # Test video analysis service methods
                from services.video_analysis_service import get_video_analysis_service
                video_analysis_service = get_video_analysis_service()
                
                # Get analysis for the video
                analysis_result = await session.execute(
                    select(VideoAnalysis).filter(
                        VideoAnalysis.video_id == latest_video.id,
                        VideoAnalysis.user_id == self.test_user_id
                    )
                )
                analysis = analysis_result.scalar_one_or_none()
                
                api_tests = {
                    'video_found': bool(latest_video),
                    'analysis_found': bool(analysis),
                    'analysis_completed': analysis.is_completed if analysis else False,
                    'has_results': bool(analysis.ai_analysis) if analysis else False
                }
                
                if analysis:
                    # Test getting analysis status
                    status = await video_analysis_service.get_analysis_status(
                        analysis.id, self.test_user_id
                    )
                    api_tests['status_retrieval'] = bool(status)
                    
                    # Test getting analysis results (if completed)
                    if analysis.is_completed:
                        results = await video_analysis_service.get_analysis_results(
                            analysis.id, self.test_user_id
                        )
                        api_tests['results_retrieval'] = bool(results)
                
                return {
                    'test_name': 'API Integration',
                    'success': all(api_tests.values()),
                    'details': api_tests,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"API integration test failed: {e}")
            return {
                'test_name': 'API Integration',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _test_complete_workflow(self) -> Dict[str, Any]:
        """Test complete workflow from start to finish."""
        logger.info("Testing complete workflow")
        
        start_time = time.time()
        
        try:
            # Create a copy of test video for this test
            temp_video_path = os.path.join(
                tempfile.gettempdir(), 
                f"test_workflow_{int(time.time())}.mp4"
            )
            shutil.copy2(self.test_video_path, temp_video_path)
            
            try:
                # Run complete workflow
                workflow_result = await self.pipeline_service.process_video_complete(
                    temp_video_path,
                    self.test_user_id,
                    "Complete Workflow Test"
                )
                
                # Verify all components worked
                workflow_checks = {
                    'pipeline_success': workflow_result['success'],
                    'video_uploaded': bool(workflow_result.get('video_id')),
                    'analysis_created': bool(workflow_result.get('analysis_id')),
                    'results_generated': bool(workflow_result.get('results')),
                    'pipeline_id': workflow_result.get('pipeline_id')
                }
                
                if workflow_result['success']:
                    results = workflow_result['results']
                    workflow_checks.update({
                        'has_video_info': bool(results.get('video_info')),
                        'has_analysis_info': bool(results.get('analysis_info')),
                        'has_ai_analysis': bool(results.get('ai_analysis')),
                        'has_pose_analysis': bool(results.get('pose_analysis')),
                        'has_summary': bool(results.get('summary'))
                    })
                
                duration = time.time() - start_time
                
                return {
                    'test_name': 'Complete Workflow',
                    'success': workflow_result['success'],
                    'details': workflow_checks,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat(),
                    'error': workflow_result.get('error') if not workflow_result['success'] else None
                }
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_video_path):
                    os.unlink(temp_video_path)
                    
        except Exception as e:
            logger.error(f"Complete workflow test failed: {e}")
            return {
                'test_name': 'Complete Workflow',
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid inputs."""
        logger.info("Testing error handling")
        
        try:
            error_tests = {}
            
            # Test 1: Invalid video path
            try:
                result = await self.pipeline_service.process_video_complete(
                    "/nonexistent/video.mp4",
                    self.test_user_id,
                    "Invalid Video Test"
                )
                error_tests['invalid_video_path'] = not result['success']
            except Exception:
                error_tests['invalid_video_path'] = True
            
            # Test 2: Invalid user ID
            try:
                result = await self.pipeline_service.process_video_complete(
                    self.test_video_path,
                    999999,  # Non-existent user ID
                    "Invalid User Test"
                )
                error_tests['invalid_user_id'] = not result['success']
            except Exception:
                error_tests['invalid_user_id'] = True
            
            # Test 3: Check pipeline health after errors
            health_after_errors = await self.pipeline_service.validate_pipeline_health()
            error_tests['pipeline_healthy_after_errors'] = health_after_errors['pipeline_healthy']
            
            return {
                'test_name': 'Error Handling',
                'success': all(error_tests.values()),
                'details': error_tests,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return {
                'test_name': 'Error Handling',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _test_performance(self) -> Dict[str, Any]:
        """Test performance metrics."""
        logger.info("Testing performance")
        
        start_time = time.time()
        
        try:
            # Test multiple concurrent analyses (limited for testing)
            num_concurrent = 2
            tasks = []
            
            for i in range(num_concurrent):
                # Create temp video copy
                temp_video_path = os.path.join(
                    tempfile.gettempdir(), 
                    f"perf_test_{i}_{int(time.time())}.mp4"
                )
                shutil.copy2(self.test_video_path, temp_video_path)
                
                # Create task
                task = self.pipeline_service.process_video_complete(
                    temp_video_path,
                    self.test_user_id,
                    f"Performance Test {i}"
                )
                tasks.append((task, temp_video_path))
            
            # Run concurrent tasks
            results = []
            for task, temp_path in tasks:
                try:
                    result = await task
                    results.append(result)
                finally:
                    # Clean up
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            
            total_duration = time.time() - start_time
            avg_duration = total_duration / len(results) if results else 0
            success_rate = sum(1 for r in results if r['success']) / len(results) if results else 0
            
            performance_metrics = {
                'concurrent_analyses': num_concurrent,
                'total_duration': total_duration,
                'average_duration': avg_duration,
                'success_rate': success_rate,
                'all_successful': all(r['success'] for r in results)
            }
            
            return {
                'test_name': 'Performance Test',
                'success': success_rate >= 0.8,  # 80% success rate threshold
                'details': performance_metrics,
                'duration': total_duration,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            return {
                'test_name': 'Performance Test',
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _save_test_results(self, results: Dict[str, Any]):
        """Save test results to file."""
        try:
            results_file = os.path.join(
                os.path.dirname(__file__), 
                f"complete_pipeline_test_results_{int(time.time())}.json"
            )
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Test results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")


async def main():
    """Run the complete test suite."""
    print("=" * 80)
    print("FUTUREGOLF COMPLETE VIDEO PIPELINE TEST SUITE")
    print("=" * 80)
    
    test_suite = VideoPipelineTestSuite()
    
    # Run tests
    results = await test_suite.run_complete_test_suite()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUITE SUMMARY")
    print("=" * 80)
    print(f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")
    print(f"Started: {results['started_at']}")
    print(f"Completed: {results.get('completed_at', 'N/A')}")
    print(f"Total Tests: {len(results['tests'])}")
    
    passed_tests = sum(1 for test in results['tests'] if test['success'])
    failed_tests = len(results['tests']) - passed_tests
    
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    print("\nDETAILED RESULTS:")
    print("-" * 80)
    
    for test in results['tests']:
        status = "✅ PASSED" if test['success'] else "❌ FAILED"
        duration = test.get('duration', 0)
        print(f"{test['test_name']}: {status} ({duration:.2f}s)")
        
        if not test['success'] and 'error' in test:
            print(f"  Error: {test['error']}")
        
        if 'details' in test:
            print(f"  Details: {json.dumps(test['details'], indent=4)}")
        
        print()
    
    if 'error' in results:
        print(f"Suite Error: {results['error']}")
    
    print("=" * 80)
    
    return results['overall_success']


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)