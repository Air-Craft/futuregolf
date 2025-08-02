import Foundation
import UIKit
import Combine

// MARK: - API Models

// Voice analysis has been moved to on-device processing

// Swing detection has been moved to WebSocket implementation (SwingDetectionWebSocketService)

// MARK: - Recording API Service

@MainActor
class RecordingAPIService: ObservableObject {
    
    static let shared = RecordingAPIService()
    
    private let baseURL: String
    private let session: URLSession
    // WebSocket removed - voice processing now handled on-device
    
    // Session management
    @Published var isConnected = false
    private var currentSessionId: String?
    
    private init() {
        // Get base URL from centralized config
        self.baseURL = Config.apiBaseURL
        
        // Configure URL session
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = Config.apiRequestTimeout
        config.timeoutIntervalForResource = Config.videoUploadTimeout
        self.session = URLSession(configuration: config)
    }
    
    // MARK: - Session Management
    
    func startSession() -> String {
        let sessionId = UUID().uuidString
        currentSessionId = sessionId
        return sessionId
    }
    
    func getCurrentSessionId() -> String {
        if let sessionId = currentSessionId {
            return sessionId
        }
        return startSession()
    }
    
    func endSession() {
        currentSessionId = nil
        // WebSocket cleanup no longer needed
    }
    
    // MARK: - Voice Analysis Removed
    // Voice commands are now processed on-device using iOS Speech Recognition
    
    // MARK: - WebSocket Voice Streaming Removed
    // Voice streaming has been replaced with on-device speech recognition
    
    // MARK: - Swing Detection Removed
    // Swing detection has been replaced with WebSocket implementation (SwingDetectionWebSocketService)
    
    // MARK: - Session Status API
    
    func getSessionStatus() async throws -> [String: Any] {
        let sessionId = getCurrentSessionId()
        let url = URL(string: "\(baseURL)/api/v1/recording/swing/sessions/\(sessionId)/status")!
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "GET"
        urlRequest.timeoutInterval = Config.apiRequestTimeout
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw RecordingAPIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw RecordingAPIError.serverError(httpResponse.statusCode)
        }
        
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        return json ?? [:]
    }
    
    func resetSession() async throws {
        let sessionId = getCurrentSessionId()
        let url = URL(string: "\(baseURL)/api/v1/recording/swing/sessions/\(sessionId)/reset")!
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.timeoutInterval = Config.apiRequestTimeout
        
        let (data, _) = try await session.data(for: urlRequest)
        print("Session reset response: \(String(data: data, encoding: .utf8) ?? "none")")
    }
    
    // MARK: - Health Check
    
    func checkServiceHealth() async -> Bool {
        do {
            // Use general health endpoint since voice-specific health check is no longer needed
            let url = URL(string: "\(baseURL.replacingOccurrences(of: "/api/v1", with: ""))/health")!
            var healthRequest = URLRequest(url: url)
            healthRequest.timeoutInterval = Config.healthCheckTimeout
            let (_, response) = try await session.data(for: healthRequest)
            
            if let httpResponse = response as? HTTPURLResponse {
                return httpResponse.statusCode == 200
            }
            return false
        } catch {
            print("Health check failed: \(error)")
            return false
        }
    }
}

// MARK: - Error Handling

enum RecordingAPIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case notConnected
    case imageProcessingFailed
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .invalidResponse:
            return "Invalid server response"
        case .serverError(let code):
            return "Server error: \(code)"
        case .notConnected:
            return "Not connected to server"
        case .imageProcessingFailed:
            return "Failed to process image"
        case .networkError:
            return "Network error"
        }
    }
}