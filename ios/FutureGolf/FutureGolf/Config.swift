import Foundation

struct Config {
    // MARK: - API Configuration
    
    /// The base URL for the backend API server
    static let serverBaseURL: String = {
        // Check for environment variable first, then fallback to default
        return ProcessInfo.processInfo.environment["API_BASE_URL"] ?? "http://192.168.40.75:8000"
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
