"""
Swing Detection Configuration
Based on AI_SWING_DETECTION.md specification
"""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_MODEL = os.getenv("SWING_DETECTION_LLM_MODEL", "gemini/gemini-1.5-flash-002")

# Timing thresholds (in seconds)
LLM_SUBMISSION_THRESHOLD = float(os.getenv("LLM_SUBMISSION_THRESHOLD", "1.25"))
CONTEXT_EXPIRY_SECONDS = float(os.getenv("CONTEXT_EXPIRY_SECONDS", "5.0"))

# Buffer limits
MAX_IMAGE_BUFFER = int(os.getenv("MAX_IMAGE_BUFFER", "100"))

# Frame rate from iOS app (for testing)
IOS_FRAME_INTERVAL = float(os.getenv("IOS_FRAME_INTERVAL", "0.35"))

# Image processing settings
IMAGE_MAX_SIZE = (640, 480)
IMAGE_JPEG_QUALITY = 75