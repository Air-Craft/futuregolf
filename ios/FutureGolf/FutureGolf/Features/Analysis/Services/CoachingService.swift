import Foundation
import AVFoundation
import SwiftUI
import Combine

@MainActor
class CoachingService: NSObject, AVSpeechSynthesizerDelegate {
    @Published var currentFeedback: String?
    
    private let synthesizer = AVSpeechSynthesizer()
    private var coachingTimer: Timer?
    
    override init() {
        super.init()
        setupCoaching()
    }
    
    func scheduleCoaching(for phase: SwingPhase) {
        coachingTimer?.invalidate()
        
        withAnimation {
            currentFeedback = phase.feedback
        }
        
        coachingTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: false) { [weak self] _ in
            self?.speakFeedback(phase.feedback)
        }
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 4.0) { [weak self] in
            withAnimation {
                self?.currentFeedback = nil
            }
        }
    }
    
    func speakFeedback(_ text: String) {
        synthesizer.stopSpeaking(at: .word)
        
        let utterance = AVSpeechUtterance(string: text)
        let speechRate = UserDefaults.standard.float(forKey: "coachingSpeechRate")
        utterance.rate = speechRate > 0 ? speechRate : 0.48
        utterance.pitchMultiplier = 1.05
        utterance.volume = 0.9
        utterance.preUtteranceDelay = 0.2
        utterance.postUtteranceDelay = 0.3
        
        if let voiceIdentifier = UserDefaults.standard.string(forKey: "preferredCoachingVoice"),
           let voice = AVSpeechSynthesisVoice(identifier: voiceIdentifier) {
            utterance.voice = voice
        } else if let voice = AVSpeechSynthesisVoice(language: "en-US") {
            utterance.voice = voice
        }
        
        synthesizer.speak(utterance)
    }
    
    private func setupCoaching() {
        synthesizer.delegate = self
        
        let preferredVoices = [
            "com.apple.voice.enhanced.en-US.Ava",
            "com.apple.voice.premium.en-US.Zoe",
            "com.apple.ttsbundle.Samantha-compact",
            "com.apple.ttsbundle.siri_female_en-US_compact"
        ]
        
        var selectedVoice: AVSpeechSynthesisVoice?
        
        for voiceIdentifier in preferredVoices {
            if let voice = AVSpeechSynthesisVoice(identifier: voiceIdentifier) {
                selectedVoice = voice
                break
            }
        }
        
        if selectedVoice == nil {
            selectedVoice = AVSpeechSynthesisVoice(language: "en-US")
        }
        
        if let voice = selectedVoice {
            UserDefaults.standard.set(voice.identifier, forKey: "preferredCoachingVoice")
        }
    }
    
    func stop() {
        coachingTimer?.invalidate()
        synthesizer.stopSpeaking(at: .immediate)
    }
}
