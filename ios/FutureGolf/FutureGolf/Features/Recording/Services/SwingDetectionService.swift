import Foundation
import UIKit
import Combine
import AudioToolbox

@MainActor
class SwingDetectionService: ObservableObject {
    @Published var swingCount = 0
    @Published var progressCircles: [ProgressCircle] = []
    
    private let targetSwingCount: Int
    private let swingDetector = SwingDetector()
    
    var onSwingDetected: ((Int) -> Void)?
    
    init(targetSwingCount: Int) {
        self.targetSwingCount = targetSwingCount
        setupProgressCircles()
        
        swingDetector.onSwingDetected = { [weak self] confidence in
            self?.processSwingDetection(isSwingDetected: true, confidence: confidence)
        }
    }
    
    func connect() {
        swingDetector.connect()
    }
    
    func disconnect() {
        swingDetector.disconnect()
    }
    
    func analyzeStillForSwing(_ image: UIImage) async throws {
        try await swingDetector.analyzeStillForSwing(image)
    }
    
    private func setupProgressCircles() {
        progressCircles = (0..<targetSwingCount).map { _ in ProgressCircle() }
    }
    
    private func processSwingDetection(isSwingDetected: Bool, confidence: Float = 0.0) {
        guard isSwingDetected else { return }
        
        swingCount += 1
        
        if swingCount <= progressCircles.count {
            progressCircles[swingCount - 1].isCompleted = true
        }
        
        playSwingTone()
        onSwingDetected?(swingCount)
    }
    
    private func playSwingTone() {
        AudioServicesPlaySystemSound(1057) // "Tink"
    }
    
    func reset() {
        swingCount = 0
        setupProgressCircles()
    }
}
