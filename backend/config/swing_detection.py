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
LLM_SUBMISSION_THRESHOLD = float(os.getenv("LLM_SUBMISSION_THRESHOLD", "1.0"))

# Frame rate from iOS app (for testing)
IOS_FRAME_INTERVAL = float(os.getenv("IOS_FRAME_INTERVAL", "0.2"))

# Image processing settings
IMAGE_MAX_SIZE = (128, 128)  # Target box size for resizing images (maintains aspect ratio)
IMAGE_WEBP_QUALITY = 40  # WebP compression quality (1-100)
IMAGE_CONVERT_BW = True

# Confidence threshold for swing detection
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

# Post-detection cooldown (seconds)
POST_DETECTION_COOLDOWN = float(os.getenv("POST_DETECTION_COOLDOWN", "2.0"))