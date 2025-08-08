"""
Utility functions for test server management.
"""

import subprocess
import time
import socket
import os
import sys
import signal
import logging
from typing import Optional, Tuple

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

logger = logging.getLogger(__name__)


def find_free_port(start_port: int = 8009) -> int:
    """Find a free port starting from the given port."""
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('', port))
                sock.close()
                return port
            except OSError:
                port += 1
    raise RuntimeError("No free ports available")


def wait_for_server(host: str, port: int, timeout: float = 30.0) -> bool:
    """Wait for server to be ready to accept connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.1)
    return False


def start_test_server(port: Optional[int] = None, log_file: Optional[str] = None) -> Tuple[subprocess.Popen, int]:
    """
    Start a test server and return the process and port.
    
    Args:
        port: Optional port to use, will find free port if not specified
        log_file: Optional log file path, defaults to backend/logs/test_server_logs.txt
        
    Returns:
        Tuple of (process, port)
    """
    if port is None:
        port = find_free_port()
    
    if log_file is None:
        log_dir = os.path.join(backend_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "test_server_logs.txt")
    
    # Prepare environment
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['HOST'] = '127.0.0.1'
    env['LOG_LEVEL'] = 'INFO'
    # Add backend directory to PYTHONPATH so 'app' module can be found
    env['PYTHONPATH'] = backend_dir + os.pathsep + env.get('PYTHONPATH', '')
    
    # Pass through API keys if they exist
    for key in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY', 'DATABASE_URL']:
        if key in os.environ:
            env[key] = os.environ[key]
    
    # Open log file
    log_handle = open(log_file, 'w')
    
    # Start server process
    cmd = [sys.executable, 'app/start_server.py']
    process = subprocess.Popen(
        cmd,
        cwd=backend_dir,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid if sys.platform != 'win32' else None
    )
    
    # Wait for server to be ready
    if not wait_for_server('127.0.0.1', port, timeout=15.0):
        process.terminate()
        process.wait(timeout=5)
        log_handle.close()
        
        # Read log file for debugging
        with open(log_file, 'r') as f:
            logs = f.read()
        
        raise RuntimeError(f"Server failed to start on port {port}. Logs:\n{logs}")
    
    logger.info(f"Test server started on port {port}, logging to {log_file}")
    return process, port


def stop_test_server(process: subprocess.Popen) -> None:
    """Stop a test server process."""
    if process:
        try:
            if sys.platform == 'win32':
                process.terminate()
            else:
                # Kill the process group to ensure all child processes are terminated
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Wait for process to terminate
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                if sys.platform == 'win32':
                    process.kill()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
                
        except Exception as e:
            logger.warning(f"Error stopping server: {e}")


def get_test_base_url(port: int) -> str:
    """Get base URL for test server."""
    return f"http://127.0.0.1:{port}"