import Foundation
import UIKit

@MainActor
class StillImageCaptureService {
    private var stillCaptureTimer: Timer?
    private let stillCaptureInterval: TimeInterval
    
    var onCapture: (() -> Void)?
    
    init(stillCaptureInterval: TimeInterval) {
        self.stillCaptureInterval = stillCaptureInterval
    }
    
    func start() {
        stillCaptureTimer = Timer.scheduledTimer(withTimeInterval: stillCaptureInterval, repeats: true) { [weak self] _ in
            self?.onCapture?()
        }
    }
    
    func stop() {
        stillCaptureTimer?.invalidate()
        stillCaptureTimer = nil
    }
}
