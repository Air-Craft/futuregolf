import Foundation
import AVFoundation
import Combine

class TTSService: NSObject, ObservableObject {
    static let shared = TTSService()
    
    private let serverURL = Config.serverBaseURL
    private var audioPlayer: AVAudioPlayer?
    private var audioPlayerDelegate: AudioPlayerDelegate?
    private var speechQueue: [(String, (Bool) -> Void)] = []
    private var isProcessingQueue = false
    @Published var isPlaying = false
    @Published var isLoading = false
    
    // TTS Cache Manager
    let cacheManager = TTSCacheManager()
    
    // Fallback iOS TTS
    private let speechSynthesizer = AVSpeechSynthesizer()
    private var currentSpeechCompletion: ((Bool) -> Void)?
    
    private override init() {
        super.init()
        configureAudioSession()
    }
    
    private func configureAudioSession() {
        do {
            // Use playAndRecord to be compatible with STT that might be running
            try AVAudioSession.sharedInstance().setCategory(.playAndRecord, mode: .default, options: [.duckOthers, .defaultToSpeaker])
            try AVAudioSession.sharedInstance().setActive(true, options: [])
            print("🗣️ TTS: Audio session configured successfully")
            print("🗣️ TTS: Audio session category: \(AVAudioSession.sharedInstance().category)")
            print("🗣️ TTS: Audio session mode: \(AVAudioSession.sharedInstance().mode)")
            print("🗣️ TTS: Audio session options: \(AVAudioSession.sharedInstance().categoryOptions)")
        } catch {
            print("🗣️ TTS: Failed to configure audio session: \(error)")
        }
    }
    
    func speakText(_ text: String, completion: @escaping (Bool) -> Void = { _ in }) {
        guard !text.isEmpty else {
            print("🗣️ TTS: Empty text provided, skipping")
            completion(false)
            return
        }
        
        let startTime = Date()
        print("🗣️ TTS: [\(startTime.timeIntervalSince1970)] Received request to speak: '\(text)'")
        
        // Add to queue and process
        speechQueue.append((text, { success in
            let totalTime = Date().timeIntervalSince(startTime)
            print("🗣️ TTS: Total time from request to completion: \(String(format: "%.2f", totalTime))s")
            completion(success)
        }))
        print("🗣️ TTS: Added to queue. Queue size: \(speechQueue.count)")
        processNextInQueue()
    }
    
    private func processNextInQueue() {
        guard !isProcessingQueue && !speechQueue.isEmpty else { 
            if isProcessingQueue {
                print("🗣️ TTS: Already processing queue")
            } else if speechQueue.isEmpty {
                print("🗣️ TTS: Queue is empty")
            }
            return 
        }
        
        print("🗣️ TTS: Starting to process next item in queue")
        isProcessingQueue = true
        let (text, completion) = speechQueue.removeFirst()
        
        print("🗣️ TTS: Processing text: '\(text)'")
        
        // Stop any current playback
        stopCurrentPlayback()
        
        isLoading = true
        print("🗣️ TTS: Set loading state to true, starting synthesis...")
        
        Task {
            do {
                let audioData: Data
                
                // Try to get cached audio first
                if let cachedData = await cacheManager.getCachedAudio(for: text) {
                    print("🗣️💾 TTS: Using cached audio for: '\(text.prefix(30))...'")
                    audioData = cachedData
                    
                    // Skip loading state since we have instant access
                    await MainActor.run {
                        self.isLoading = false
                    }
                } else {
                    // Debug: Check cache status when cache miss occurs
                    if TTSPhraseManager.shared.isCacheable(text: text) {
                        print("🗣️💾 TTS: Cache miss for cacheable phrase!")
                        await MainActor.run {
                            self.cacheManager.debugListCachedFiles()
                        }
                    }
                    // Check if this is a cacheable phrase but user is going too fast
                    let isCacheWarming = await MainActor.run { self.cacheManager.isCacheWarming }
                    if TTSPhraseManager.shared.isCacheable(text: text) && isCacheWarming {
                        print("🗣️💾 TTS: ⚠️ Cache still warming for cacheable phrase, skipping playback to avoid delay")
                        completion(false)
                        self.isProcessingQueue = false
                        self.processNextInQueue()
                        return
                    }
                    
                    // Synthesize from server
                    let synthesisStart = Date()
                    print("🗣️ TTS: [\(synthesisStart.timeIntervalSince1970)] No cache found, synthesizing: '\(text.prefix(30))...'")
                    audioData = try await synthesizeSpeech(text: text)
                    let synthesisTime = Date().timeIntervalSince(synthesisStart)
                    print("🗣️ TTS: Successfully synthesized \(audioData.count) bytes in \(String(format: "%.2f", synthesisTime))s")
                    
                    // Save to cache if it's a cacheable phrase
                    await MainActor.run {
                        self.cacheManager.saveToCacheIfCacheable(text: text, data: audioData)
                    }
                }
                
                await MainActor.run {
                    let playbackStart = Date()
                    self.playAudio(data: audioData) { [weak self] success in
                        let playbackTime = Date().timeIntervalSince(playbackStart)
                        print("🗣️ TTS: Playback completed in \(String(format: "%.2f", playbackTime))s with success: \(success)")
                        completion(success)
                        self?.isProcessingQueue = false
                        self?.processNextInQueue()
                    }
                }
            } catch {
//                print("🎵 TTS Error: \(error) - Falling back to system TTS")
//                await MainActor.run {
//                    // Fallback to iOS built-in TTS
//                    self.fallbackToSystemTTS(text: text, completion: completion)
//                    self.isProcessingQueue = false
//                    self.processNextInQueue()
//                }
            }
        }
    }
    
    private func synthesizeSpeech(text: String) async throws -> Data {
        let urlString = "\(serverURL)/api/v1/tts/coaching"
        print("🗣️ TTS: Attempting to synthesize speech at URL: \(urlString)")
        
        guard let url = URL(string: urlString) else {
            print("🗣️ TTS: Invalid URL: \(urlString)")
            throw TTSError.invalidURL
        }
        
        let requestBody = TTSRequest(
            text: text,
            voice: "onyx",
            model: "tts-1-hd",
            speed: 0.9
        )
        
        print("🗣️ TTS: Request body: \(requestBody)")
        
        // Use default URLSession configuration
        let session = URLSession.shared
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        let networkStart = Date()
        print("🗣️ TTS: [\(networkStart.timeIntervalSince1970)] Sending POST request to \(url)")
        
        let (data, response) = try await session.data(for: request)
        let networkTime = Date().timeIntervalSince(networkStart)
        
        print("🗣️ TTS: Received response with \(data.count) bytes in \(String(format: "%.2f", networkTime))s")
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("🗣️ TTS: Invalid response type")
            throw TTSError.invalidResponse
        }
        
        print("🗣️ TTS: HTTP Status Code: \(httpResponse.statusCode)")
        
        guard httpResponse.statusCode == 200 else {
            print("🗣️ TTS: Server error with status code: \(httpResponse.statusCode)")
            if let errorString = String(data: data, encoding: .utf8) {
                print("🗣️ TTS: Error response body: \(errorString)")
            }
            throw TTSError.serverError(httpResponse.statusCode)
        }
        
        print("🗣️ TTS: Successfully received audio data")
        return data
    }
    
    private func playAudio(data: Data, completion: @escaping (Bool) -> Void) {
        do {
            print("🗣️ TTS: Creating AVAudioPlayer with \(data.count) bytes of audio data")
            
            // Reconfigure audio session for playback
            try AVAudioSession.sharedInstance().setCategory(.playAndRecord, mode: .default, options: [.duckOthers, .defaultToSpeaker])
            try AVAudioSession.sharedInstance().setActive(true, options: [])
            
            audioPlayer = try AVAudioPlayer(data: data)
            audioPlayer?.volume = 1.0  // Maximum volume
            audioPlayer?.prepareToPlay()
            
            print("🗣️ TTS: Audio player created. Format: \(audioPlayer?.format.debugDescription ?? "unknown")")
            print("🗣️ TTS: Audio player duration: \(audioPlayer?.duration ?? 0) seconds")
            print("🗣️ TTS: Audio player volume: \(audioPlayer?.volume ?? 0)")
            print("🗣️ TTS: Device volume: \(AVAudioSession.sharedInstance().outputVolume)")
            
            audioPlayerDelegate = AudioPlayerDelegate { [weak self] success in
                DispatchQueue.main.async {
                    print("🗣️ TTS: Audio playback finished with success: \(success)")
                    self?.isPlaying = false
                    self?.isLoading = false
                    self?.audioPlayerDelegate = nil
                    completion(success)
                }
            }
            audioPlayer?.delegate = audioPlayerDelegate
            
            isLoading = false
            isPlaying = true
            
            print("🗣️ TTS: Starting audio playback...")
            let didStart = audioPlayer?.play() ?? false
            print("🗣️ TTS: Audio player play() returned: \(didStart)")
            
            if !didStart {
                print("🗣️ TTS: Failed to start playback, checking audio player state")
                print("🗣️ TTS: Audio player isPlaying: \(audioPlayer?.isPlaying ?? false)")
                print("🗣️ TTS: Audio session category: \(AVAudioSession.sharedInstance().category)")
                print("🗣️ TTS: Audio session isOtherAudioPlaying: \(AVAudioSession.sharedInstance().isOtherAudioPlaying)")
            }
            
        } catch {
            print("🗣️ TTS: Failed to play audio: \(error)")
            isLoading = false
            completion(false)
        }
    }
    
    private func stopCurrentPlayback() {
        audioPlayer?.stop()
        audioPlayer = nil
        audioPlayerDelegate = nil
        isPlaying = false
        isLoading = false
    }
    
    func stopSpeaking() {
        stopCurrentPlayback()
        speechQueue.removeAll()
        isProcessingQueue = false
        
        // Also stop system TTS if it's running
        if speechSynthesizer.isSpeaking {
            speechSynthesizer.stopSpeaking(at: .immediate)
        }
    }
    
    func pauseSpeaking() {
        audioPlayer?.pause()
        isPlaying = false
    }
    
    func resumeSpeaking() {
        audioPlayer?.play()
        isPlaying = true
    }
    
    var isSpeaking: Bool {
        return isPlaying || isLoading
    }
    
    // MARK: - Fallback System TTS
    
    private func fallbackToSystemTTS(text: String, completion: @escaping (Bool) -> Void) {
        print("🗣️ TTS: Using iOS system TTS as fallback")
        
        // Stop any existing speech
        if speechSynthesizer.isSpeaking {
            speechSynthesizer.stopSpeaking(at: .immediate)
        }
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = 0.5  // Slightly slower than default
        utterance.volume = 1.0
        
        currentSpeechCompletion = completion
        speechSynthesizer.delegate = self
        
        isLoading = false
        isPlaying = true
        
        speechSynthesizer.speak(utterance)
    }
    
}

// MARK: - AVSpeechSynthesizerDelegate

extension TTSService: AVSpeechSynthesizerDelegate {
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        print("🗣️ TTS: System TTS finished speaking")
        isPlaying = false
        currentSpeechCompletion?(true)
        currentSpeechCompletion = nil
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        print("🗣️ TTS: System TTS was cancelled")
        isPlaying = false
        currentSpeechCompletion?(false)
        currentSpeechCompletion = nil
    }
}

// MARK: - Data Models (shared with TTSCacheManager)

// MARK: - Audio Player Delegate

private class AudioPlayerDelegate: NSObject, AVAudioPlayerDelegate {
    private let completion: (Bool) -> Void
    
    init(completion: @escaping (Bool) -> Void) {
        self.completion = completion
        super.init()
    }
    
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        completion(flag)
    }
    
    func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        print("Audio player decode error: \(error?.localizedDescription ?? "Unknown")")
        completion(false)
    }
}
