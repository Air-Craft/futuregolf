import Foundation
import UIKit

@MainActor
class StillImageCaptureService {
    private let stillCaptureInterval: TimeInterval
    private var captureTask: Task<Void, Never>?

    var onCapture: (() async -> Void)?
    
    init(stillCaptureInterval: TimeInterval) {
        self.stillCaptureInterval = stillCaptureInterval
    }
    
    func start() {
        // Cancel any existing task before starting a new one
        stop()
        
        captureTask = Task {
            while !Task.isCancelled {
                await onCapture?()
                do {
                    // Wait for the specified interval before the next capture
                    try await Task.sleep(nanoseconds: UInt64(stillCaptureInterval * 1_000_000_000))
                } catch {
                    // Task was cancelled, exit the loop
                    break
                }
            }
        }
    }
    
    func stop() {
        captureTask?.cancel()
        captureTask = nil
    }
}