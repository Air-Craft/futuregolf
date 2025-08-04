import Foundation
import Speech
import AVFoundation
import Combine
import Factory

class OnDeviceSTTService: NSObject, ObservableObject {
    // MARK: - Published Properties
    @Published var isListening = false
    @Published var isAvailable = false
    @Published var transcript = ""
    @Published var lastCommand: VoiceCommand?
    
    // MARK: - Private Properties
    private let speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    private var audioRouteManager: AudioRouteManager?
    
    // Command detection
    private let startCommandPatterns = [
        "begin",
        "start",
        "ready",
        "let's go",
        "do it",
        "record"
        // Removed "recording" to prevent TTS feedback loops
    ]
    
    private let stopCommandPatterns = [
        "stop",
        "finish",
        "done",
        "cancel",
        "abort",
        "end",
        "that's enough",
        "I've had enough",
        "that is enough"
    ]
    
    override init() {
        // Initialize with user's preferred language, fallback to English
        self.speechRecognizer = SFSpeechRecognizer(locale: Locale.current) ?? SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        super.init()
        
        Task { @MainActor in
            self.audioRouteManager = Container.shared.audioRouteManager()
        }
        
        setupAvailability()
    }
    
    // MARK: - Public Methods
    
    func requestPermissions() async -> Bool {
        // Request speech recognition permission
        let speechStatus = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status)
            }
        }
        
        // Request microphone permission
        let microphoneStatus: Bool
        if #available(iOS 17.0, *) {
            microphoneStatus = await AVAudioApplication.requestRecordPermission()
        } else {
            microphoneStatus = await withCheckedContinuation { continuation in
                AVAudioSession.sharedInstance().requestRecordPermission { granted in
                    continuation.resume(returning: granted)
                }
            }
        }
        
        let hasPermissions = speechStatus == .authorized && microphoneStatus
        
        await MainActor.run {
            self.updateAvailability()
        }
        
        return hasPermissions
    }
    
    func startListening() {
        guard canStartListening() else {
            if Config.isDebugEnabled {
                print("Cannot start listening: requirements not met")
            }
            return
        }
        
        // Stop any existing recognition
        stopListening()
        
        do {
            try startRecognition()
            isListening = true
            if Config.isDebugEnabled {
                print("Started voice command listening")
            }
        } catch {
            if Config.isDebugEnabled {
                print("Failed to start voice recognition: \(error)")
            }
        }
    }
    
    func stopListening() {
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest = nil
        
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        
        isListening = false
        
        if Config.isDebugEnabled {
            print("Stopped voice command listening")
        }
    }
    
    // MARK: - Private Methods
    
    private func setupAvailability() {
        updateAvailability()
        
        // Monitor speech recognizer availability changes
        speechRecognizer?.delegate = self
    }
    
    private func updateAvailability() {
        guard let recognizer = speechRecognizer else {
            isAvailable = false
            return
        }
        
        let hasPermissions = SFSpeechRecognizer.authorizationStatus() == .authorized
        let deviceSupported = recognizer.isAvailable && recognizer.supportsOnDeviceRecognition
        
        isAvailable = hasPermissions && deviceSupported
    }
    
    private func canStartListening() -> Bool {
        return isAvailable && !isListening && speechRecognizer != nil
    }
    
    private func startRecognition() throws {
        // Use AudioRouteManager to configure for recording
        Task { @MainActor in
            audioRouteManager?.configureForRecording()
        }
        
        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            throw STTError.recognitionUnavailable
        }
        
        // Configure for on-device processing
        recognitionRequest.requiresOnDeviceRecognition = true
        recognitionRequest.shouldReportPartialResults = true
        
        // Set up audio input
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        // Log input configuration
        print("🎤 STT Audio input format: \(recordingFormat)")
        print("🎤 STT Input node: \(inputNode)")
        
        // Ensure we're using the correct input
        let session = AVAudioSession.sharedInstance()
        if let preferredInput = session.preferredInput {
            print("🎤 STT Preferred input: \(preferredInput.portName)")
        }
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }
        
        // Start audio engine
        audioEngine.prepare()
        try audioEngine.start()
        
        // Start recognition task
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            self?.handleRecognitionResult(result: result, error: error)
        }
    }
    
    private func handleRecognitionResult(result: SFSpeechRecognitionResult?, error: Error?) {
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            
            if let error = error {
                if Config.isDebugEnabled {
                    print("Speech recognition error: \(error)")
                }
                self.stopListening()
                return
            }
            
            guard let result = result else { return }
            
            // Update transcript
            let newTranscript = result.bestTranscription.formattedString
            self.transcript = newTranscript
            
            // Check for commands
            if let command = self.detectCommand(in: newTranscript) {
                self.lastCommand = command
                if Config.isDebugEnabled {
                    print("Voice command detected: \(command)")
                }
            }
            
            // If this is a final result, restart listening for next command
            if result.isFinal {
                // Brief pause before restarting to avoid echo
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    if self.isListening {
                        self.startListening()
                    }
                }
            }
        }
    }
    
    private func detectCommand(in transcript: String) -> VoiceCommand? {
        let lowercased = transcript.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Check if transcript contains any of our command patterns
        // Check for stop commands first (higher priority when recording)
        for pattern in stopCommandPatterns {
            if lowercased.contains(pattern) {
                if Config.isDebugEnabled {
                    print("Detected stop command pattern '\(pattern)' in: '\(transcript)'")
                }
                return .stopRecording
            }
        }
        
        // Check for start commands
        for pattern in startCommandPatterns {
            if lowercased.contains(pattern) {
                if Config.isDebugEnabled {
                    print("Detected start command pattern '\(pattern)' in: '\(transcript)'")
                }
                return .startRecording
            }
        }
        
        return nil
    }
}

// MARK: - SFSpeechRecognizerDelegate

extension OnDeviceSTTService: SFSpeechRecognizerDelegate {
    func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        DispatchQueue.main.async {
            self.updateAvailability()
            if Config.isDebugEnabled {
                print("Speech recognizer availability changed: \(available)")
            }
        }
    }
}

// MARK: - Supporting Types

enum VoiceCommand: Equatable {
    case startRecording
    case stopRecording
    
    var description: String {
        switch self {
        case .startRecording:
            return "Start Recording"
        case .stopRecording:
            return "Stop Recording"
        }
    }
}

enum STTError: LocalizedError {
    case recognitionUnavailable
    case permissionDenied
    case audioEngineFailure
    
    var errorDescription: String? {
        switch self {
        case .recognitionUnavailable:
            return "Speech recognition is not available"
        case .permissionDenied:
            return "Speech recognition permission denied"
        case .audioEngineFailure:
            return "Audio engine failed to start"
        }
    }
}
