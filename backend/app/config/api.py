"""
API configuration for FutureGolf backend.
"""

# API versioning
API_VERSION_PREFIX = "/api/v1"

# API documentation settings
API_TITLE = "FutureGolf API"
API_DESCRIPTION = "A modern golf management system API with comprehensive authentication"
API_VERSION = "1.0.0"

# Rate limiting settings (for future implementation)
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000

# Request timeout settings
REQUEST_TIMEOUT_SECONDS = 30

# CORS settings (can be extended as needed)
CORS_MAX_AGE = 3600