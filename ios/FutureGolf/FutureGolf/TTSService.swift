import Foundation
import AVFoundation
import Combine

class TTSService: ObservableObject {
    static let shared = TTSService()
    
    private let serverURL = Config.serverBaseURL
    private var audioPlayer: AVAudioPlayer?
    private var audioPlayerDelegate: AudioPlayerDelegate?
    private var speechQueue: [(String, (Bool) -> Void)] = []
    private var isProcessingQueue = false
    @Published var isPlaying = false
    @Published var isLoading = false
    
    private init() {
        configureAudioSession()
    }
    
    private func configureAudioSession() {
        do {
            // Use playAndRecord to be compatible with STT that might be running
            try AVAudioSession.sharedInstance().setCategory(.playAndRecord, mode: .spokenAudio, options: [.duckOthers, .defaultToSpeaker])
            try AVAudioSession.sharedInstance().setActive(true)
            print("🎵 TTS: Audio session configured successfully")
            print("🎵 TTS: Audio session category: \(AVAudioSession.sharedInstance().category)")
            print("🎵 TTS: Audio session mode: \(AVAudioSession.sharedInstance().mode)")
            print("🎵 TTS: Audio session options: \(AVAudioSession.sharedInstance().categoryOptions)")
        } catch {
            print("🎵 TTS: Failed to configure audio session: \(error)")
        }
    }
    
    func speakText(_ text: String, completion: @escaping (Bool) -> Void = { _ in }) {
        guard !text.isEmpty else {
            print("🎵 TTS: Empty text provided, skipping")
            completion(false)
            return
        }
        
        print("🎵 TTS: Received request to speak: '\(text)'")
        
        // Add to queue and process
        speechQueue.append((text, completion))
        print("🎵 TTS: Added to queue. Queue size: \(speechQueue.count)")
        processNextInQueue()
    }
    
    private func processNextInQueue() {
        guard !isProcessingQueue && !speechQueue.isEmpty else { 
            if isProcessingQueue {
                print("🎵 TTS: Already processing queue")
            } else if speechQueue.isEmpty {
                print("🎵 TTS: Queue is empty")
            }
            return 
        }
        
        print("🎵 TTS: Starting to process next item in queue")
        isProcessingQueue = true
        let (text, completion) = speechQueue.removeFirst()
        
        print("🎵 TTS: Processing text: '\(text)'")
        
        // Stop any current playback
        stopCurrentPlayback()
        
        isLoading = true
        print("🎵 TTS: Set loading state to true, starting synthesis...")
        
        Task {
            do {
                print("🎵 TTS: Calling synthesizeSpeech...")
                let audioData = try await synthesizeSpeech(text: text)
                print("🎵 TTS: Successfully synthesized \(audioData.count) bytes of audio data")
                await MainActor.run {
                    self.playAudio(data: audioData) { [weak self] success in
                        print("🎵 TTS: Playback completed with success: \(success)")
                        completion(success)
                        self?.isProcessingQueue = false
                        self?.processNextInQueue()
                    }
                }
            } catch {
                print("🎵 TTS Error: \(error)")
                await MainActor.run {
                    self.isLoading = false
                    completion(false)
                    self.isProcessingQueue = false
                    self.processNextInQueue()
                }
            }
        }
    }
    
    private func synthesizeSpeech(text: String) async throws -> Data {
        let urlString = "\(serverURL)/api/v1/tts/coaching"
        print("🎵 TTS: Attempting to synthesize speech at URL: \(urlString)")
        
        guard let url = URL(string: urlString) else {
            print("🎵 TTS: Invalid URL: \(urlString)")
            throw TTSError.invalidURL
        }
        
        let requestBody = TTSRequest(
            text: text,
            voice: "onyx",
            model: "tts-1-hd",
            speed: 0.9
        )
        
        print("🎵 TTS: Request body: \(requestBody)")
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        print("🎵 TTS: Sending POST request to \(url)")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        print("🎵 TTS: Received response with \(data.count) bytes")
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("🎵 TTS: Invalid response type")
            throw TTSError.invalidResponse
        }
        
        print("🎵 TTS: HTTP Status Code: \(httpResponse.statusCode)")
        
        guard httpResponse.statusCode == 200 else {
            print("🎵 TTS: Server error with status code: \(httpResponse.statusCode)")
            if let errorString = String(data: data, encoding: .utf8) {
                print("🎵 TTS: Error response body: \(errorString)")
            }
            throw TTSError.serverError(httpResponse.statusCode)
        }
        
        print("🎵 TTS: Successfully received audio data")
        return data
    }
    
    private func playAudio(data: Data, completion: @escaping (Bool) -> Void) {
        do {
            print("Creating AVAudioPlayer with \(data.count) bytes of audio data")
            audioPlayer = try AVAudioPlayer(data: data)
            audioPlayerDelegate = AudioPlayerDelegate { [weak self] success in
                DispatchQueue.main.async {
                    print("Audio playback finished with success: \(success)")
                    self?.isPlaying = false
                    self?.isLoading = false
                    self?.audioPlayerDelegate = nil
                    completion(success)
                }
            }
            audioPlayer?.delegate = audioPlayerDelegate
            
            isLoading = false
            isPlaying = true
            
            print("Starting audio playback...")
            let didStart = audioPlayer?.play() ?? false
            print("Audio player play() returned: \(didStart)")
            
        } catch {
            print("Failed to play audio: \(error)")
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
}

// MARK: - Data Models

struct TTSRequest: Codable {
    let text: String
    let voice: String
    let model: String
    let speed: Double
}

enum TTSError: LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid TTS server URL"
        case .invalidResponse:
            return "Invalid server response"
        case .serverError(let code):
            return "Server error: \(code)"
        case .networkError:
            return "Network error"
        }
    }
}

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