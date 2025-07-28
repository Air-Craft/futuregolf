import Foundation
import AVFoundation
import Combine

class TTSService: ObservableObject {
    static let shared = TTSService()
    
    private let serverURL = "http://localhost:8000"
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
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
            try AVAudioSession.sharedInstance().setActive(true)
            print("Audio session configured successfully")
        } catch {
            print("Failed to configure audio session: \(error)")
        }
    }
    
    func speakText(_ text: String, completion: @escaping (Bool) -> Void = { _ in }) {
        guard !text.isEmpty else {
            completion(false)
            return
        }
        
        // Add to queue and process
        speechQueue.append((text, completion))
        processNextInQueue()
    }
    
    private func processNextInQueue() {
        guard !isProcessingQueue && !speechQueue.isEmpty else { return }
        
        isProcessingQueue = true
        let (text, completion) = speechQueue.removeFirst()
        
        // Stop any current playback
        stopCurrentPlayback()
        
        isLoading = true
        
        Task {
            do {
                let audioData = try await synthesizeSpeech(text: text)
                await MainActor.run {
                    self.playAudio(data: audioData) { [weak self] success in
                        completion(success)
                        self?.isProcessingQueue = false
                        self?.processNextInQueue()
                    }
                }
            } catch {
                print("TTS Error: \(error)")
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
        guard let url = URL(string: "\(serverURL)/api/v1/tts/coaching") else {
            throw TTSError.invalidURL
        }
        
        let requestBody = TTSRequest(
            text: text,
            voice: "onyx",
            model: "tts-1-hd",
            speed: 0.9
        )
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw TTSError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw TTSError.serverError(httpResponse.statusCode)
        }
        
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