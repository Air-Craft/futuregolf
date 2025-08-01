import Foundation

struct Config {
    // MARK: - API Configuration
    
    /// The base URL for the backend API server
    static let serverBaseURL: String = {
        // Check for environment variable first, then fallback to default
//        return ProcessInfo.processInfo.environment["API_BASE_URL"] ?? "http://brians-macbook-pro-2.local:8001"
        return "http://brians-macbook-pro-2.local:8001"
    }()
    
    /// API version endpoint
    static let apiVersion = "v1"
    
    /// Full API base URL with version
    static var apiBaseURL: String {
        return "\(serverBaseURL)/api/\(apiVersion)"
    }
    
    // MARK: - Recording Configuration
    
    /// Camera frame rate preferences
    struct Camera {
        static let preferredFrameRate: Double = 60.0
        static let fallbackFrameRate: Double = 30.0
    }
    
    /// Recording timeout in seconds (3 minutes)
    static let recordingTimeout: TimeInterval = 180.0
    
    /// Target number of swings to record
    static let targetSwingCount = 3
    
    /// Frame capture interval for swing detection (in seconds)
    static let stillCaptureInterval: TimeInterval = 0.2
    
    /// Post-detection cooldown period (in seconds)
    static let postDetectionCooldown: TimeInterval = 2.0
    
    /// Convert images to black and white for faster processing
    static let imageConvertBW = true
    
    /// Disable swing detection (bypass server queries)
    static let disableSwingDetection = false
    
    // MARK: - Image Processing Configuration
    
    /// Target box size for resizing images (maintains aspect ratio)
    static let imageMaxSize = CGSize(width: 128, height: 128)
    
    /// JPEG compression quality (0.0-1.0) - equivalent to WebP quality 40
    static let imageJPEGQuality: CGFloat = 0.4
    
    // MARK: - TTS Cache Configuration
    
    /// How often to refresh the TTS cache (24 hours by default)
    static let ttsCacheRefreshInterval: TimeInterval = 86400.0
    
    /// Force TTS cache refresh on app launch (for debugging/testing)
    static let ttsForceCacheRefreshOnLaunch: Bool = false
    
    /// Directory name for TTS cache
    static let ttsCacheDirectory = "TTSCache"
    
    // MARK: - Network Timeout Configuration
    
    /// Timeout for TTS synthesis requests (in seconds)
    static let ttsSynthesisTimeout: TimeInterval = 20.0
    
    /// Timeout for health check requests (in seconds)
    static let healthCheckTimeout: TimeInterval = 5.0
    
    /// Timeout for general API requests (in seconds)
    static let apiRequestTimeout: TimeInterval = 30.0
    
    /// Timeout for video upload requests (in seconds)
    static let videoUploadTimeout: TimeInterval = 120.0
    
    // MARK: - Debug Configuration
    
    /// Enable debug logging
    static let isDebugEnabled: Bool = {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }()
    
    // MARK: - Convenience Methods
    
    /// Check if we're running in simulator
    static var isSimulator: Bool {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }
}
