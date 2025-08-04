import Foundation
import SwiftUI
import AVFoundation
import Combine
import Speech
import CoreImage
import Factory

@MainActor
@Observable
class RecordingViewModel: NSObject, ObservableObject {
    
    // MARK: - Dependencies
    @ObservationIgnored @Injected(\.appState) private var appState
    @ObservationIgnored @Injected(\.videoProcessingService) private var videoProcessingService
    @ObservationIgnored @Injected(\.ttsService) var ttsService
    @ObservationIgnored @Injected(\.cameraService) private var cameraService
    @ObservationIgnored @Injected(\.recordingService) private var recordingService
    @ObservationIgnored @Injected(\.voiceCommandService) private var voiceCommandService
    @ObservationIgnored @Injected(\.recordingAPIService) private var recordingAPIService

    // MARK: - Services
    private let swingDetectionWebSocketService = SwingDetectionWebSocketService()
    private let audioFeedbackService = AudioFeedbackService()
    
    // MARK: - Published State
    var currentPhase: RecordingPhase = .setup
    var isRecording = false
    var recordingTime: TimeInterval = 0
    var errorType: RecordingError?
    var swingCount = 0
    
    private var recordingStartTime: Date?
    private var lastCaptureTimeInterval: TimeInterval = 0
    
    // MARK: - Other Properties
    var isLeftHandedMode = false
    var cameraPosition: AVCaptureDevice.Position = .front
    var showPositioningIndicator = true
    var showProgressCircles = false
    var currentFrameRate: Double = 0.0
    var recordedVideoURL: URL?
    var recordedAnalysisId: String?
    var recordingSessionId = UUID()
    
    var captureSession: AVCaptureSession? { cameraService.captureSession }
    
    private var displayLink: CADisplayLink?
    private var timeoutTimer: Timer?
    private var activeAnalysisTasks = Set<Task<Void, Never>>()
    
    // MARK: - Configuration
    var targetSwingCount: Int { Config.targetSwingCount }
    var recordingTimeout: TimeInterval { Config.recordingTimeout }
    
    override init() {
        super.init()
        Task { @MainActor in
            setupServices()
            recordingAPIService.startSession()
        }
    }
    
    private func setupServices() {
        cameraService.onFramerateUpdate = { [weak self] frameRate in
            self?.currentFrameRate = frameRate
        }
        
        swingDetectionWebSocketService.onSwingDetected = { [weak self] confidence in
            guard let self = self else { return }
            self.swingCount += 1
            self.handleSwingDetected(self.swingCount)
        }
        
        voiceCommandService.onCommand = { [weak self] command in
            self?.handleVoiceCommand(command)
        }
    }
    
    private func handleVoiceCommand(_ command: VoiceCommand) {
        switch command {
        case .startRecording:
            if currentPhase == .setup { startRecording() }
        case .stopRecording:
            if currentPhase == .recording { finishRecording() }
        }
    }
    
    func setupCamera() async throws {
        try await cameraService.setupCamera(for: cameraPosition)
        if let session = cameraService.captureSession {
            recordingService.setupVideoOutput(for: session)
        }
    }
    
    func switchCamera() {
        cameraService.switchCamera()
        self.cameraPosition = cameraService.cameraPosition
    }
    
    func setZoomLevel(_ zoom: CGFloat) {
        cameraService.setZoomLevel(zoom)
    }
    
    func startRecording() {
        guard currentPhase == .setup else { return }
        
        recordingSessionId = UUID()
        
        // Start recording state
        currentPhase = .recording
        isRecording = true
        recordingStartTime = Date()
        lastCaptureTimeInterval = Date.now.timeIntervalSince1970
        
        startDisplayLink()
        
        showPositioningIndicator = false
        showProgressCircles = !Config.disableSwingDetection
        reset()
        
        cameraService.onFrameCaptured = { [weak self] image in
            self?.handleCapturedFrame(image)
        }
        
        if !Config.disableSwingDetection {
            swingDetectionWebSocketService.connect()
            swingDetectionWebSocketService.beginDetection()
        }
        
        recordingService.startRecording { [weak self] url, error in
            if let url = url {
                self?.handleRecordingCompletion(url: url)
            } else if let error = error {
                print("🚨 RecordingViewModel: Received error from recording service: \(error.localizedDescription)")
                self?.handle(error: RecordingError.cameraHardwareError)
            }
        }
        
        startTimeoutTimer()
        
        Task { try? await voiceCommandService.startListening() }
        ttsService.speakText("Great. I'm now recording. Begin swinging when you're ready.")
    }
    
    func finishRecording() {
        guard currentPhase == .recording else { return }
        
        // Stop recording state
        currentPhase = .processing
        isRecording = false
        recordingStartTime = nil
        stopDisplayLink()
        
        showProgressCircles = false
        
        timeoutTimer?.invalidate()
        timeoutTimer = nil
        
        cameraService.onFrameCaptured = nil
        
        activeAnalysisTasks.forEach { $0.cancel() }
        activeAnalysisTasks.removeAll()
        
        recordingService.stopRecording()
        voiceCommandService.stopListening()
        
        if !Config.disableSwingDetection {
            swingDetectionWebSocketService.endDetection()
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [weak self] in
                self?.swingDetectionWebSocketService.disconnect()
            }
        }
        
        ttsService.speakText("That's great. I'll get to work analyzing your swings.")
    }
    
    private func handleRecordingCompletion(url: URL) {
        print("📝 RecordingViewModel: Handling recording completion for URL: \(url.path)")
        self.recordedVideoURL = url
        self.recordedAnalysisId = videoProcessingService.queueVideo(videoURL: url)
        print("📝 RecordingViewModel: Queued video with Analysis ID: \(self.recordedAnalysisId ?? "nil")")
        appState.setCurrentRecording(url: url, id: self.recordedAnalysisId!)
    }
    
    private func startTimeoutTimer() {
        timeoutTimer = Timer.scheduledTimer(withTimeInterval: recordingTimeout, repeats: false) { [weak self] _ in
            Task { @MainActor in
                self?.handleRecordingTimeout()
            }
        }
    }
    
    private func startDisplayLink() {
        displayLink = CADisplayLink(target: self, selector: #selector(updateRecordingTime))
        displayLink?.add(to: .main, forMode: .common)
    }

    private func stopDisplayLink() {
        displayLink?.invalidate()
        displayLink = nil
    }
    
    @objc private func updateRecordingTime() {
        guard let startTime = recordingStartTime else { return }
        recordingTime = Date().timeIntervalSince(startTime)
    }
    
    func startVoiceRecognition() async throws {
        try await voiceCommandService.startListening()
    }
    
    private func handleCapturedFrame(_ image: UIImage) {
        guard isRecording else { return }
        let now = Date.now.timeIntervalSince1970
        if now - lastCaptureTimeInterval < Config.stillCaptureInterval {
            return
        }
        lastCaptureTimeInterval = now
        
        let task = Task { [weak self] in
            guard let self = self else { return }
            do {
                if self.swingDetectionWebSocketService.isConnected {
                    try await self.swingDetectionWebSocketService.sendFrame(image)
                } else {
                    print("⚠️ WebSocket not connected for swing detection")
                }
            } catch {
                print("🚨 Error analyzing still image: \(error)")
            }
        }
        activeAnalysisTasks.insert(task)
        Task { [weak self] in
            await task.value
            self?.activeAnalysisTasks.remove(task)
        }
    }
    
    private func handleSwingDetected(_ swingCount: Int) {
        audioFeedbackService.playSwingTone()
        
        if swingCount == 1 {
            voiceCommandService.stopListening()
            ttsService.speakText("Great. Take another when you're ready.") { [weak self] _ in
                Task { try? await self?.voiceCommandService.startListening() }
            }
        } else if swingCount == 2 {
            ttsService.speakText("Ok one more to go.")
        } else if swingCount >= targetSwingCount {
            audioFeedbackService.playCompletionTone()
            finishRecording()
        }
    }
    
    private func handleRecordingTimeout() {
        ttsService.speakText("That's taken longer than I had planned. I'll analyze what we have.")
        finishRecording()
    }
    
    func cleanup() {
        recordingSessionId = UUID()
        stopDisplayLink()
        timeoutTimer?.invalidate()
        timeoutTimer = nil
        voiceCommandService.stopListening()
        cameraService.onFrameCaptured = nil
        cameraService.stopSession()
        recordingAPIService.endSession()
        swingDetectionWebSocketService.disconnect()
    }
    
    func handle(error: Error) {
        if let recordingError = error as? RecordingError {
            errorType = recordingError
            currentPhase = .error
        }
    }
    
    func resetState() {
        currentPhase = .setup
        errorType = nil
    }

    func reset() {
        swingCount = 0
    }
}
