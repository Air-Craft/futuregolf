"""
E2E test configuration and fixtures.
"""

import pytest
import os
import sys
import logging

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from tests.utils.server_util import start_test_server, stop_test_server, get_test_base_url

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_server():
    """Start test server for E2E tests"""
    logger.info("Starting test server for E2E tests")
    
    # Start server
    process, port = start_test_server()
    base_url = get_test_base_url(port)
    
    logger.info(f"Test server started at {base_url}")
    
    yield {
        "process": process,
        "port": port,
        "base_url": base_url
    }
    
    # Cleanup
    logger.info("Stopping test server")
    stop_test_server(process)


@pytest.fixture
def base_url(test_server):
    """Get base URL for test server"""
    return test_server["base_url"]


@pytest.fixture
def api_v1_url(base_url):
    """Get API v1 base URL"""
    return f"{base_url}/api/v1"