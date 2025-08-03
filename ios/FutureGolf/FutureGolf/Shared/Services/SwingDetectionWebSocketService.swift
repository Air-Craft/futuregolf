import Foundation
import Combine
import UIKit
import CoreImage

// MARK: - WebSocket Response Models

struct SwingDetectionWSResponse: Codable {
    let status: String
    let swingDetected: Bool?
    let confidence: Float?
    let timestamp: Double?
    let contextWindow: Float?
    let contextSize: Int?
    let cooldownRemaining: Float?
    let totalSwings: Int?
    let message: String?
    let error: String?
    
    enum CodingKeys: String, CodingKey {
        case status
        case swingDetected = "swing_detected"
        case confidence
        case timestamp
        case contextWindow = "context_window"
        case contextSize = "context_size"
        case cooldownRemaining = "cooldown_remaining"
        case totalSwings = "total_swings"
        case message
        case error
    }
}

struct SwingDetectionWSRequest: Codable {
    let timestamp: Double
    let imageBase64: String
    
    enum CodingKeys: String, CodingKey {
        case timestamp
        case imageBase64 = "image_base64"
    }
}

// MARK: - WebSocket Service

@MainActor
class SwingDetectionWebSocketService: NSObject, ObservableObject {
    
    // MARK: - Properties
    
    @Published var isConnected = false
    @Published var lastResponse: SwingDetectionWSResponse?
    
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession!
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private var detectionStartTime:TimeInterval = 0
    
    // Retry Logic
    private var retryTimer: Timer?
    private var retryAttempts = 0
    private let maxRetryAttempts = 5
    private var baseRetryInterval: TimeInterval = 1.0

    // Callbacks
    var onSwingDetected: ((Float) -> Void)?  // confidence
    var onError: ((String) -> Void)?
    
    override init() {
        super.init()
        urlSession = URLSession(configuration: .default, delegate: self, delegateQueue: .main)
    }
    
    // MARK: - Connection Management
    
    func connect() {
        guard webSocketTask == nil else { return }
        
        let wsURL = Config.apiBaseURL
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")
            + "/ws/detect-golf-swing"
        
        guard let url = URL(string: wsURL) else {
            print("❌ Invalid WebSocket URL: \(wsURL)")
            return
        }
        
        print("🔌 Connecting to WebSocket: \(url)")
        
        webSocketTask = urlSession.webSocketTask(with: url)
        webSocketTask?.resume()
        
        receiveMessage()
        
        print("🔌 WebSocket connection initiated...")
    }
    
    func disconnect() {
        retryTimer?.invalidate()
        retryTimer = nil
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
        print("🔌 WebSocket disconnected")
    }
    
    private func retryConnection() {
        guard retryAttempts < maxRetryAttempts else {
            print("❌ WebSocket connection failed after \(maxRetryAttempts) attempts.")
            onError?("Failed to connect to the server.")
            return
        }
        
        let delay = baseRetryInterval * pow(2.0, Double(retryAttempts))
        retryAttempts += 1
        
        print("🔌 Retrying WebSocket connection in \(delay) seconds...")
        
        retryTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            Task { @MainActor in
                self?.connect()
            }
        }
    }
    
    // MARK: - Sending Frames
    
    
    func beginDetection() {
        guard isConnected else {
            print("⚠️ Cannot begin detection - WebSocket not connected")
            return
        }
        detectionStartTime = Date().timeIntervalSince1970
        print("🎬 Swing detection started at timestamp: \(detectionStartTime)")
    }
    
    func endDetection() {
        detectionStartTime = 0
        print("🎬 Swing detection ended")
    }
    
    func sendFrame(_ image: UIImage) async throws {
        guard isConnected, let webSocketTask = webSocketTask else {
            throw RecordingAPIError.notConnected
        }
        
        // Grab timestamp before processing
        let timestamp = Date().timeIntervalSince1970 - detectionStartTime
        
        // Process image (resize, compress, optionally convert to B&W)
        guard let processedImageData = processImage(image) else {
            throw RecordingAPIError.imageProcessingFailed
        }
        
        let base64String = processedImageData.base64EncodedString()
        
        let request = SwingDetectionWSRequest(
            timestamp: timestamp,
            imageBase64: base64String
        )
        
        let data = try encoder.encode(request)
        let jsonString = String(data: data, encoding: .utf8)!
        let message = URLSessionWebSocketTask.Message.string(jsonString)
        
        try await webSocketTask.send(message)
    }
    
    // MARK: - Image Processing
    
    private func processImage(_ image: UIImage) -> Data? {
        // Box fit resize using config settings
        guard let resizedImage = image.resizedToFit(in: Config.imageMaxSize) else {
            return nil
        }
        
        // Convert to B&W if enabled
        let processedImage: UIImage
        if Config.imageConvertBW {
            processedImage = resizedImage.convertToGrayscale() ?? resizedImage
        } else {
            processedImage = resizedImage
        }
        
        // Compress using config quality
        return processedImage.jpegData(compressionQuality: Config.imageJPEGQuality)
    }
    
    // MARK: - Receiving Messages
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            Task { @MainActor in
                guard let self = self else { return }
                
                switch result {
                case .success(let message):
                    switch message {
                    case .data(let data):
                        self.handleMessage(data)
                    case .string(let string):
                        if let data = string.data(using: .utf8) {
                            self.handleMessage(data)
                        }
                    @unknown default:
                        break
                    }
                    
                    // Continue receiving messages
                    self.receiveMessage()
                    
                case .failure(let error):
                    print("❌ WebSocket receive error: \(error)")
                    self.handleConnectionFailure(error: error)
                }
            }
        }
    }
    
    private func handleMessage(_ data: Data) {
        do {
            let response = try decoder.decode(SwingDetectionWSResponse.self, from: data)
            lastResponse = response
            
            if response.status == "error" {
                print("❌ Error: \(response.error ?? "Unknown error")")
                onError?(response.error ?? "Unknown error")
                return
            }
            
            if let swingDetected = response.swingDetected,
               let confidence = response.confidence,
               swingDetected,
               confidence >= Config.swingDetectConfidenceThreshold {
                print("🏌️ Swing detected with confidence: \(confidence)")
                onSwingDetected?(confidence)
            }
            
            // Optional: Print every 5th cooldown message
            if response.status == "cooldown",
               let cooldownRemaining = response.cooldownRemaining {
                struct CooldownTracker {
                    static var counter = 0
                }
                CooldownTracker.counter += 1
                if CooldownTracker.counter % 11 == 0 {
                    print("⏱️ Cooldown: \(cooldownRemaining)s remaining")
                }
            }
            
            // Uncomment for debugging full response
            // print("🧾 Full WS Response: \(response)")
            
        } catch {
            print("❌ Failed to decode message: \(error)")
            print("📦 Raw message data: \(String(data: data, encoding: .utf8) ?? "Unable to decode")")
        }
    }
    
    private func handleConnectionFailure(error: Error) {
        isConnected = false
        webSocketTask = nil
        onError?(error.localizedDescription)
        retryConnection()
    }
}

// MARK: - URLSessionWebSocketDelegate

extension SwingDetectionWebSocketService: URLSessionWebSocketDelegate {
    
    nonisolated func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        Task { @MainActor in
            print("✅ WebSocket connection opened")
            self.isConnected = true
            self.retryAttempts = 0
            self.retryTimer?.invalidate()
            self.retryTimer = nil
        }
    }
    
    nonisolated func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        Task { @MainActor in
            print("🔌 WebSocket connection closed: \(closeCode.rawValue)")
            self.isConnected = false
            if closeCode != .goingAway {
                self.retryConnection()
            }
        }
    }
    
    nonisolated func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            Task { @MainActor in
                print("❌ WebSocket connection error: \(error)")
                self.handleConnectionFailure(error: error)
            }
        }
    }
}

// MARK: - Image Extensions

extension UIImage {
    func convertToGrayscale() -> UIImage? {
        guard let currentCGImage = self.cgImage else { return nil }
        
        let currentCIImage = CIImage(cgImage: currentCGImage)
        let filter = CIFilter(name: "CIColorMonochrome")
        filter?.setValue(currentCIImage, forKey: "inputImage")
        filter?.setValue(CIColor(red: 0.7, green: 0.7, blue: 0.7), forKey: "inputColor")
        filter?.setValue(1.0, forKey: "inputIntensity")
        
        guard let outputImage = filter?.outputImage else { return nil }
        
        let context = CIContext()
        guard let cgImage = context.createCGImage(outputImage, from: outputImage.extent) else { return nil }
        
        return UIImage(cgImage: cgImage)
    }
    
    func resizedToFit(in targetSize: CGSize) -> UIImage? {
        let widthRatio = targetSize.width / size.width
        let heightRatio = targetSize.height / size.height
        
        // Use the smaller ratio to ensure the image fits within the box
        let scale = min(widthRatio, heightRatio)
        
        // Only resize if the image is larger than the target
        if scale >= 1.0 {
            return self
        }
        
        let newSize = CGSize(width: size.width * scale, height: size.height * scale)
        
        UIGraphicsBeginImageContextWithOptions(newSize, false, 0.0)
        draw(in: CGRect(origin: .zero, size: newSize))
        let resizedImage = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        
        return resizedImage
    }
}
