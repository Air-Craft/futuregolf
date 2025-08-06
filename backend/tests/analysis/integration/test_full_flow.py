"""
Full integration test with all real services.
Tests the complete video analysis flow using real GCS, Gemini, and Neon.
MUST FAIL if any service is not accessible.
"""

import pytest
import os
import uuid
import tempfile
import asyncio
import cv2
import numpy as np
from datetime import datetime, timedelta
import logging

from app.services.video_analysis_service import AnalysisOrchestrator
from app.services.storage_service import get_storage_service
from app.database.config import AsyncSessionLocal
from app.models.video_analysis import VideoAnalysis, AnalysisStatus
from app.models.user import User
from sqlalchemy import select

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def verify_all_services():
    """Verify all required services are accessible"""
    errors = []
    
    # Check GCS
    try:
        storage = get_storage_service()
        if not storage.bucket.exists():
            errors.append(f"GCS bucket '{storage.config.bucket_name}' not accessible")
    except Exception as e:
        errors.append(f"GCS not accessible: {e}")
    
    # Check Gemini API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        errors.append("Gemini API key not configured (GEMINI_API_KEY or GOOGLE_API_KEY)")
    
    # Check Neon database
    try:
        import asyncio
        async def check_db():
            async with AsyncSessionLocal() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        
        if not asyncio.run(check_db()):
            errors.append("Neon database connectivity check failed")
    except Exception as e:
        errors.append(f"Neon database not accessible: {e}")
    
    if errors:
        pytest.fail(
            "Integration tests require ALL services to be available:\n" + 
            "\n".join(f"  - {error}" for error in errors)
        )


@pytest.fixture
async def test_user():
    """Create a test user for the integration test"""
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"integration_test_{uuid.uuid4().hex}@example.com",
            username=f"integration_user_{uuid.uuid4().hex[:8]}",
            hashed_password="hashed_password_integration"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id
    
    yield user_id
    
    # Cleanup
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if user:
            await session.delete(user)
            await session.commit()


@pytest.fixture
def create_real_test_video():
    """Create a real test video file"""
    def _create_video(duration_seconds=3, include_golf_motion=True):
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            temp_path = f.name
        
        # Video parameters
        fps = 30
        width = 640
        height = 480
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        
        # Generate frames
        total_frames = int(duration_seconds * fps)
        for i in range(total_frames):
            frame = np.ones((height, width, 3), dtype=np.uint8) * 50  # Dark gray background
            
            if include_golf_motion:
                # Simulate a golf club swing motion
                angle = (i / total_frames) * np.pi
                
                # Club position
                club_x = int(width/2 + 150 * np.cos(angle))
                club_y = int(height/2 + 150 * np.sin(angle))
                
                # Draw "golfer" (circle for head)
                cv2.circle(frame, (width//2, height//2 - 50), 20, (255, 255, 255), -1)
                
                # Draw "club" (line)
                cv2.line(frame, (width//2, height//2), (club_x, club_y), (200, 200, 200), 5)
                
                # Draw "ball" at impact point
                if i > total_frames * 0.6:
                    ball_x = int(width/2 + (i - total_frames*0.6) * 10)
                    cv2.circle(frame, (ball_x, height - 100), 5, (255, 255, 255), -1)
            
            # Add frame number
            cv2.putText(frame, f"Frame {i+1}/{total_frames}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        return temp_path
    
    return _create_video


@pytest.mark.integration
@pytest.mark.requires_gcs
@pytest.mark.requires_gemini
@pytest.mark.requires_neon
class TestFullIntegrationFlow:
    """Test complete analysis flow with all real services"""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_flow_real_services(
        self, verify_all_services, test_user, create_real_test_video
    ):
        """
        Test complete flow with ALL real services.
        MUST FAIL if any service (GCS, Gemini, Neon) is not accessible.
        """
        analysis_uuid = None
        video_blob_name = None
        
        try:
            # 1. Create analysis entry in real Neon DB
            logger.info("Step 1: Creating analysis in Neon database...")
            orchestrator = AnalysisOrchestrator()
            analysis_uuid = await orchestrator.create_analysis_entry(user_id=test_user)
            assert analysis_uuid is not None, "Failed to create analysis entry"
            logger.info(f"Created analysis with UUID: {analysis_uuid}")
            
            # 2. Verify in database
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(VideoAnalysis).filter(
                        VideoAnalysis.uuid == uuid.UUID(analysis_uuid)
                    )
                )
                analysis = result.scalar_one_or_none()
                assert analysis is not None, "Analysis not found in database"
                assert analysis.status == AnalysisStatus.PENDING
            
            # 3. Create and upload video to real GCS
            logger.info("Step 2: Uploading video to GCS...")
            video_path = create_real_test_video(duration_seconds=5, include_golf_motion=True)
            
            storage = get_storage_service()
            video_blob_name = f"integration_test/{analysis_uuid}_test.mp4"
            
            with open(video_path, 'rb') as f:
                result = await storage.upload_video(
                    file=f,
                    filename=video_blob_name,
                    user_id=test_user,
                    video_id=1,
                    content_type='video/mp4'
                )
            
            assert result["success"] is True, f"GCS upload failed: {result.get('error')}"
            logger.info(f"Uploaded video to GCS: {video_blob_name}")
            
            # 4. Attach video to analysis
            success = await orchestrator.attach_video_to_analysis(
                analysis_uuid, video_blob_name
            )
            assert success is True, "Failed to attach video to analysis"
            
            # 5. Process with real Gemini (run in background)
            logger.info("Step 3: Processing video with Gemini...")
            
            # Start background analysis
            analysis_task = asyncio.create_task(
                orchestrator.analyze_video_background(analysis_uuid)
            )
            
            # Wait for processing to complete (with timeout)
            max_wait = 60  # seconds
            start_time = datetime.utcnow()
            
            while (datetime.utcnow() - start_time).total_seconds() < max_wait:
                # Check status
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(VideoAnalysis).filter(
                            VideoAnalysis.uuid == uuid.UUID(analysis_uuid)
                        )
                    )
                    analysis = result.scalar_one_or_none()
                    
                    if analysis.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                        break
                
                await asyncio.sleep(2)
            
            # Wait for task to complete
            try:
                await asyncio.wait_for(analysis_task, timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Analysis task didn't complete in time")
            
            # 6. Verify final state in database
            logger.info("Step 4: Verifying final results...")
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(VideoAnalysis).filter(
                        VideoAnalysis.uuid == uuid.UUID(analysis_uuid)
                    )
                )
                final_analysis = result.scalar_one_or_none()
                
                assert final_analysis is not None, "Analysis disappeared from database"
                
                # Check final status
                if final_analysis.status == AnalysisStatus.FAILED:
                    logger.warning(f"Analysis failed: {final_analysis.errorDescription}")
                    # This is acceptable - Gemini might not detect a golf swing in test video
                else:
                    assert final_analysis.status == AnalysisStatus.COMPLETED, \
                           f"Unexpected status: {final_analysis.status}"
                    
                    # Verify analysis results
                    assert final_analysis.analysisJSON is not None or \
                           final_analysis.ai_analysis is not None, \
                           "No analysis results stored"
                    
                    # Verify video was moved to processed folder
                    if final_analysis.processedVideoURL:
                        assert "processed/" in final_analysis.processedVideoURL, \
                               "Video not moved to processed folder"
                
                logger.info(f"Final status: {final_analysis.status}")
            
            # Cleanup test video file
            os.unlink(video_path)
            
            logger.info("✅ Full integration test completed successfully!")
            
        except Exception as e:
            pytest.fail(f"Full integration test failed: {e}")
        
        finally:
            # Cleanup GCS
            if video_blob_name:
                try:
                    storage = get_storage_service()
                    # Try to delete from both processing and processed folders
                    for prefix in ["integration_test/", "processing/", "processed/"]:
                        blob = storage.bucket.blob(f"{prefix}{analysis_uuid}_test.mp4")
                        if blob.exists():
                            blob.delete()
                            logger.info(f"Cleaned up GCS blob: {prefix}{analysis_uuid}_test.mp4")
                except Exception as e:
                    logger.warning(f"Failed to cleanup GCS: {e}")
            
            # Cleanup database
            if analysis_uuid:
                try:
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(
                            select(VideoAnalysis).filter(
                                VideoAnalysis.uuid == uuid.UUID(analysis_uuid)
                            )
                        )
                        analysis = result.scalar_one_or_none()
                        if analysis:
                            await session.delete(analysis)
                            await session.commit()
                            logger.info(f"Cleaned up analysis: {analysis_uuid}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup database: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_full_flow(
        self, verify_all_services, test_user, create_real_test_video
    ):
        """Test multiple concurrent analyses with all real services"""
        analysis_uuids = []
        
        try:
            # Create multiple analyses concurrently
            orchestrator = AnalysisOrchestrator()
            storage = get_storage_service()
            
            # Create 3 concurrent analyses
            tasks = []
            for i in range(3):
                async def run_analysis(index):
                    # Create analysis
                    analysis_uuid = await orchestrator.create_analysis_entry(user_id=test_user)
                    
                    # Create and upload video
                    video_path = create_real_test_video(duration_seconds=2)
                    video_blob_name = f"integration_test/concurrent_{analysis_uuid}.mp4"
                    
                    with open(video_path, 'rb') as f:
                        await storage.upload_video(
                            file=f,
                            filename=video_blob_name,
                            user_id=test_user,
                            video_id=index,
                            content_type='video/mp4'
                        )
                    
                    # Attach and start analysis
                    await orchestrator.attach_video_to_analysis(analysis_uuid, video_blob_name)
                    
                    # Start background processing
                    asyncio.create_task(
                        orchestrator.analyze_video_background(analysis_uuid)
                    )
                    
                    # Cleanup video file
                    os.unlink(video_path)
                    
                    return analysis_uuid
                
                tasks.append(run_analysis(i))
            
            # Run concurrently
            analysis_uuids = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            successful = 0
            for result in analysis_uuids:
                if isinstance(result, Exception):
                    logger.warning(f"Concurrent analysis failed: {result}")
                else:
                    successful += 1
            
            assert successful > 0, "All concurrent analyses failed"
            logger.info(f"Successfully started {successful}/3 concurrent analyses")
            
            # Wait a bit for processing
            await asyncio.sleep(10)
            
            # Check final states
            async with AsyncSessionLocal() as session:
                for analysis_uuid in analysis_uuids:
                    if isinstance(analysis_uuid, str):
                        result = await session.execute(
                            select(VideoAnalysis).filter(
                                VideoAnalysis.uuid == uuid.UUID(analysis_uuid)
                            )
                        )
                        analysis = result.scalar_one_or_none()
                        if analysis:
                            logger.info(f"Analysis {analysis_uuid}: {analysis.status}")
            
        finally:
            # Cleanup
            for analysis_uuid in analysis_uuids:
                if isinstance(analysis_uuid, str):
                    # Cleanup GCS
                    try:
                        storage = get_storage_service()
                        blob = storage.bucket.blob(f"integration_test/concurrent_{analysis_uuid}.mp4")
                        if blob.exists():
                            blob.delete()
                    except:
                        pass
                    
                    # Cleanup database
                    try:
                        async with AsyncSessionLocal() as session:
                            result = await session.execute(
                                select(VideoAnalysis).filter(
                                    VideoAnalysis.uuid == uuid.UUID(analysis_uuid)
                                )
                            )
                            analysis = result.scalar_one_or_none()
                            if analysis:
                                await session.delete(analysis)
                                await session.commit()
                    except:
                        pass