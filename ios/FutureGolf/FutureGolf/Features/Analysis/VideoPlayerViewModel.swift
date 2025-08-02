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
    
    var isCoachingEnabled = true {
        didSet {
            if !isCoachingEnabled {
                coachingService.stop()
            }
        }
    }
    
    private var timeObserver: Any?
    private var analysisResult: AnalysisResult?
    private let coachingService = CoachingService()
    
    func setupPlayer(with url: URL, analysisResult: AnalysisResult) {
        self.analysisResult = analysisResult
        
        let playerItem = AVPlayerItem(url: url)
        player = AVPlayer(playerItem: playerItem)
        
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
        
        let interval = CMTime(seconds: 0.1, preferredTimescale: 600)
        timeObserver = player?.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
            guard let self = self, !self.isSeeking else { return }
            
            self.currentTime = time.seconds
            self.updateCurrentPhase(for: time.seconds)
        }
        
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(playerDidFinishPlaying),
            name: .AVPlayerItemDidPlayToEndTime,
            object: player?.currentItem
        )
        
        if let firstPhase = analysisResult.swingPhases.first {
            currentPhase = firstPhase
        }
    }
    
    func cleanup() {
        if let timeObserver = timeObserver {
            player?.removeTimeObserver(timeObserver)
        }
        player?.pause()
        isPlaying = false
        player = nil
        coachingService.stop()
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
    
    func jumpToPhase(_ index: Int) {
        guard let phases = analysisResult?.swingPhases,
              index >= 0,
              index < phases.count else { return }
        
        currentPhaseIndex = index
        currentPhase = phases[index]
        
        let time = phases[index].timestamp
        seek(to: time)
        
        if isCoachingEnabled {
            coachingService.speakFeedback(phases[index].feedback)
        }
    }
    
    private func updateCurrentPhase(for time: Double) {
        guard let phases = analysisResult?.swingPhases else { return }
        
        for (index, phase) in phases.enumerated() {
            if index < phases.count - 1 {
                let nextPhase = phases[index + 1]
                if time >= phase.timestamp && time < nextPhase.timestamp {
                    if currentPhaseIndex != index {
                        currentPhaseIndex = index
                        currentPhase = phase
                        
                        if isCoachingEnabled && isPlaying {
                            coachingService.scheduleCoaching(for: phase)
                        }
                    }
                    return
                }
            } else {
                if time >= phase.timestamp {
                    if currentPhaseIndex != index {
                        currentPhaseIndex = index
                        currentPhase = phase
                        
                        if isCoachingEnabled && isPlaying {
                            coachingService.scheduleCoaching(for: phase)
                        }
                    }
                }
            }
        }
    }
    
    @objc private func playerDidFinishPlaying() {
        isPlaying = false
        seek(to: 0)
    }
}

