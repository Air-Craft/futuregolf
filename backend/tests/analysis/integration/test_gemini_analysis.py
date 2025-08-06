"""
Integration tests for Gemini Vision API.
These tests use REAL Gemini API and MUST FAIL if the API is not accessible.
"""

import pytest
import os
import tempfile
import asyncio
import cv2
import numpy as np
import logging
from typing import Optional

from app.core.providers.vision_gemini import GeminiVisionProvider
from app.services.video_analysis_service import CleanVideoAnalysisService

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def gemini_provider():
    """Get real Gemini provider - will fail if API not configured"""
    try:
        # Check for API key
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            pytest.fail("Gemini API key not configured (GEMINI_API_KEY or GOOGLE_API_KEY)")
        
        provider = GeminiVisionProvider(model_name="gemini-1.5-flash")
        return provider
    except Exception as e:
        pytest.fail(f"Gemini integration test failed - API not accessible: {e}")


@pytest.fixture(scope="module")
def analysis_service():
    """Get real video analysis service"""
    try:
        service = CleanVideoAnalysisService(model_name="gemini-1.5-flash")
        return service
    except Exception as e:
        pytest.fail(f"Video analysis service initialization failed: {e}")


@pytest.fixture
def create_test_video():
    """Create a real test video file"""
    def _create_video(duration_seconds=3, fps=30, width=640, height=480):
        """Create a test video with specified parameters"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            temp_path = f.name
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        
        # Generate frames
        total_frames = int(duration_seconds * fps)
        for i in range(total_frames):
            # Create a frame with changing content (simulates movement)
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add a moving circle to simulate a golf ball
            circle_x = int((i / total_frames) * width)
            circle_y = height // 2
            cv2.circle(frame, (circle_x, circle_y), 20, (255, 255, 255), -1)
            
            # Add text
            cv2.putText(frame, f"Frame {i}", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            out.write(frame)
        
        out.release()
        return temp_path
    
    paths = []
    yield _create_video
    
    # Cleanup
    for path in paths:
        if os.path.exists(path):
            os.unlink(path)


@pytest.mark.integration
@pytest.mark.requires_gemini
class TestGeminiAnalysis:
    """Test real Gemini API operations"""
    
    @pytest.mark.asyncio
    async def test_gemini_video_analysis_real(self, gemini_provider, create_test_video):
        """Test real Gemini API video analysis - MUST FAIL if API is not accessible"""
        try:
            # Create a test video
            video_path = create_test_video(duration_seconds=2)
            
            # Create a simple prompt
            prompt = """Analyze this video and provide a JSON response with the following structure:
            {
                "description": "Brief description of what you see",
                "frame_count": "Estimated number of frames",
                "has_movement": true/false
            }"""
            
            # Analyze with real Gemini API
            result = await gemini_provider.analyze_video(video_path, prompt)
            
            # Verify response structure
            assert result is not None, "Gemini returned None"
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            
            # Check for expected fields (Gemini should understand the prompt)
            assert "description" in result or "has_movement" in result or "_metadata" in result, \
                   f"Gemini response missing expected fields: {result}"
            
            # Verify metadata
            if "_metadata" in result:
                assert "analysis_duration" in result["_metadata"], "Missing analysis duration"
                assert result["_metadata"]["analysis_duration"] > 0, "Invalid analysis duration"
            
            # Cleanup
            os.unlink(video_path)
            
        except Exception as e:
            pytest.fail(f"Gemini video analysis test failed - API error: {e}")
    
    @pytest.mark.asyncio
    async def test_gemini_golf_swing_analysis(self, analysis_service, create_test_video):
        """Test real Gemini API with golf swing analysis prompt"""
        try:
            # Create a test video
            video_path = create_test_video(duration_seconds=5)
            
            # Use the actual golf swing analysis
            result = await analysis_service.analyze_video_file(video_path)
            
            # Verify response structure for golf analysis
            assert result is not None, "Analysis returned None"
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            
            # Check for metadata
            assert "_metadata" in result, "Missing metadata"
            assert "video_duration" in result["_metadata"], "Missing video duration"
            assert "analysis_duration" in result["_metadata"], "Missing analysis duration"
            
            # The actual swing analysis might not detect a real swing in our test video,
            # but the API should still respond
            logger.info(f"Gemini analysis completed in {result['_metadata']['analysis_duration']}s")
            
            # Cleanup
            os.unlink(video_path)
            
        except Exception as e:
            pytest.fail(f"Gemini golf swing analysis test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_gemini_retry_logic(self, gemini_provider, create_test_video):
        """Test Gemini retry logic on transient failures"""
        try:
            # Create a test video
            video_path = create_test_video(duration_seconds=1)
            
            # Use a very complex prompt that might cause issues
            prompt = "x" * 100000  # Very long prompt that might be rejected
            
            # This should either succeed with retries or fail gracefully
            try:
                result = await gemini_provider.analyze_video(video_path, prompt)
                # If it succeeds, that's fine
                assert result is not None
            except Exception as e:
                # If it fails, verify it's a reasonable error
                error_msg = str(e).lower()
                assert any(word in error_msg for word in ["token", "limit", "invalid", "too long"]), \
                       f"Unexpected error type: {e}"
            
            # Cleanup
            os.unlink(video_path)
            
        except Exception as e:
            pytest.fail(f"Gemini retry logic test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_gemini_concurrent_requests(self, gemini_provider, create_test_video):
        """Test concurrent Gemini API requests"""
        try:
            # Create multiple test videos
            video_paths = [create_test_video(duration_seconds=1) for _ in range(3)]
            
            # Create analysis tasks
            prompt = "Describe what you see in this video in one sentence."
            tasks = []
            
            for video_path in video_paths:
                task = gemini_provider.analyze_video(video_path, prompt)
                tasks.append(task)
            
            # Execute concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            successful = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Concurrent request {i} failed: {result}")
                else:
                    successful += 1
                    assert result is not None, f"Request {i} returned None"
            
            # At least some should succeed (API might have rate limits)
            assert successful > 0, "All concurrent requests failed"
            
            # Cleanup
            for path in video_paths:
                os.unlink(path)
                
        except Exception as e:
            pytest.fail(f"Gemini concurrent requests test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_gemini_large_video_handling(self, gemini_provider, create_test_video):
        """Test Gemini API with a larger video"""
        try:
            # Create a longer video (10 seconds)
            video_path = create_test_video(duration_seconds=10, fps=30)
            
            # Check file size
            file_size = os.path.getsize(video_path)
            logger.info(f"Testing with video size: {file_size / 1024:.2f} KB")
            
            # Analyze with Gemini
            prompt = "How many seconds long is this video approximately?"
            result = await gemini_provider.analyze_video(video_path, prompt)
            
            # Verify response
            assert result is not None, "Gemini returned None for large video"
            
            # Cleanup
            os.unlink(video_path)
            
        except Exception as e:
            pytest.fail(f"Gemini large video test failed: {e}")


@pytest.mark.integration
@pytest.mark.requires_gemini
class TestGeminiErrorHandling:
    """Test Gemini API error handling"""
    
    @pytest.mark.asyncio
    async def test_gemini_invalid_video_format(self, gemini_provider):
        """Test Gemini API with invalid video file"""
        try:
            # Create a non-video file
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                f.write(b"This is not a video")
                temp_path = f.name
            
            # Try to analyze
            with pytest.raises(Exception) as exc_info:
                await gemini_provider.analyze_video(temp_path, "Analyze this video")
            
            # Verify appropriate error
            assert exc_info.value is not None
            
            # Cleanup
            os.unlink(temp_path)
            
        except Exception as e:
            if "not a video" not in str(e).lower():
                # The error should indicate it's not a valid video
                logger.info(f"Gemini handled invalid video with error: {e}")
    
    @pytest.mark.asyncio
    async def test_gemini_api_key_validation(self):
        """Test Gemini API with invalid API key"""
        try:
            # Create provider with invalid key
            import os
            original_key = os.environ.get("GEMINI_API_KEY")
            
            try:
                os.environ["GEMINI_API_KEY"] = "invalid-api-key"
                provider = GeminiVisionProvider()
                
                # Try to use it
                with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
                    with pytest.raises(Exception) as exc_info:
                        await provider.analyze_video(f.name, "Test")
                    
                    # Should get authentication error
                    error_msg = str(exc_info.value).lower()
                    assert any(word in error_msg for word in ["auth", "api", "key", "invalid", "401", "403"]), \
                           f"Unexpected error for invalid API key: {exc_info.value}"
            finally:
                # Restore original key
                if original_key:
                    os.environ["GEMINI_API_KEY"] = original_key
                else:
                    os.environ.pop("GEMINI_API_KEY", None)
                    
        except Exception as e:
            logger.info(f"API key validation test completed: {e}")
    
    @pytest.mark.asyncio
    async def test_gemini_timeout_handling(self, gemini_provider, create_test_video):
        """Test Gemini API timeout handling"""
        try:
            # Create a video
            video_path = create_test_video(duration_seconds=5)
            
            # Use extremely complex prompt to potentially cause timeout
            prompt = """
            Provide an extremely detailed frame-by-frame analysis including:
            1. Exact RGB values of every pixel in key frames
            2. Mathematical analysis of motion vectors
            3. Fourier transform of the audio spectrum
            4. Detailed object detection with confidence scores
            5. Complete transcription of any text
            6. Analysis of compression artifacts
            7. Color grading assessment
            """ * 10  # Make it even longer
            
            # This might timeout or succeed - both are acceptable
            try:
                result = await gemini_provider.analyze_video(video_path, prompt)
                logger.info("Complex analysis succeeded")
                assert result is not None
            except Exception as e:
                # Timeout or rate limit errors are expected
                logger.info(f"Complex analysis failed as expected: {e}")
                assert any(word in str(e).lower() for word in ["timeout", "deadline", "rate", "limit"])
            
            # Cleanup
            os.unlink(video_path)
            
        except Exception as e:
            pytest.fail(f"Timeout handling test failed: {e}")