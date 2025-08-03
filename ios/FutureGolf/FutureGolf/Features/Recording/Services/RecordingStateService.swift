import Foundation
import Combine

@MainActor
class RecordingStateService: ObservableObject {
    @Published var currentPhase: RecordingPhase = .setup
    @Published var isRecording = false
    @Published var recordingTime: TimeInterval = 0
    @Published var errorType: RecordingError?
    
    private var recordingTimer: Timer?
    
    func startRecording() {
        currentPhase = .recording
        isRecording = true
        recordingTime = 0
        startTimer()
    }
    
    func stopRecording() {
        currentPhase = .processing
        isRecording = false
        stopTimer()
    }
    
    func showError(_ error: RecordingError) {
        errorType = error
        currentPhase = .error
    }
    
    private func startTimer() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.01, repeats: true) { [weak self] _ in
            self?.recordingTime += 0.01
        }
    }
    
    private func stopTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
    }
    
    func cleanup() {
        stopTimer()
    }
}
