import Foundation
import UIKit
import Combine

// MARK: - API Models

struct VoiceBeginRequest: Codable {
    let transcript: String
    let confidence: Float
    let sessionId: String
    let timestamp: String?
    
    enum CodingKeys: String, CodingKey {
        case transcript, confidence, timestamp
        case sessionId = "session_id"
    }
}

struct VoiceBeginResponse: Codable {
    let readyToBegin: Bool
    let confidence: Float
    let reason: String
    let sessionId: String
    let timestamp: String
    
    enum CodingKeys: String, CodingKey {
        case reason, timestamp
        case readyToBegin = "ready_to_begin"
        case confidence
        case sessionId = "session_id"
    }
}

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
    private var webSocketTask: URLSessionWebSocketTask?
    
    // Session management
    @Published var isConnected = false
    private var currentSessionId: String?
    
    private init() {
        // Get base URL from environment or use default
        self.baseURL = ProcessInfo.processInfo.environment["API_BASE_URL"] ?? "http://localhost:8000"
        
        // Configure URL session
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
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
        disconnectWebSocket()
    }
    
    // MARK: - Voice Begin Signal API
    
    func analyzeVoiceForBegin(transcript: String, confidence: Float) async throws -> VoiceBeginResponse {
        let url = URL(string: "\(baseURL)/api/v1/recording/voice/begin")!
        
        let request = VoiceBeginRequest(
            transcript: transcript,
            confidence: confidence,
            sessionId: getCurrentSessionId(),
            timestamp: ISO8601DateFormatter().string(from: Date())
        )
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw RecordingAPIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw RecordingAPIError.serverError(httpResponse.statusCode)
        }
        
        let decoder = JSONDecoder()
        let voiceResponse = try decoder.decode(VoiceBeginResponse.self, from: data)
        
        print("Voice analysis result: ready=\(voiceResponse.readyToBegin), confidence=\(voiceResponse.confidence), reason=\(voiceResponse.reason)")
        
        return voiceResponse
    }
    
    // MARK: - WebSocket Voice Streaming
    
    func connectWebSocket(sessionId: String) async throws {
        guard let url = URL(string: "\(baseURL.replacingOccurrences(of: "http", with: "ws"))/api/v1/recording/voice/stream/\(sessionId)") else {
            throw RecordingAPIError.invalidURL
        }
        
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        
        isConnected = true
        
        // Start listening for messages
        listenForWebSocketMessages()
    }
    
    func sendVoiceData(transcript: String, confidence: Float, isFinal: Bool) async throws {
        guard let webSocketTask = webSocketTask else {
            throw RecordingAPIError.notConnected
        }
        
        let message = [
            "transcript": transcript,
            "confidence": confidence,
            "is_final": isFinal,
            "timestamp": ISO8601DateFormatter().string(from: Date())
        ] as [String : Any]
        
        let jsonData = try JSONSerialization.data(withJSONObject: message)
        let webSocketMessage = URLSessionWebSocketTask.Message.data(jsonData)
        
        try await webSocketTask.send(webSocketMessage)
    }
    
    private func listenForWebSocketMessages() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                Task { @MainActor in
                    await self?.handleWebSocketMessage(message)
                    self?.listenForWebSocketMessages() // Continue listening
                }
            case .failure(let error):
                Task { @MainActor in
                    print("WebSocket error: \(error)")
                    self?.isConnected = false
                }
            }
        }
    }
    
    private func handleWebSocketMessage(_ message: URLSessionWebSocketTask.Message) async {
        switch message {
        case .data(let data):
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    print("WebSocket message received: \(json)")
                    // Handle voice analysis response from WebSocket
                    // This would be processed by the RecordingViewModel
                }
            } catch {
                print("Failed to parse WebSocket message: \(error)")
            }
        case .string(let text):
            print("WebSocket text message: \(text)")
        @unknown default:
            break
        }
    }
    
    func disconnectWebSocket() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
    }
    
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
        
        let (data, _) = try await session.data(for: urlRequest)
        print("Session reset response: \(String(data: data, encoding: .utf8) ?? "none")")
    }
    
    // MARK: - Health Check
    
    func checkServiceHealth() async -> Bool {
        do {
            let url = URL(string: "\(baseURL)/api/v1/recording/voice/health")!
            let (_, response) = try await session.data(from: url)
            
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