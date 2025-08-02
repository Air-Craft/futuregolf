import Foundation
import SwiftUI
import AVFoundation
import AudioToolbox
import Combine
import Speech
import CoreImage

// MARK: - Recording Phases
enum RecordingPhase {
    case setup
    case recording
    case processing
    case error
}

// MARK: - Recording Errors
enum RecordingError: LocalizedError, Equatable {
    case cameraPermissionDenied
    case insufficientStorage
    case cameraHardwareError
    case audioPermissionDenied
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .cameraPermissionDenied:
            return "Camera access is required to record your swing. Please enable camera permissions in Settings."
        case .insufficientStorage:
            return "Not enough storage space available. Please free up space and try again."
        case .cameraHardwareError:
            return "Camera hardware error. Please restart the app and try again."
        case .audioPermissionDenied:
            return "Microphone access is required for voice commands. Please enable microphone permissions in Settings."
        case .networkError:
            return "Network connection required for voice processing. Please check your connection."
        }
    }
}

// MARK: - Progress Circle Model
struct ProgressCircle: Identifiable {
    let id = UUID()
    var isCompleted: Bool = false
}

@MainActor
@Observable
class RecordingViewModel: NSObject {
    
    // MARK: - Dependencies
    weak var dependencies: AppDependencies?
    
    // MARK: - Published Properties
    var currentPhase: RecordingPhase = .setup
    var isRecording = false
    var recordingTime: TimeInterval = 0
    var swingCount = 0
    var progressCircles: [ProgressCircle] = []
    var errorType: RecordingError?
    var isLeftHandedMode = false
    var cameraPosition: AVCaptureDevice.Position = .front
    var showPositioningIndicator = true
    var showProgressCircles = false
    var currentFrameRate: Double = 0.0  // Actual achieved frame rate for display
    var recordedVideoURL: URL?
    var recordedAnalysisId: String?
    var isProcessingEnabled = false  // Controls whether to process captured photos
    var captureStartTime: Date?
    var lastFrameCaptureTime: TimeInterval = 0  // Track last frame capture time
    var lastFrameSendTime: TimeInterval = 0  // Track last frame send time
    var activeAnalysisTasks = Set<Task<Void, Never>>()  // Track active analysis tasks
    var capturedFramesBuffer: [UIImage] = []  // Buffer for captured frames
    var shouldCaptureNextFrame = false  // Flag to capture next video frame
    var recordingSessionId = UUID()  // Unique ID for each recording session
    
    // MARK: - Camera Properties
    var deviceOrientation: UIDeviceOrientation = .portrait
    var stillCaptureInterval: TimeInterval = Config.stillCaptureInterval // Capture every 0.35s as requested
    var recordingTimeout: TimeInterval { Config.recordingTimeout }
    
    // MARK: - Configuration
    var targetSwingCount: Int { Config.targetSwingCount }
    
    // MARK: - Services
    var ttsService: TTSService = TTSService.shared
    private let recordingAPIService = RecordingAPIService.shared
    private let cameraService = CameraService()
    private let recordingService = RecordingService()
    private let swingDetector = SwingDetector()
    private let voiceCommandService = VoiceCommandService()
    
    // MARK: - Camera Session
    var captureSession: AVCaptureSession? {
        return cameraService.captureSession
    }
    
    // MARK: - Audio Feedback
    private var swingTonePlayer: AVAudioPlayer?
    private var completionTonePlayer: AVAudioPlayer?
    
    // MARK: - Timers
    private var stillCaptureTimer: Timer?
    private var timeoutTimer: Timer?
    
    // MARK: - Callbacks
    var onRecordingStarted: (() -> Void)?
    var onTimeUpdate: ((TimeInterval) -> Void)?
    var onTimeout: (() -> Void)?
    var onCancelRequested: (() -> Void)?
    var onStillCaptured: ((UIImage) -> Void)?
    
    init(dependencies: AppDependencies? = nil) {
        self.dependencies = dependencies
        super.init()
        
        print("🐛 RecordingViewModel: Initializing...")
        
        setupProgressCircles()
        print("🐛 RecordingViewModel: Progress circles setup completed")
        
        setupServices()
        print("🐛 RecordingViewModel: Services setup completed")
        
        let sessionId = recordingAPIService.startSession()
        print("🐛 RecordingViewModel: API session started with ID: \(sessionId)")
        
        setupAudioTones()
    }
    
    // MARK: - Setup Methods
    
    private func setupAudioTones() {
        // Using system sounds for better performance and lower latency
    }
    
    private func setupProgressCircles() {
        progressCircles = (0..<targetSwingCount).map { _ in ProgressCircle() }
    }
    
    private func setupServices() {
        cameraService.onFrameCaptured = { [weak self] image in
            self?.handleCapturedFrame(image)
        }
        
        swingDetector.onSwingDetected = { [weak self] confidence in
            self?.processSwingDetection(isSwingDetected: true, confidence: confidence)
        }
        
        voiceCommandService.onCommand = { [weak self] command in
            self?.handleVoiceCommand(command)
        }
    }
    
    private func handleVoiceCommand(_ command: VoiceCommand) {
        switch command {
        case .startRecording:
            guard currentPhase == .setup, !isRecording else { return }
            print("🎤 Voice command received: Start Recording")
            startRecording()
        case .stopRecording:
            guard currentPhase == .recording else { return }
            print("🎤 Voice command received: Stop Recording")
            finishRecording()
        }
    }
    
    func setupCamera() async throws {
        try await cameraService.setupCamera(for: cameraPosition)
        if let session = cameraService.captureSession {
            recordingService.setupVideoOutput(for: session)
        }
    }
    
    // MARK: - Orientation Handling
    
    func updateOrientation(_ orientation: UIDeviceOrientation) {
        // This will be handled by the view and passed to the CameraService
    }
    
    // MARK: - Camera Control Methods
    
    func switchCamera() {
        cameraService.switchCamera()
        self.cameraPosition = cameraService.cameraPosition
    }
    
    func toggleLeftHandedMode() {
        isLeftHandedMode.toggle()
    }
    
    func setZoomLevel(_ zoom: CGFloat) {
        cameraService.setZoomLevel(zoom)
    }
    
    // MARK: - Recording Control Methods
    
    func startRecording() {
        guard currentPhase == .setup else { return }
        
        recordingSessionId = UUID()
        print("🎬 Starting new recording session: \(recordingSessionId)")
        
        currentPhase = .recording
        isRecording = true
        isProcessingEnabled = true
        showPositioningIndicator = false
        showProgressCircles = !Config.disableSwingDetection
        recordingTime = 0
        swingCount = 0
        capturedFramesBuffer.removeAll()
        
        for i in 0..<progressCircles.count {
            progressCircles[i].isCompleted = false
        }
        
        if !Config.disableSwingDetection {
            swingDetector.connect()
        }
        
        recordingService.startRecording { [weak self] url, error in
            if let error = error {
                print("Video recording finished with error: \(error)")
            } else if let url = url {
                print("Video recording finished successfully: \(url)")
                self?.handleRecordingCompletion(url: url)
            }
        }
        
        startStillCaptureTimer()
        startTimeoutTimer()
        
        Task { try? await voiceCommandService.startListening() }
        
        ttsService.speakText("Great. I'm now recording. Begin swinging when you're ready.")
        
        onRecordingStarted?()
    }
    
    func finishRecording() {
        guard currentPhase == .recording else { return }
        
        print("🏁 Finishing recording")
        
        stopAllTimers()
        shouldCaptureNextFrame = false
        isRecording = false
        isProcessingEnabled = false
        showProgressCircles = false
        
        activeAnalysisTasks.forEach { $0.cancel() }
        activeAnalysisTasks.removeAll()
        
        recordingService.stopRecording()
        voiceCommandService.stopListening()
        
        if !Config.disableSwingDetection {
            swingDetector.disconnect()
        }
        
        ttsService.speakText("That's great. I'll get to work analyzing your swings.")
    }
    
    private func handleRecordingCompletion(url: URL) {
        self.recordedVideoURL = url
        
        if let deps = self.dependencies {
            self.recordedAnalysisId = deps.videoProcessing.queueVideo(videoURL: url)
            deps.setCurrentRecording(url: url, id: self.recordedAnalysisId!)
            
            if self.currentPhase != .processing {
                self.currentPhase = .processing
            }
        } else {
            print("⚠️ No dependencies available, cannot queue video")
        }
    }
    
    // MARK: - Timer Methods
    
    private func startStillCaptureTimer() {
        let currentSessionId = recordingSessionId
        stillCaptureTimer = Timer.scheduledTimer(withTimeInterval: stillCaptureInterval, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self = self, self.recordingSessionId == currentSessionId, self.currentPhase == .recording, self.isProcessingEnabled else { return }
                self.captureStillForAnalysis()
            }
        }
    }
    
    private func startTimeoutTimer() {
        timeoutTimer = Timer.scheduledTimer(withTimeInterval: recordingTimeout, repeats: false) { [weak self] _ in
            Task { @MainActor in
                self?.handleRecordingTimeout()
            }
        }
    }
    
    private func stopAllTimers() {
        stillCaptureTimer?.invalidate()
        stillCaptureTimer = nil
        timeoutTimer?.invalidate()
        timeoutTimer = nil
    }
    
    // MARK: - Voice Recognition Methods
    
    func startVoiceRecognition() async throws {
        try await voiceCommandService.startListening()
    }
    
    func stopVoiceRecognition() {
        voiceCommandService.stopListening()
    }
    
    // MARK: - Still Capture Methods
    
    func captureStillForAnalysis() {
        guard currentPhase == .recording, isProcessingEnabled else { return }
        shouldCaptureNextFrame = true
    }
    
    private func handleCapturedFrame(_ image: UIImage) {
        guard shouldCaptureNextFrame, isProcessingEnabled, currentPhase == .recording else { return }
        
        shouldCaptureNextFrame = false
        lastFrameCaptureTime = Date().timeIntervalSince1970
        
        print("🎥 Capturing frame for swing analysis at time: \(lastFrameCaptureTime)")
        
        onStillCaptured?(image)
        processStillImage(image)
    }
    
    // MARK: - Audio Feedback Methods
    
    private func playSwingTone() {
        AudioServicesPlaySystemSound(1057) // "Tink"
    }
    
    private func playCompletionTone() {
        AudioServicesPlaySystemSound(1025) // "Complete"
    }
    
    // MARK: - Swing Detection Methods
    
    func processSwingDetection(isSwingDetected: Bool, confidence: Float = 0.0) {
        guard currentPhase == .recording, isSwingDetected else { return }
        
        swingCount += 1
        print("🏌️ Swing \(swingCount) detected with confidence: \(confidence)!")
        
        if swingCount <= progressCircles.count {
            progressCircles[swingCount - 1].isCompleted = true
        }
        
        playSwingTone()
        
        if swingCount == 1 {
            voiceCommandService.stopListening()
            ttsService.speakText("Great. Take another when you're ready.") { [weak self] _ in
                Task { try? await self?.voiceCommandService.startListening() }
            }
        } else if swingCount == 2 {
            ttsService.speakText("Ok one more to go.")
        } else if swingCount >= targetSwingCount {
            playCompletionTone()
            finishRecording()
        }
    }
    
    func processStillImage(_ image: UIImage) {
        guard isProcessingEnabled else { return }
        
        print("🖼️ Sending frame for analysis...")
        
        let task = Task { [weak self] in
            guard let self = self, self.isProcessingEnabled else { return }
            
            do {
                try await self.swingDetector.analyzeStillForSwing(image)
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
    
    // MARK: - Error Handling
    
    func handleCameraPermissionDenied() {
        errorType = .cameraPermissionDenied
        currentPhase = .error
    }
    
    func handleInsufficientStorage() {
        errorType = .insufficientStorage
        currentPhase = .error
    }
    
    func handleCameraHardwareError() {
        errorType = .cameraHardwareError
        currentPhase = .error
    }
    
    func handleRecordingTimeout() {
        ttsService.speakText("That's taken longer than I had planned. I'll analyze what we have.")
        onTimeout?()
        finishRecording()
    }
    
    // MARK: - Cancel Handling
    
    func handleCancelPressed() {
        ttsService.stopSpeaking()
        onCancelRequested?()
    }
    
    // MARK: - Cleanup
    
    func cleanup() {
        recordingSessionId = UUID()
        stopAllTimers()
        voiceCommandService.stopListening()
        cameraService.stopSession()
        recordingAPIService.endSession()
        swingDetector.disconnect()
    }
}
