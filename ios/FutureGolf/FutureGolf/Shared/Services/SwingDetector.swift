import Foundation
import UIKit

@MainActor
class SwingDetector {
    private let swingDetectionWS = SwingDetectionWebSocketService()
    var onSwingDetected: ((Float) -> Void)?

    init() {
        setupWebSocketCallbacks()
    }

    func connect() {
        swingDetectionWS.connect()
        swingDetectionWS.beginDetection()
    }

    func disconnect() {
        swingDetectionWS.endDetection()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [weak self] in
            self?.swingDetectionWS.disconnect()
        }
    }

    func analyzeStillForSwing(_ image: UIImage) async throws {
        if swingDetectionWS.isConnected {
            try await swingDetectionWS.sendFrame(image)
        } else {
            print("⚠️ WebSocket not connected for swing detection")
        }
    }

    private func setupWebSocketCallbacks() {
        swingDetectionWS.onSwingDetected = { [weak self] confidence in
            self?.onSwingDetected?(confidence)
        }
        
        swingDetectionWS.onError = { error in
            print("❌ WebSocket error: \(error)")
        }
    }
}
