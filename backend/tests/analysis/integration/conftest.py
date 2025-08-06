"""
Configuration for integration tests.
These tests require all real services to be available.
"""

import pytest
import logging
import os
from typing import Generator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def integration_test_setup():
    """Setup for all integration tests"""
    logger.info("=" * 60)
    logger.info("Starting Integration Tests")
    logger.info("These tests use REAL services:")
    logger.info("  - Google Cloud Storage (GCS)")
    logger.info("  - Gemini Vision API")
    logger.info("  - Neon PostgreSQL Database")
    logger.info("=" * 60)
    
    # Verify environment
    warnings = []
    
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        warnings.append("⚠️  No Gemini API key found - some tests will fail")
    
    if not os.getenv("DATABASE_URL"):
        warnings.append("⚠️  No DATABASE_URL found - database tests will fail")
    
    if not os.getenv("GCS_BUCKET_NAME"):
        warnings.append("⚠️  No GCS_BUCKET_NAME found - storage tests may fail")
    
    if not os.getenv("GOOGLE_CLOUD_API_KEY") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        warnings.append("⚠️  No Google Cloud authentication found - storage tests will fail")
    
    if warnings:
        logger.warning("Environment warnings:")
        for warning in warnings:
            logger.warning(warning)
    
    yield
    
    logger.info("=" * 60)
    logger.info("Integration Tests Completed")
    logger.info("=" * 60)


@pytest.fixture(scope="session")
def skip_if_no_gcs():
    """Skip test if GCS is not available"""
    try:
        from app.services.storage_service import get_storage_service
        storage = get_storage_service()
        if not storage.bucket.exists():
            pytest.skip("GCS bucket not accessible")
    except Exception as e:
        pytest.skip(f"GCS not available: {e}")


@pytest.fixture(scope="session")
def skip_if_no_gemini():
    """Skip test if Gemini API is not available"""
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("Gemini API key not configured")


@pytest.fixture(scope="session")
def skip_if_no_neon():
    """Skip test if Neon database is not available"""
    if not os.getenv("DATABASE_URL"):
        pytest.skip("Neon database not configured")


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "requires_gcs: Test requires Google Cloud Storage access"
    )
    config.addinivalue_line(
        "markers", "requires_gemini: Test requires Gemini API access"
    )
    config.addinivalue_line(
        "markers", "requires_neon: Test requires Neon database access"
    )