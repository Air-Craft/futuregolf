"""
Test server fixture for self-contained backend tests
"""

import subprocess
import time
import socket
import os
import sys
import signal
import atexit
import threading
from contextlib import contextmanager
from typing import Optional

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)


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


class TestServer:
    """Manages a test server instance."""
    
    def __init__(self, port: Optional[int] = None, env: Optional[dict] = None):
        self.port = port or find_free_port()
        self.process = None
        self.env = env or {}
        self._stop_streaming = threading.Event()
        self._stream_thread = None
        
    def _stream_output(self):
        """Stream server output to console in real-time."""
        try:
            while not self._stop_streaming.is_set():
                if self.process and self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        # Print with [SERVER] prefix for clarity
                        print(f"[SERVER] {line.strip()}")
                    elif self.process.poll() is not None:
                        # Process has terminated
                        break
                else:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[SERVER] Error streaming output: {e}")
        
    def start(self) -> None:
        """Start the test server."""
        # Prepare environment
        env = os.environ.copy()
        env.update(self.env)
        env['PORT'] = str(self.port)
        env['HOST'] = '127.0.0.1'
        
        # Pass through API keys if they exist
        for key in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY']:
            if key in os.environ:
                env[key] = os.environ[key]
        
        # Start server process directly with Python
        cmd = [sys.executable, 'start_server.py']
        self.process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stdout and stderr
            preexec_fn=os.setsid if sys.platform != 'win32' else None,
            text=True
        )
        
        # Register cleanup
        atexit.register(self.stop)
        
        # Start log streaming thread
        self._stop_streaming.clear()
        self._stream_thread = threading.Thread(target=self._stream_output, daemon=True)
        self._stream_thread.start()
        
        # Wait for server to be ready
        if not wait_for_server('127.0.0.1', self.port, timeout=10.0):
            # Get server output for debugging
            output = []
            try:
                for line in iter(self.process.stdout.readline, ''):
                    if not line:
                        break
                    output.append(line.strip())
            except:
                pass
            
            self.stop()
            error_msg = f"Server failed to start on port {self.port}"
            if output:
                error_msg += f"\nServer output:\n" + "\n".join(output)
            raise RuntimeError(error_msg)
            
        print(f"✅ Test server started on port {self.port}")
        
    def stop(self) -> None:
        """Stop the test server."""
        # Signal the streaming thread to stop
        self._stop_streaming.set()
        
        if self.process:
            try:
                if sys.platform == 'win32':
                    self.process.terminate()
                else:
                    # Kill the process group to ensure all child processes are terminated
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                
                # Wait for process to terminate
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    if sys.platform == 'win32':
                        self.process.kill()
                    else:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    self.process.wait()
                    
            except Exception as e:
                print(f"Warning: Error stopping server: {e}")
            finally:
                self.process = None
                
                # Wait for streaming thread to finish
                if self._stream_thread and self._stream_thread.is_alive():
                    self._stream_thread.join(timeout=1.0)
                
                print(f"✅ Test server stopped on port {self.port}")
                
    def get_base_url(self) -> str:
        """Get the base URL for the test server."""
        return f"http://127.0.0.1:{self.port}"
        
    def get_ws_url(self, path: str) -> str:
        """Get WebSocket URL for the test server."""
        return f"ws://127.0.0.1:{self.port}{path}"


@contextmanager
def test_server(port: Optional[int] = None, env: Optional[dict] = None):
    """Context manager for running a test server."""
    server = TestServer(port=port, env=env)
    try:
        server.start()
        yield server
    finally:
        server.stop()


# Pytest fixture support
def pytest_server_fixture(port: Optional[int] = None):
    """Create a pytest fixture for the test server."""
    import pytest
    
    @pytest.fixture(scope="session")
    def server():
        with test_server(port=port) as srv:
            yield srv
    
    return server