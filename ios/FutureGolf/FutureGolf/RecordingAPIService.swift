import Foundation
import UIKit
import Combine

// MARK: - API Models

// Voice analysis has been moved to on-device processing

struct SwingDetectionRequest: Codable {
    let sessionId: String
    let imageData: String
    let sequenceNumber: Int
    let timestamp: String?
    
    enum CodingKeys: String, CodingKey {
        case timestamp
        case sessionId = "session_id"
        case imageData = "image_data"
        case sequenceNumber = "sequence_number"
    }
}

struct SwingDetectionResponse: Codable {
    let swingDetected: Bool
    let confidence: Float
    let swingPhase: String?
    let reason: String
    let sessionId: String
    let sequenceNumber: Int
    let timestamp: String
    
    enum CodingKeys: String, CodingKey {
        case reason, timestamp
        case swingDetected = "swing_detected"
        case confidence
        case swingPhase = "swing_phase"
        case sessionId = "session_id"
        case sequenceNumber = "sequence_number"
    }
}

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
        self.baseURL = Config.serverBaseURL
        
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
    
    // MARK: - Swing Detection API
    
    func analyzeSwingFromImage(_ image: UIImage, sequenceNumber: Int) async throws -> SwingDetectionResponse {
        let url = URL(string: "\(baseURL)/api/v1/recording/swing/detect")!
        
        // Convert image to base64
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            throw RecordingAPIError.imageProcessingFailed
        }
        
        let base64String = imageData.base64EncodedString()
        
        let request = SwingDetectionRequest(
            sessionId: getCurrentSessionId(),
            imageData: base64String,
            sequenceNumber: sequenceNumber,
            timestamp: ISO8601DateFormatter().string(from: Date())
        )
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)
        urlRequest.timeoutInterval = Config.apiRequestTimeout
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw RecordingAPIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw RecordingAPIError.serverError(httpResponse.statusCode)
        }
        
        let decoder = JSONDecoder()
        let swingResponse = try decoder.decode(SwingDetectionResponse.self, from: data)
        
        print("Swing analysis result: detected=\(swingResponse.swingDetected), confidence=\(swingResponse.confidence), phase=\(swingResponse.swingPhase ?? "none")")
        
        return swingResponse
    }
    
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