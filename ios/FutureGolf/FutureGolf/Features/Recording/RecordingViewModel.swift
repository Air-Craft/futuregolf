import Foundation
import SwiftUI
import AVFoundation
import Combine
import Speech
import CoreImage

@MainActor
@Observable
class RecordingViewModel: ObservableObject {
    
    // MARK: - Dependencies
    weak var dependencies: AppDependencies?
    
    // MARK: - Services
    let stateService = RecordingStateService()
    let swingDetectionService: SwingDetectionService
    private let audioFeedbackService = AudioFeedbackService()
    let stillImageCaptureService: StillImageCaptureService
    
    var ttsService: TTSService = TTSService.shared
    private let recordingAPIService = RecordingAPIService.shared
    private let cameraService = CameraService()
    private let recordingService = RecordingService()
    private let voiceCommandService = VoiceCommandService()
    
    // MARK: - Published Properties from Services
    var currentPhase: RecordingPhase { stateService.currentPhase }
    var isRecording: Bool { stateService.isRecording }
    var recordingTime: TimeInterval { stateService.recordingTime }
    var swingCount: Int { swingDetectionService.swingCount }
    var progressCircles: [ProgressCircle] { swingDetectionService.progressCircles }
    var errorType: RecordingError? { stateService.errorType }
    
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
    
    private var timeoutTimer: Timer?
    private var activeAnalysisTasks = Set<Task<Void, Never>>()
    
    // MARK: - Configuration
    var targetSwingCount: Int { Config.targetSwingCount }
    var stillCaptureInterval: TimeInterval { Config.stillCaptureInterval }
    var recordingTimeout: TimeInterval { Config.recordingTimeout }
    
    init(dependencies: AppDependencies? = nil) {
        self.dependencies = dependencies
        self.swingDetectionService = SwingDetectionService(targetSwingCount: Config.targetSwingCount)
        self.stillImageCaptureService = StillImageCaptureService(stillCaptureInterval: Config.stillCaptureInterval)
        setupServices()
        recordingAPIService.startSession()
    }
    
    private func setupServices() {
        cameraService.onFrameCaptured = { [weak self] image in
            self?.handleCapturedFrame(image)
        }
        
        swingDetectionService.onSwingDetected = { [weak self] swingCount in
            self?.handleSwingDetected(swingCount)
        }
        
        voiceCommandService.onCommand = { [weak self] command in
            self?.handleVoiceCommand(command)
        }
        
        stillImageCaptureService.onCapture = { [weak self] in
            self?.captureStillForAnalysis()
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
        stateService.startRecording()
        showPositioningIndicator = false
        showProgressCircles = !Config.disableSwingDetection
        swingDetectionService.reset()
        
        if !Config.disableSwingDetection {
            swingDetectionService.connect()
        }
        
        recordingService.startRecording { [weak self] url, error in
            if let url = url {
                self?.handleRecordingCompletion(url: url)
            }
        }
        
        stillImageCaptureService.start()
        startTimeoutTimer()
        
        Task { try? await voiceCommandService.startListening() }
        ttsService.speakText("Great. I'm now recording. Begin swinging when you're ready.")
    }
    
    func finishRecording() {
        guard currentPhase == .recording else { return }
        
        stateService.stopRecording()
        showProgressCircles = false
        
        timeoutTimer?.invalidate()
        timeoutTimer = nil
        
        stillImageCaptureService.stop()
        
        activeAnalysisTasks.forEach { $0.cancel() }
        activeAnalysisTasks.removeAll()
        
        recordingService.stopRecording()
        voiceCommandService.stopListening()
        
        if !Config.disableSwingDetection {
            swingDetectionService.disconnect()
        }
        
        ttsService.speakText("That's great. I'll get to work analyzing your swings.")
    }
    
    private func handleRecordingCompletion(url: URL) {
        self.recordedVideoURL = url
        if let deps = dependencies {
            self.recordedAnalysisId = deps.videoProcessing.queueVideo(videoURL: url)
            deps.setCurrentRecording(url: url, id: self.recordedAnalysisId!)
        }
    }
    
    private func startTimeoutTimer() {
        timeoutTimer = Timer.scheduledTimer(withTimeInterval: recordingTimeout, repeats: false) { [weak self] _ in
            self?.handleRecordingTimeout()
        }
    }
    
    func startVoiceRecognition() async throws {
        try await voiceCommandService.startListening()
    }
    
    private func captureStillForAnalysis() {
        cameraService.captureStillImage()
    }
    
    private func handleCapturedFrame(_ image: UIImage) {
        let task = Task { [weak self] in
            guard let self = self else { return }
            do {
                try await self.swingDetectionService.analyzeStillForSwing(image)
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
        stateService.cleanup()
        timeoutTimer?.invalidate()
        timeoutTimer = nil
        stillImageCaptureService.stop()
        voiceCommandService.stopListening()
        cameraService.stopSession()
        recordingAPIService.endSession()
        swingDetectionService.disconnect()
    }
    
    func resetState() {
        stateService.reset()
    }
}
