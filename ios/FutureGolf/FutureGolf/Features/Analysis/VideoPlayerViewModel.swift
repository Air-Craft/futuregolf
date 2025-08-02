import SwiftUI
import AVKit
import AVFoundation
import Observation

@MainActor
@Observable
class VideoPlayerViewModel {
    var player: AVPlayer?
    var isPlaying = false
    var currentTime: Double = 0
    var duration: Double = 0
    var currentPhase: SwingPhase?
    var currentPhaseIndex = 0
    var currentFeedback: String?
    var isSeeking = false
    
    var isCoachingEnabled = true
    private var timeObserver: Any?
    private var analysisResult: AnalysisResult?
    private let synthesizer = AVSpeechSynthesizer()
    private var coachingTimer: Timer?
    
    func setupPlayer(with url: URL, analysisResult: AnalysisResult) {
        self.analysisResult = analysisResult
        
        let playerItem = AVPlayerItem(url: url)
        player = AVPlayer(playerItem: playerItem)
        
        // Get duration
        Task {
            do {
                let duration = try await playerItem.asset.load(.duration)
                await MainActor.run {
                    self.duration = duration.seconds
                }
            } catch {
                print("Failed to load duration: \(error)")
            }
        }
        
        // Add time observer
        let interval = CMTime(seconds: 0.1, preferredTimescale: 600)
        timeObserver = player?.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
            guard let self = self, !self.isSeeking else { return }
            
            self.currentTime = time.seconds
            self.updateCurrentPhase(for: time.seconds)
        }
        
        // Add notification observers
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(playerDidFinishPlaying),
            name: .AVPlayerItemDidPlayToEndTime,
            object: player?.currentItem
        )
        
        // Set initial phase
        if let firstPhase = analysisResult.swingPhases.first {
            currentPhase = firstPhase
        }
        
        // Setup coaching
        setupCoaching()
    }
    
    func cleanup() {
        if let timeObserver = timeObserver {
            player?.removeTimeObserver(timeObserver)
        }
        player?.pause()
        isPlaying = false
        player = nil
        coachingTimer?.invalidate()
        synthesizer.stopSpeaking(at: .immediate)
        NotificationCenter.default.removeObserver(self)
    }
    
    func togglePlayPause() {
        if isPlaying {
            player?.pause()
        } else {
            player?.play()
        }
        isPlaying.toggle()
    }
    
    func seek(to time: Double) {
        let cmTime = CMTime(seconds: time, preferredTimescale: 600)
        player?.seek(to: cmTime)
    }
    
    func setPlaybackSpeed(_ speed: Float) {
        player?.rate = isPlaying ? speed : 0
    }
    
    func previousPhase() {
        guard currentPhaseIndex > 0,
              let phases = analysisResult?.swingPhases else { return }
        
        currentPhaseIndex -= 1
        jumpToPhase(currentPhaseIndex)
    }
    
    func nextPhase() {
        guard let phases = analysisResult?.swingPhases,
              currentPhaseIndex < phases.count - 1 else { return }
        
        currentPhaseIndex += 1
        jumpToPhase(currentPhaseIndex)
    }
    
    func testCoaching(for phaseIndex: Int? = nil) {
        guard let phases = analysisResult?.swingPhases else { return }
        
        let index = phaseIndex ?? currentPhaseIndex
        guard index >= 0, index < phases.count else { return }
        
        let phase = phases[index]
        speakFeedback(phase.feedback)
        
        // Also show visual feedback
        withAnimation {
            currentFeedback = phase.feedback
        }
        
        // Hide feedback after speech duration estimate
        let wordCount = phase.feedback.split(separator: " ").count
        let estimatedDuration = Double(wordCount) * 0.15 + 2.0  // Rough estimate
        
        DispatchQueue.main.asyncAfter(deadline: .now() + estimatedDuration) { [weak self] in
            withAnimation {
                self?.currentFeedback = nil
            }
        }
    }
    
    func jumpToPhase(_ index: Int) {
        guard let phases = analysisResult?.swingPhases,
              index >= 0,
              index < phases.count else { return }
        
        currentPhaseIndex = index
        currentPhase = phases[index]
        
        let time = phases[index].timestamp
        seek(to: time)
        
        // Speak the phase feedback if coaching is enabled
        if isCoachingEnabled {
            speakFeedback(phases[index].feedback)
        }
    }
    
    private func updateCurrentPhase(for time: Double) {
        guard let phases = analysisResult?.swingPhases else { return }
        
        // Find the current phase based on timestamp
        for (index, phase) in phases.enumerated() {
            if index < phases.count - 1 {
                let nextPhase = phases[index + 1]
                if time >= phase.timestamp && time < nextPhase.timestamp {
                    if currentPhaseIndex != index {
                        currentPhaseIndex = index
                        currentPhase = phase
                        
                        // Trigger coaching for new phase
                        if isCoachingEnabled && isPlaying {
                            scheduleCoaching(for: phase)
                        }
                    }
                    return
                }
            } else {
                // Last phase
                if time >= phase.timestamp {
                    if currentPhaseIndex != index {
                        currentPhaseIndex = index
                        currentPhase = phase
                        
                        if isCoachingEnabled && isPlaying {
                            scheduleCoaching(for: phase)
                        }
                    }
                }
            }
        }
    }
    
    private func setupCoaching() {
        synthesizer.delegate = nil
        
        // Configure voice - prefer enhanced voices for better quality
        let preferredVoices = [
            "com.apple.voice.enhanced.en-US.Ava",
            "com.apple.voice.premium.en-US.Zoe",
            "com.apple.ttsbundle.Samantha-compact",
            "com.apple.ttsbundle.siri_female_en-US_compact"
        ]
        
        var selectedVoice: AVSpeechSynthesisVoice?
        
        // Try to find a preferred voice
        for voiceIdentifier in preferredVoices {
            if let voice = AVSpeechSynthesisVoice(identifier: voiceIdentifier) {
                selectedVoice = voice
                break
            }
        }
        
        // Fallback to default US English voice
        if selectedVoice == nil {
            selectedVoice = AVSpeechSynthesisVoice(language: "en-US")
        }
        
        // Store the selected voice for consistent use
        if let voice = selectedVoice {
            UserDefaults.standard.set(voice.identifier, forKey: "preferredCoachingVoice")
        }
    }
    
    private func scheduleCoaching(for phase: SwingPhase) {
        coachingTimer?.invalidate()
        
        // Show feedback immediately
        withAnimation {
            currentFeedback = phase.feedback
        }
        
        // Schedule speech after a short delay
        coachingTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: false) { [weak self] _ in
            self?.speakFeedback(phase.feedback)
        }
        
        // Hide feedback after 4 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 4.0) { [weak self] in
            withAnimation {
                self?.currentFeedback = nil
            }
        }
    }
    
    private func speakFeedback(_ text: String) {
        guard isCoachingEnabled else { return }
        
        synthesizer.stopSpeaking(at: .word)
        
        let utterance = AVSpeechUtterance(string: text)
        
        // Configurable speech rate (stored in UserDefaults)
        let speechRate = UserDefaults.standard.float(forKey: "coachingSpeechRate")
        utterance.rate = speechRate > 0 ? speechRate : 0.48  // Slightly slower than default
        
        utterance.pitchMultiplier = 1.05  // Slightly higher pitch for clarity
        utterance.volume = 0.9
        
        // Add pre and post utterance delays for better timing
        utterance.preUtteranceDelay = 0.2
        utterance.postUtteranceDelay = 0.3
        
        // Use the stored preferred voice
        if let voiceIdentifier = UserDefaults.standard.string(forKey: "preferredCoachingVoice"),
           let voice = AVSpeechSynthesisVoice(identifier: voiceIdentifier) {
            utterance.voice = voice
        } else if let voice = AVSpeechSynthesisVoice(language: "en-US") {
            utterance.voice = voice
        }
        
        synthesizer.speak(utterance)
    }
    
    @objc private func playerDidFinishPlaying() {
        isPlaying = false
        seek(to: 0)
    }
}
