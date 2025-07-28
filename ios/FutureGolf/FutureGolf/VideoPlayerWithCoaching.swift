import SwiftUI
import AVKit
import AVFoundation
import Observation

struct VideoPlayerWithCoaching: View {
    let analysisResult: AnalysisResult
    let videoURL: URL
    
    @State private var playerViewModel = VideoPlayerViewModel()
    @State private var isCoachingEnabled = true
    @State private var currentPhaseIndex = 0
    @State private var showPhaseOverlay = true
    @State private var playbackSpeed: Float = 1.0
    @State private var showControls = true
    @State private var hideControlsTimer: Timer?
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Video Player
                VideoPlayer(player: playerViewModel.player) {
                    // Custom overlay
                    if showPhaseOverlay {
                        phaseOverlay
                    }
                }
                .onAppear {
                    playerViewModel.setupPlayer(with: videoURL, analysisResult: analysisResult)
                }
                .onDisappear {
                    playerViewModel.cleanup()
                }
                .onTapGesture {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        showControls.toggle()
                    }
                    resetHideControlsTimer()
                }
                
                // Custom Controls
                if showControls {
                    VStack {
                        Spacer()
                        customControlsView
                            .padding()
                            .liquidGlassBackground(intensity: .heavy, cornerRadius: 20)
                            .padding()
                    }
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    Toggle("Coaching Voice", isOn: $isCoachingEnabled)
                        .onChange(of: isCoachingEnabled) { _, enabled in
                            playerViewModel.isCoachingEnabled = enabled
                        }
                    
                    Toggle("Phase Overlay", isOn: $showPhaseOverlay)
                    
                    Menu("Playback Speed") {
                        Button("0.25x") { setPlaybackSpeed(0.25) }
                        Button("0.5x") { setPlaybackSpeed(0.5) }
                        Button("Normal") { setPlaybackSpeed(1.0) }
                        Button("1.5x") { setPlaybackSpeed(1.5) }
                        Button("2x") { setPlaybackSpeed(2.0) }
                    }
                } label: {
                    Image(systemName: "gearshape")
                        .symbolRenderingMode(.hierarchical)
                }
            }
        }
        .onAppear {
            resetHideControlsTimer()
        }
    }
    
    private var phaseOverlay: some View {
        VStack {
            HStack {
                // Current Phase Indicator
                if let currentPhase = playerViewModel.currentPhase {
                    LiquidGlassCard {
                        HStack(spacing: 12) {
                            Image(systemName: phaseIcon(for: currentPhase.name))
                                .font(.title2)
                                .symbolRenderingMode(.hierarchical)
                                .foregroundStyle(.tint)
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text(currentPhase.name)
                                    .font(.headline)
                                    .foregroundColor(.glassText)
                                Text("Phase \(playerViewModel.currentPhaseIndex + 1) of \(analysisResult.swingPhases.count)")
                                    .font(.caption)
                                    .foregroundColor(.glassSecondaryText)
                            }
                        }
                        .padding()
                    }
                    .transition(.asymmetric(
                        insertion: .scale.combined(with: .opacity),
                        removal: .scale.combined(with: .opacity)
                    ))
                }
                
                Spacer()
            }
            .padding()
            
            Spacer()
            
            // Coaching Feedback
            if isCoachingEnabled, let currentFeedback = playerViewModel.currentFeedback {
                HStack {
                    Spacer()
                    
                    LiquidGlassCard {
                        HStack(spacing: 12) {
                            Image(systemName: "person.fill.questionmark")
                                .font(.title3)
                                .symbolRenderingMode(.hierarchical)
                                .foregroundStyle(.tint)
                            
                            Text(currentFeedback)
                                .font(.subheadline)
                                .foregroundColor(.glassText)
                                .lineLimit(3)
                                .frame(maxWidth: 300)
                        }
                        .padding()
                    }
                    .transition(.asymmetric(
                        insertion: .move(edge: .trailing).combined(with: .opacity),
                        removal: .move(edge: .trailing).combined(with: .opacity)
                    ))
                }
                .padding()
            }
        }
    }
    
    private var customControlsView: some View {
        VStack(spacing: 20) {
            // Time Slider
            VStack(spacing: 8) {
                Slider(
                    value: $playerViewModel.currentTime,
                    in: 0...playerViewModel.duration,
                    onEditingChanged: { editing in
                        if editing {
                            playerViewModel.isSeeking = true
                        } else {
                            playerViewModel.seek(to: playerViewModel.currentTime)
                            playerViewModel.isSeeking = false
                        }
                        resetHideControlsTimer()
                    }
                )
                .tint(.fairwayGreen)
                
                HStack {
                    Text(formatTime(playerViewModel.currentTime))
                        .font(.caption)
                        .foregroundColor(.glassSecondaryText)
                    
                    Spacer()
                    
                    Text(formatTime(playerViewModel.duration))
                        .font(.caption)
                        .foregroundColor(.glassSecondaryText)
                }
            }
            
            // Playback Controls
            HStack(spacing: 40) {
                // Previous Phase
                Button(action: {
                    playerViewModel.previousPhase()
                    HapticManager.impact(.light)
                    resetHideControlsTimer()
                }) {
                    Image(systemName: "backward.end.fill")
                        .font(.title2)
                        .symbolRenderingMode(.hierarchical)
                }
                .disabled(playerViewModel.currentPhaseIndex == 0)
                
                // Play/Pause
                Button(action: {
                    playerViewModel.togglePlayPause()
                    HapticManager.impact(.medium)
                    resetHideControlsTimer()
                }) {
                    Image(systemName: playerViewModel.isPlaying ? "pause.fill" : "play.fill")
                        .font(.largeTitle)
                        .symbolRenderingMode(.hierarchical)
                }
                
                // Next Phase
                Button(action: {
                    playerViewModel.nextPhase()
                    HapticManager.impact(.light)
                    resetHideControlsTimer()
                }) {
                    Image(systemName: "forward.end.fill")
                        .font(.title2)
                        .symbolRenderingMode(.hierarchical)
                }
                .disabled(playerViewModel.currentPhaseIndex >= analysisResult.swingPhases.count - 1)
            }
            .foregroundColor(.glassText)
            
            // Phase Quick Jump
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(Array(analysisResult.swingPhases.enumerated()), id: \.offset) { index, phase in
                        Button(action: {
                            playerViewModel.jumpToPhase(index)
                            HapticManager.impact(.light)
                            resetHideControlsTimer()
                        }) {
                            VStack(spacing: 4) {
                                Image(systemName: phaseIcon(for: phase.name))
                                    .font(.title3)
                                Text(phase.name)
                                    .font(.caption2)
                            }
                            .foregroundColor(playerViewModel.currentPhaseIndex == index ? .white : .glassText)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background {
                                if playerViewModel.currentPhaseIndex == index {
                                    Capsule()
                                        .fill(Color.golfGreen)
                                } else {
                                    Capsule()
                                        .fill(Material.ultraThin)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
    
    private func setPlaybackSpeed(_ speed: Float) {
        playbackSpeed = speed
        playerViewModel.setPlaybackSpeed(speed)
        resetHideControlsTimer()
    }
    
    private func resetHideControlsTimer() {
        hideControlsTimer?.invalidate()
        hideControlsTimer = Timer.scheduledTimer(withTimeInterval: 3.0, repeats: false) { _ in
            withAnimation {
                showControls = false
            }
        }
    }
    
    private func formatTime(_ time: Double) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private func phaseIcon(for phaseName: String) -> String {
        switch phaseName.lowercased() {
        case let name where name.contains("setup"): return "figure.stand"
        case let name where name.contains("backswing"): return "arrow.turn.up.left"
        case let name where name.contains("downswing"): return "arrow.turn.down.right"
        case let name where name.contains("impact"): return "bolt.fill"
        case let name where name.contains("follow"): return "arrow.up.right"
        default: return "figure.golf"
        }
    }
}

// MARK: - Video Player View Model

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
        
        // Configure voice
        if let voice = AVSpeechSynthesisVoice(language: "en-US") {
            // Use a specific voice if available
            synthesizer.stopSpeaking(at: .immediate)
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
        utterance.rate = 0.5
        utterance.pitchMultiplier = 1.0
        utterance.volume = 0.9
        
        // Use a preferred voice
        if let voice = AVSpeechSynthesisVoice(language: "en-US") {
            utterance.voice = voice
        }
        
        synthesizer.speak(utterance)
    }
    
    @objc private func playerDidFinishPlaying() {
        isPlaying = false
        seek(to: 0)
    }
}

// MARK: - Preview

#Preview {
    NavigationStack {
        VideoPlayerWithCoaching(
            analysisResult: AnalysisResult(
                id: "123",
                status: "completed",
                swingPhases: [
                    SwingPhase(
                        name: "Setup",
                        timestamp: 0.0,
                        description: "Initial stance",
                        feedback: "Great stance, keep your shoulders relaxed"
                    ),
                    SwingPhase(
                        name: "Backswing",
                        timestamp: 1.5,
                        description: "Club to top",
                        feedback: "Excellent rotation, maintain this position"
                    ),
                    SwingPhase(
                        name: "Downswing",
                        timestamp: 3.0,
                        description: "Transition",
                        feedback: "Good hip movement, focus on your tempo"
                    ),
                    SwingPhase(
                        name: "Impact",
                        timestamp: 3.8,
                        description: "Ball contact",
                        feedback: "Solid contact, well done"
                    ),
                    SwingPhase(
                        name: "Follow Through",
                        timestamp: 4.5,
                        description: "Finish position",
                        feedback: "Complete your rotation for better balance"
                    )
                ],
                keyPoints: ["Great tempo"],
                overallAnalysis: "Good swing",
                coachingScript: "Keep practicing",
                swingSpeed: 90,
                tempo: "3:1",
                balance: 85
            ),
            videoURL: URL(fileURLWithPath: "/path/to/video.mp4")
        )
    }
}