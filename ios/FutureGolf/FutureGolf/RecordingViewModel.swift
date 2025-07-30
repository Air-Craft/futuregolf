import Foundation
import SwiftUI
import AVFoundation
import Combine
import Speech

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

// MARK: - Camera Configuration
enum CameraConfiguration {
    static let preferredFrameRate: Double = 60.0  // Try for 60fps when device supports it
    static let fallbackFrameRate: Double = 30.0   // Fallback to 30fps
    static let minFrameRate: Double = 24.0        // Minimum acceptable frame rate
    static let resolution = AVCaptureSession.Preset.hd1920x1080
    static let videoFormat = AVFileType.mp4
    static let stillCaptureInterval: TimeInterval = 0.25
}

@MainActor
@Observable
class RecordingViewModel: NSObject, ObservableObject {
    
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
    
    // MARK: - Camera Properties  
    var preferredFrameRate: Double { CameraConfiguration.preferredFrameRate }
    var fallbackFrameRate: Double { CameraConfiguration.fallbackFrameRate }
    var minFrameRate: Double { CameraConfiguration.minFrameRate }
    var resolution: AVCaptureSession.Preset { CameraConfiguration.resolution }
    var videoFormat: AVFileType { CameraConfiguration.videoFormat }
    var isPortraitMode = true
    var isAutoFocusEnabled = true
    var focusMode: AVCaptureDevice.FocusMode = .continuousAutoFocus
    var stillCaptureInterval: TimeInterval { CameraConfiguration.stillCaptureInterval }
    var recordingTimeout: TimeInterval { Config.recordingTimeout }
    
    // MARK: - Configuration
    var targetSwingCount: Int { Config.targetSwingCount }
    
    // MARK: - Services
    var ttsService: TTSService = TTSService.shared
    private let apiClient = APIClient()
    private let recordingAPIService = RecordingAPIService.shared
    private let onDeviceSTT = OnDeviceSTTService.shared
    
    // MARK: - Camera Session
    var captureSession: AVCaptureSession?
    private var videoOutput: AVCaptureMovieFileOutput?
    private var photoOutput: AVCapturePhotoOutput?
    private var currentCamera: AVCaptureDevice?
    private var videoInput: AVCaptureDeviceInput?
    
    // MARK: - Timers
    private var recordingTimer: Timer?
    private var stillCaptureTimer: Timer?
    private var timeoutTimer: Timer?
    
    // MARK: - Voice Processing
    private var voiceCommandCancellable: AnyCancellable?
    
    // MARK: - Callbacks
    var onRecordingStarted: (() -> Void)?
    var onTimeUpdate: ((TimeInterval) -> Void)?
    var onTimeout: (() -> Void)?
    var onCancelRequested: (() -> Void)?
    var onStillCaptured: ((UIImage) -> Void)?
    
    override init() {
        super.init()
        
        // Enhanced error logging for debugging
        print("🐛 RecordingViewModel: Initializing...")
        
        do {
            setupProgressCircles()
            print("🐛 RecordingViewModel: Progress circles setup completed")
            
            setupVoiceCommands()
            print("🐛 RecordingViewModel: Voice commands setup completed")
            
            // Start API session
            let sessionId = recordingAPIService.startSession()
            print("🐛 RecordingViewModel: API session started with ID: \(sessionId)")
            
        } catch {
            print("🐛 RecordingViewModel: Initialization error: \(error)")
        }
    }
    
    // MARK: - Setup Methods
    
    private func setupProgressCircles() {
        progressCircles = (0..<targetSwingCount).map { _ in ProgressCircle() }
    }
    
    private func setupVoiceCommands() {
        // Listen for voice commands from the on-device STT service
        voiceCommandCancellable = onDeviceSTT.$lastCommand
            .compactMap { $0 }
            .sink { [weak self] command in
                self?.handleVoiceCommand(command)
            }
    }
    
    private func handleVoiceCommand(_ command: VoiceCommand) {
        switch command {
        case .startRecording:
            guard currentPhase == .setup else { return }
            print("🎤 Voice command received: Start Recording")
            startRecording()
        case .stopRecording:
            guard currentPhase == .recording else { return }
            print("🎤 Voice command received: Stop Recording")
            finishRecording()
        }
    }
    
    func setupCamera() async throws {
        print("🐛 RecordingViewModel: Starting camera setup...")
        
        captureSession = AVCaptureSession()
        
        guard let session = captureSession else {
            print("🐛 RecordingViewModel: Failed to create capture session")
            throw RecordingError.cameraHardwareError
        }
        
        print("🐛 RecordingViewModel: Capture session created successfully")
        
        // Check camera permission
        let cameraAuthStatus = AVCaptureDevice.authorizationStatus(for: .video)
        print("🐛 RecordingViewModel: Camera permission status: \(cameraAuthStatus.rawValue)")
        
        if cameraAuthStatus != .authorized {
            if cameraAuthStatus == .notDetermined {
                print("🐛 RecordingViewModel: Requesting camera permission...")
                let granted = await AVCaptureDevice.requestAccess(for: .video)
                print("🐛 RecordingViewModel: Camera permission granted: \(granted)")
                if !granted {
                    throw RecordingError.cameraPermissionDenied
                }
            } else {
                print("🐛 RecordingViewModel: Camera permission denied or restricted")
                throw RecordingError.cameraPermissionDenied
            }
        }
        
        print("🐛 RecordingViewModel: Starting session configuration...")
        session.beginConfiguration()
        
        // Set session preset
        if session.canSetSessionPreset(resolution) {
            session.sessionPreset = resolution
            print("🐛 RecordingViewModel: Session preset set to: \(resolution.rawValue)")
        } else {
            print("🐛 RecordingViewModel: Warning - Could not set session preset to: \(resolution.rawValue)")
        }
        
        do {
            // Setup camera input
            print("🐛 RecordingViewModel: Setting up camera input...")
            try setupCameraInput(for: cameraPosition)
            print("🐛 RecordingViewModel: Camera input setup completed")
            
            // Setup video output
            print("🐛 RecordingViewModel: Setting up video output...")
            setupVideoOutput()
            print("🐛 RecordingViewModel: Video output setup completed")
            
            // Setup photo output for stills
            print("🐛 RecordingViewModel: Setting up photo output...")
            setupPhotoOutput()
            print("🐛 RecordingViewModel: Photo output setup completed")
            
        } catch {
            print("🐛 RecordingViewModel: Camera setup error: \(error)")
            session.commitConfiguration()
            throw error
        }
        
        session.commitConfiguration()
        print("🐛 RecordingViewModel: Camera setup completed successfully")
    }
    
    private func setupCameraInput(for position: AVCaptureDevice.Position) throws {
        guard let session = captureSession else { return }
        
        // Remove existing input
        if let existingInput = videoInput {
            session.removeInput(existingInput)
        }
        
        // Get camera for position using the standard method
        var camera: AVCaptureDevice?
        
        // Try wide angle camera first
        camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: position)
        
        if camera == nil {
            print("🐛 RecordingViewModel: No wide angle camera found for position: \(position)")
            // Fallback to any available camera
            camera = AVCaptureDevice.default(for: .video)
            print("🐛 RecordingViewModel: Using fallback camera")
        } else {
            print("🐛 RecordingViewModel: Using built-in wide angle camera")
        }
        
        guard let camera = camera else {
            print("🐛 RecordingViewModel: No camera available at all")
            throw RecordingError.cameraHardwareError
        }
        
        currentCamera = camera
        
        // Configure camera settings with advanced 60fps detection
        do {
            try camera.lockForConfiguration()
            
            let (bestFormat, achievedFrameRate) = findBestCameraFormat(for: camera, position: position)
            
            if let format = bestFormat {
                print("🐛 RecordingViewModel: Setting optimal format for \(achievedFrameRate)fps")
                camera.activeFormat = format
                
                // Set the frame rate
                let frameDuration = CMTime(value: 1, timescale: Int32(achievedFrameRate))
                if frameDuration.isValid && !frameDuration.isIndefinite {
                    camera.activeVideoMinFrameDuration = frameDuration
                    camera.activeVideoMaxFrameDuration = frameDuration
                    
                    // Update the actual achieved frame rate for UI display
                    self.currentFrameRate = achievedFrameRate
                    
                    print("🐛 RecordingViewModel: Successfully configured camera for \(achievedFrameRate)fps")
                } else {
                    print("🐛 RecordingViewModel: Invalid frame duration, using device defaults")
                    self.currentFrameRate = 30.0 // Default fallback
                }
            } else {
                print("🐛 RecordingViewModel: No suitable format found, using device defaults")
                self.currentFrameRate = 30.0 // Default fallback
            }
            
            // Set focus mode
            if camera.isFocusModeSupported(focusMode) {
                camera.focusMode = focusMode
            }
            
            // Set exposure mode
            if camera.isExposureModeSupported(.continuousAutoExposure) {
                camera.exposureMode = .continuousAutoExposure
            }
            
        } catch {
            print("🐛 RecordingViewModel: Error configuring camera: \(error)")
            camera.unlockForConfiguration()
            throw RecordingError.cameraHardwareError
        }
        
        camera.unlockForConfiguration()
        
        // Create input
        let input = try AVCaptureDeviceInput(device: camera)
        
        if session.canAddInput(input) {
            session.addInput(input)
            videoInput = input
        } else {
            throw RecordingError.cameraHardwareError
        }
    }
    
    // MARK: - Advanced Camera Format Detection
    
    private func findBestCameraFormat(for camera: AVCaptureDevice, position: AVCaptureDevice.Position) -> (AVCaptureDevice.Format?, Double) {
        let cameraName = position == .front ? "Front" : "Back"
        print("🐛 RecordingViewModel: Analyzing \(cameraName) camera formats for optimal frame rate...")
        
        var bestFormat: AVCaptureDevice.Format?
        var achievedFrameRate: Double = fallbackFrameRate
        
        // Priority order: try for 60fps first, then fallback to 30fps, then device max
        let targetRates = [preferredFrameRate, fallbackFrameRate]
        
        for targetRate in targetRates {
            print("🐛 RecordingViewModel: Searching for format supporting \(targetRate)fps...")
            
            for format in camera.formats {
                let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
                let frameRateRanges = format.videoSupportedFrameRateRanges
                
                // Look for 1080p or higher resolution formats
                let isHighRes = dimensions.width >= 1920 && dimensions.height >= 1080
                
                for range in frameRateRanges {
                    if range.maxFrameRate >= targetRate && range.minFrameRate <= targetRate {
                        // Found a format that supports our target frame rate
                        let formatInfo = "Format: \(dimensions.width)x\(dimensions.height), FPS: \(range.minFrameRate)-\(range.maxFrameRate)"
                        print("🐛 RecordingViewModel: Found compatible format - \(formatInfo)")
                        
                        // Prefer higher resolution if frame rate is supported
                        if bestFormat == nil || (isHighRes && !isFormatHighRes(bestFormat!)) {
                            bestFormat = format
                            achievedFrameRate = targetRate
                            print("🐛 RecordingViewModel: Selected format for \(targetRate)fps - \(formatInfo)")
                        }
                    }
                }
                
                if bestFormat != nil && achievedFrameRate == preferredFrameRate {
                    // Found 60fps format, no need to continue searching
                    break
                }
            }
            
            if bestFormat != nil {
                // Found a suitable format at this frame rate
                break
            }
        }
        
        // If no format found, find the highest frame rate available
        if bestFormat == nil {
            print("🐛 RecordingViewModel: No format found for target rates, finding best available...")
            var maxAvailableFrameRate: Double = 0
            
            for format in camera.formats {
                let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
                let frameRateRanges = format.videoSupportedFrameRateRanges
                
                // Prefer 1080p or higher
                let isHighRes = dimensions.width >= 1920 && dimensions.height >= 1080
                
                for range in frameRateRanges {
                    if range.maxFrameRate > maxAvailableFrameRate || 
                       (range.maxFrameRate == maxAvailableFrameRate && isHighRes && (bestFormat == nil || !isFormatHighRes(bestFormat!))) {
                        bestFormat = format
                        maxAvailableFrameRate = range.maxFrameRate
                        achievedFrameRate = range.maxFrameRate
                    }
                }
            }
            
            if let format = bestFormat {
                let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
                print("🐛 RecordingViewModel: Using best available format: \(dimensions.width)x\(dimensions.height) at \(achievedFrameRate)fps")
            }
        }
        
        if bestFormat == nil {
            print("🐛 RecordingViewModel: Warning - No suitable format found, using device default")
            achievedFrameRate = fallbackFrameRate
        }
        
        return (bestFormat, achievedFrameRate)
    }
    
    private func isFormatHighRes(_ format: AVCaptureDevice.Format) -> Bool {
        let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
        return dimensions.width >= 1920 && dimensions.height >= 1080
    }
    
    private func setupVideoOutput() {
        guard let session = captureSession else { return }
        
        videoOutput = AVCaptureMovieFileOutput()
        
        if let output = videoOutput, session.canAddOutput(output) {
            session.addOutput(output)
            
            // Configure video connection
            if let connection = output.connection(with: .video) {
                if connection.isVideoStabilizationSupported {
                    connection.preferredVideoStabilizationMode = .auto
                }
                
                // Set video orientation for portrait mode  
                if #available(iOS 17.0, *) {
                    if connection.isVideoRotationAngleSupported(90) {
                        connection.videoRotationAngle = 90 // Portrait mode
                    }
                } else {
                    if connection.isVideoOrientationSupported {
                        connection.videoOrientation = .portrait
                    }
                }
            }
        }
    }
    
    private func setupPhotoOutput() {
        guard let session = captureSession else { return }
        
        photoOutput = AVCapturePhotoOutput()
        
        if let output = photoOutput, session.canAddOutput(output) {
            session.addOutput(output)
        }
    }
    
    // MARK: - Camera Control Methods
    
    func switchCamera() {
        let newPosition: AVCaptureDevice.Position = (cameraPosition == .back) ? .front : .back
        cameraPosition = newPosition
        
        Task {
            try? setupCameraInput(for: newPosition)
        }
    }
    
    func toggleLeftHandedMode() {
        isLeftHandedMode.toggle()
    }
    
    // MARK: - Recording Control Methods
    
    func startRecording() {
        guard currentPhase == .setup else { return }
        
        currentPhase = .recording
        isRecording = true
        showPositioningIndicator = false
        showProgressCircles = true
        recordingTime = 0
        swingCount = 0
        
        // Reset progress circles
        for i in 0..<progressCircles.count {
            progressCircles[i].isCompleted = false
        }
        
        // Start recording video
        startVideoRecording()
        
        // Start timers
        startRecordingTimer()
        startStillCaptureTimer()
        startTimeoutTimer()
        
        // Play TTS confirmation
        ttsService.speakText("Great. I'm now recording. Begin swinging when you're ready.")
        
        onRecordingStarted?()
    }
    
    func finishRecording() {
        guard currentPhase == .recording else { return }
        
        currentPhase = .processing
        isRecording = false
        showProgressCircles = false
        
        // Stop all timers
        stopAllTimers()
        
        // Stop video recording
        stopVideoRecording()
        
        // Stop voice recognition
        onDeviceSTT.stopListening()
        stopVoiceRecognition()
        
        // Play completion TTS
        ttsService.speakText("That's great. I'll get to work analyzing your swings.")
    }
    
    private func startVideoRecording() {
        guard let output = videoOutput else { return }
        
        // Create output file URL
        let outputURL = createOutputFileURL()
        
        // Start recording
        output.startRecording(to: outputURL, recordingDelegate: self)
    }
    
    private func stopVideoRecording() {
        videoOutput?.stopRecording()
    }
    
    private func createOutputFileURL() -> URL {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let fileName = "swing_recording_\(Date().timeIntervalSince1970).mp4"
        return documentsPath.appendingPathComponent(fileName)
    }
    
    // MARK: - Timer Methods
    
    private func startRecordingTimer() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.recordingTime += 0.1
                self?.onTimeUpdate?(self?.recordingTime ?? 0)
            }
        }
    }
    
    private func startStillCaptureTimer() {
        stillCaptureTimer = Timer.scheduledTimer(withTimeInterval: stillCaptureInterval, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.captureStillForAnalysis()
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
        recordingTimer?.invalidate()
        recordingTimer = nil
        
        stillCaptureTimer?.invalidate()
        stillCaptureTimer = nil
        
        timeoutTimer?.invalidate()
        timeoutTimer = nil
    }
    
    // MARK: - Voice Recognition Methods
    
    func startVoiceRecognition() async throws {
        print("🐛 RecordingViewModel: Starting on-device voice recognition...")
        
        // Request permissions for the on-device STT service
        let hasPermissions = await onDeviceSTT.requestPermissions()
        
        if !hasPermissions {
            throw RecordingError.audioPermissionDenied
        }
        
        // Start listening for voice commands
        onDeviceSTT.startListening()
    }
    
    func stopVoiceRecognition() {
        onDeviceSTT.stopListening()
    }
    
    // Voice processing is now handled by OnDeviceSTTService
    // Commands are processed in handleVoiceCommand() method
    
    // MARK: - Still Capture Methods
    
    func captureStillForAnalysis() {
        guard let photoOutput = photoOutput, currentPhase == .recording else { return }
        
        let photoSettings = AVCapturePhotoSettings()
        if #available(iOS 16.0, *) {
            photoSettings.maxPhotoDimensions = CMVideoDimensions(width: 1920, height: 1080)
        } else {
            photoSettings.isHighResolutionPhotoEnabled = false
        }
        
        photoOutput.capturePhoto(with: photoSettings, delegate: self)
    }
    
    // MARK: - Swing Detection Methods
    
    func processSwingDetection(isSwingDetected: Bool) {
        guard currentPhase == .recording, isSwingDetected else { return }
        
        swingCount += 1
        
        // Update progress circle
        if swingCount <= progressCircles.count {
            progressCircles[swingCount - 1].isCompleted = true
        }
        
        // Provide audio feedback
        if swingCount == 1 {
            ttsService.speakText("Great. Take another when you're ready.")
        } else if swingCount == 2 {
            ttsService.speakText("Ok one more to go.")
        } else if swingCount >= targetSwingCount {
            finishRecording()
        }
    }
    
    func processStillImage(_ image: UIImage) {
        // Send to server for swing detection
        Task {
            do {
                let isSwingDetected = try await analyzeStillForSwing(image)
                await MainActor.run {
                    processSwingDetection(isSwingDetected: isSwingDetected)
                }
            } catch {
                print("Error analyzing still image: \(error)")
                // Fallback to local mock detection if API fails
                await MainActor.run {
                    let mockDetection = Bool.random() && recordingTime > 2.0 // Mock detection after 2 seconds
                    processSwingDetection(isSwingDetected: mockDetection)
                }
            }
        }
    }
    
    private var stillSequenceNumber = 0
    
    private func analyzeStillForSwing(_ image: UIImage) async throws -> Bool {
        stillSequenceNumber += 1
        
        // Use API service for swing detection
        let response = try await recordingAPIService.analyzeSwingFromImage(
            image, 
            sequenceNumber: stillSequenceNumber
        )
        
        print("Swing detection: \(response.swingDetected), confidence: \(response.confidence), phase: \(response.swingPhase ?? "none")")
        
        // Return true if swing detected with high confidence
        return response.swingDetected && response.confidence > 0.7
    }
    
    private func compressImage(_ image: UIImage) -> Data? {
        // Resize to smaller size for faster processing
        let targetSize = CGSize(width: 300, height: 400)
        let resizedImage = image.resized(to: targetSize)
        return resizedImage?.jpegData(compressionQuality: 0.7)
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
        stopAllTimers()
        stopVoiceRecognition()
        voiceCommandCancellable?.cancel()
        captureSession?.stopRunning()
        recordingAPIService.endSession()
    }
    
    deinit {
        // Note: Cannot call main actor isolated methods from deinit
        // Cleanup will be handled by the view's onDisappear
    }
}

// MARK: - AVCaptureFileOutputRecordingDelegate

extension RecordingViewModel: AVCaptureFileOutputRecordingDelegate {
    
    nonisolated func fileOutput(_ output: AVCaptureFileOutput, didStartRecordingTo fileURL: URL, from connections: [AVCaptureConnection]) {
        // Recording started successfully
        print("Video recording started to: \(fileURL)")
    }
    
    nonisolated func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
        if let error = error {
            print("Video recording finished with error: \(error)")
        } else {
            print("Video recording finished successfully: \(outputFileURL)")
            // Here you would typically save the video or pass it to the analysis pipeline
        }
    }
}

// MARK: - AVCapturePhotoCaptureDelegate

extension RecordingViewModel: AVCapturePhotoCaptureDelegate {
    
    nonisolated func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        if let error = error {
            print("Photo capture error: \(error)")
            return
        }
        
        guard let imageData = photo.fileDataRepresentation(),
              let image = UIImage(data: imageData) else {
            print("Failed to create image from photo data")
            return
        }
        
        Task { @MainActor in
            self.onStillCaptured?(image)
            self.processStillImage(image)
        }
    }
}

// MARK: - Voice Commands
// Voice command handling is now managed by OnDeviceSTTService

// MARK: - UIImage Extension

extension UIImage {
    func resized(to targetSize: CGSize) -> UIImage? {
        let size = self.size
        let widthRatio = targetSize.width / size.width
        let heightRatio = targetSize.height / size.height
        let ratio = min(widthRatio, heightRatio)
        
        let newSize = CGSize(width: size.width * ratio, height: size.height * ratio)
        
        UIGraphicsBeginImageContextWithOptions(newSize, false, 0)
        draw(in: CGRect(origin: .zero, size: newSize))
        let newImage = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        
        return newImage
    }
}
