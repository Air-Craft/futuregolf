import SwiftUI
import AVKit
import AVFoundation

struct CoachingVideoView: View {
    @State private var player: AVPlayer?
    @State private var playerItem: AVPlayerItem?
    @State private var isPlaying = false
    @State private var currentTime: Double = 0
    @State private var duration: Double = 0
    @State private var playbackSpeed: Float = 0.25
    @State private var showTextTips = true
    @State private var ttsEnabled = true
    @State private var coachAudioMuted = false
    @State private var currentSwing = 0
    @State private var currentScore: Double = 0.0
    @State private var clubheadSpeed = "100mph"
    @State private var activeTextTips: [String] = []
    @State private var timeObserver: Any?
    @StateObject private var ttsService = TTSService.shared
    @State private var currentTTSIndex = 0
    @State private var analysisData: VideoCoachingAnalysisData?
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color.black.ignoresSafeArea()
                
                // Full-screen video player
                if let player = player {
                    VideoPlayerView(player: player)
                        .ignoresSafeArea()
                }
                
                // Overlay controls with Liquid Glass styling
                VStack {
                    // Top overlay with stats
                    HStack {
                        overlayViews
                        Spacer()
                    }
                    .padding(.top, 50)
                    .padding(.horizontal, 20)
                    
                    Spacer()
                    
                    // Bottom controls with translucent black background
                    videoControls
                        .background(
                            Color.black.opacity(0.7),
                            in: RoundedRectangle(cornerRadius: 20)
                        )
                        .padding(.horizontal, 20)
                        .padding(.bottom, 40)
                }
            }
        }
        .navigationBarHidden(true)
        .onAppear {
            setupVideo()
            loadAnalysisData()
        }
        .onDisappear {
            cleanupPlayer()
        }
    }
    
    private var overlayViews: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                // Swing counter with glass morphism
                Text("Swing: \(currentSwing)")
                    .font(.headline.weight(.semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(.ultraThinMaterial, in: Capsule())
                    .overlay(Capsule().stroke(.white.opacity(0.2), lineWidth: 1))
                
                // Score with glass morphism  
                Text("Score: \(String(format: "%.1f", currentScore))")
                    .font(.headline.weight(.semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(.ultraThinMaterial, in: Capsule())
                    .overlay(Capsule().stroke(.white.opacity(0.2), lineWidth: 1))
            }
            
            // Clubhead speed with glass morphism
            Text("Clubhead: \(clubheadSpeed)")
                .font(.subheadline.weight(.medium))
                .foregroundColor(.white)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(.thinMaterial, in: Capsule())
                .overlay(Capsule().stroke(.white.opacity(0.15), lineWidth: 1))
            
            // Text tips with enhanced glass styling
            if showTextTips && !activeTextTips.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(activeTextTips, id: \.self) { tip in
                        Text(tip)
                            .font(.caption.weight(.medium))
                            .foregroundColor(.white)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(.blue.opacity(0.3), lineWidth: 1))
                    }
                }
            }
        }
    }
    
    private var videoControls: some View {
        VStack(spacing: 16) {
            // Time scrubber with glass styling
            VStack(spacing: 8) {
                Slider(value: $currentTime, in: 0...duration) { editing in
                    if !editing {
                        seekToTime(currentTime)
                    }
                }
                .tint(.white)
                
                HStack {
                    Text(formatTime(currentTime))
                        .font(.caption.weight(.medium))
                        .foregroundColor(.white.opacity(0.8))
                    
                    Spacer()
                    
                    Text(formatTime(duration))
                        .font(.caption.weight(.medium))
                        .foregroundColor(.white.opacity(0.8))
                }
            }
            .padding(.horizontal, 20)
            
            // Main controls with glass morphism
            HStack(spacing: 24) {
                // Skip back 5s
                Button(action: skipBackward) {
                    Image(systemName: "gobackward.5")
                        .font(.title2.weight(.semibold))
                        .foregroundColor(.white)
                        .frame(width: 44, height: 44)
                        .background(Color.black.opacity(0.5), in: Circle())
                        .overlay(Circle().stroke(.white.opacity(0.3), lineWidth: 1))
                }
                
                // Play/Pause with larger glass button
                Button(action: togglePlayPause) {
                    Image(systemName: isPlaying ? "pause.fill" : "play.fill")
                        .font(.title.weight(.bold))
                        .foregroundColor(.white)
                        .frame(width: 56, height: 56)
                        .background(Color.black.opacity(0.6), in: Circle())
                        .overlay(Circle().stroke(.white.opacity(0.4), lineWidth: 2))
                }
                
                // Skip forward 5s
                Button(action: skipForward) {
                    Image(systemName: "goforward.5")
                        .font(.title2.weight(.semibold))
                        .foregroundColor(.white)
                        .frame(width: 44, height: 44)
                        .background(Color.black.opacity(0.5), in: Circle())
                        .overlay(Circle().stroke(.white.opacity(0.3), lineWidth: 1))
                }
                
                Spacer()
                
                // Playback speed with translucent black styling
                Button(action: cyclePlaybackSpeed) {
                    Text("\(String(format: "%.2f", playbackSpeed))x")
                        .font(.caption.weight(.semibold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.black.opacity(0.5), in: Capsule())
                        .overlay(Capsule().stroke(.white.opacity(0.3), lineWidth: 1))
                }
            }
            .padding(.horizontal, 20)
            
            // Secondary controls with enhanced glass styling
            HStack(spacing: 16) {
                // TTS toggle
                Button(action: { ttsEnabled.toggle() }) {
                    HStack(spacing: 6) {
                        if ttsService.isLoading {
                            ProgressView()
                                .scaleEffect(0.8)
                                .tint(.white)
                        } else {
                            Image(systemName: ttsEnabled ? (ttsService.isPlaying ? "speaker.wave.3.fill" : "speaker.wave.2.fill") : "speaker.slash.fill")
                                .font(.caption.weight(.semibold))
                        }
                        Text("AI TTS")
                            .font(.caption.weight(.medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.black.opacity(ttsEnabled ? 0.6 : 0.4), in: Capsule())
                    .overlay(Capsule().stroke(.white.opacity(ttsEnabled ? 0.4 : 0.2), lineWidth: 1))
                }
                
                // Coach audio mute
                Button(action: { coachAudioMuted.toggle() }) {
                    HStack(spacing: 6) {
                        Image(systemName: coachAudioMuted ? "speaker.slash" : "speaker.wave.1")
                            .font(.caption.weight(.semibold))
                        Text("Coach")
                            .font(.caption.weight(.medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.black.opacity(coachAudioMuted ? 0.4 : 0.6), in: Capsule())
                    .overlay(Capsule().stroke(.white.opacity(coachAudioMuted ? 0.2 : 0.4), lineWidth: 1))
                }
                
                // Text tips toggle
                Button(action: { showTextTips.toggle() }) {
                    HStack(spacing: 6) {
                        Image(systemName: showTextTips ? "text.bubble.fill" : "text.bubble")
                            .font(.caption.weight(.semibold))
                        Text("Tips")
                            .font(.caption.weight(.medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.black.opacity(showTextTips ? 0.6 : 0.4), in: Capsule())
                    .overlay(Capsule().stroke(.white.opacity(showTextTips ? 0.4 : 0.2), lineWidth: 1))
                }
                
                Spacer()
            }
            .padding(.horizontal, 20)
        }
        .padding(.vertical, 20)
    }
    
    private func setupVideo() {
        guard let path = Bundle.main.path(forResource: "test_video", ofType: "mov") else {
            print("Video file not found in bundle")
            return
        }
        
        let url = URL(fileURLWithPath: path)
        playerItem = AVPlayerItem(url: url)
        player = AVPlayer(playerItem: playerItem)
        
        // Mute video audio to avoid conflict with TTS
        player?.isMuted = true
        
        // Add time observer
        let interval = CMTime(seconds: 0.1, preferredTimescale: 600)
        timeObserver = player?.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [self] time in
            currentTime = time.seconds
            // Update playing state based on actual player rate
            isPlaying = (player?.rate ?? 0) > 0
            updateOverlays()
            checkForTTSEvents()
        }
        
        // Handle playback end
        NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime,
            object: playerItem,
            queue: .main
        ) { _ in
            isPlaying = false
        }
        
        // Update duration when ready and auto-play
        playerItem?.publisher(for: \.status)
            .sink { status in
                if status == .readyToPlay {
                    if let duration = playerItem?.duration {
                        self.duration = duration.seconds
                    }
                    // Auto-play at the configured speed
                    self.player?.rate = self.playbackSpeed
                }
            }
            .store(in: &cancellables)
    }
    
    @State private var cancellables = Set<AnyCancellable>()
    
    private func loadAnalysisData() {
        // Use the exact JSON structure provided
        let mockData = VideoCoachingAnalysisData(
            swings: [
                VideoSwingData(
                    score: 5,
                    phases: VideoSwingPhases(
                        setup: VideoPhaseData(startFrame: 90, endFrame: 150),
                        backswing: VideoPhaseData(startFrame: 150, endFrame: 180),
                        downswing: VideoPhaseData(startFrame: 180, endFrame: 210),
                        followThrough: VideoPhaseData(startFrame: 210, endFrame: 240)
                    ),
                    comments: [
                        "Maintain a stable head position throughout the swing.",
                        "Focus on a fuller rotation in the follow-through."
                    ]
                ),
                VideoSwingData(
                    score: 5,
                    phases: VideoSwingPhases(
                        setup: VideoPhaseData(startFrame: 300, endFrame: 390),
                        backswing: VideoPhaseData(startFrame: 390, endFrame: 420),
                        downswing: VideoPhaseData(startFrame: 420, endFrame: 450),
                        followThrough: VideoPhaseData(startFrame: 450, endFrame: 480)
                    ),
                    comments: [
                        "Reduce lateral sway in the backswing.",
                        "Aim for a more complete hip and chest rotation in the finish."
                    ]
                ),
                VideoSwingData(
                    score: 6,
                    phases: VideoSwingPhases(
                        setup: VideoPhaseData(startFrame: 540, endFrame: 600),
                        backswing: VideoPhaseData(startFrame: 600, endFrame: 630),
                        downswing: VideoPhaseData(startFrame: 630, endFrame: 660),
                        followThrough: VideoPhaseData(startFrame: 660, endFrame: 690)
                    ),
                    comments: [
                        "Keep your left arm straighter through impact.",
                        "Let your hips lead the downswing more actively."
                    ]
                )
            ],
            summary: VideoSummaryData(
                highlights: [
                    "Good club head speed demonstrated.",
                    "Consistent tempo, especially on the last swing.",
                    "Solid contact achieved on the final swing."
                ],
                improvements: [
                    "Improve lower body stability during the backswing to minimize sway.",
                    "Increase body rotation through impact to enhance power and consistency.",
                    "Work on maintaining a straighter lead arm through the impact zone."
                ]
            ),
            coachingScript: VideoCoachingScriptData(
                lines: [
                    VideoCoachingLine(text: "Alright, let's take a look at your golf swing.", startFrameNumber: 0),
                    VideoCoachingLine(text: "Starting with your setup, try to maintain a consistent spine angle.", startFrameNumber: 60),
                    VideoCoachingLine(text: "In your backswing, aim for a more stable lower body to avoid any lateral sway.", startFrameNumber: 150),
                    VideoCoachingLine(text: "Through impact, focus on rotating your hips and chest fully towards the target.", startFrameNumber: 210),
                    VideoCoachingLine(text: "Let's review the second swing.", startFrameNumber: 300),
                    VideoCoachingLine(text: "Notice how a slight sway in the backswing can affect your balance.", startFrameNumber: 360),
                    VideoCoachingLine(text: "Work on extending your lead arm more fully through the ball.", startFrameNumber: 450),
                    VideoCoachingLine(text: "Now for your third swing, which looked much better.", startFrameNumber: 540),
                    VideoCoachingLine(text: "That's a stronger backswing position, good coil.", startFrameNumber: 600),
                    VideoCoachingLine(text: "Excellent contact! See how your body rotated better here, leading to a straighter shot.", startFrameNumber: 660),
                    VideoCoachingLine(text: "Overall, you have good clubhead speed and a solid tempo, especially on that last swing.", startFrameNumber: 720),
                    VideoCoachingLine(text: "To improve further, focus on minimizing lower body sway in the backswing.", startFrameNumber: 780),
                    VideoCoachingLine(text: "Also, emphasize a more active hip and chest rotation through impact to maximize power and consistency.", startFrameNumber: 840),
                    VideoCoachingLine(text: "Keep up the great work!", startFrameNumber: 900)
                ]
            )
        )
        
        analysisData = mockData
    }
    
    private func updateOverlays() {
        guard let data = analysisData else { return }
        
        // Frame numbers in JSON are based on normal playback at 30 FPS
        // Current time is the actual video time, so we calculate frame directly
        let currentFrame = Int(currentTime * 30) // Direct frame calculation from current video time
        
        // Update swing counter and score
        for (index, swing) in data.swings.enumerated() {
            if currentFrame >= swing.phases.downswing.startFrame && currentFrame <= swing.phases.downswing.endFrame {
                currentSwing = index + 1
                currentScore = Double(swing.score)
                break
            }
        }
        
        // Update text tips
        if showTextTips {
            var tips: [String] = []
            for swing in data.swings {
                if currentFrame >= swing.phases.setup.startFrame && currentFrame <= swing.phases.followThrough.endFrame {
                    tips.append(contentsOf: swing.comments)
                }
            }
            activeTextTips = tips
        }
    }
    
    private func checkForTTSEvents() {
        guard ttsEnabled, let data = analysisData else { return }
        
        // Frame numbers in JSON are based on normal playback at 30 FPS
        // Current time is the actual video time, so we calculate frame directly
        let currentFrame = Int(currentTime * 30) // Direct frame calculation from current video time
        
        // Only speak if not already speaking and there's a next line to speak
        if currentTTSIndex < data.coachingScript.lines.count && !ttsService.isSpeaking {
            let line = data.coachingScript.lines[currentTTSIndex]
            if currentFrame >= line.startFrameNumber {
                speakText(line.text)
                currentTTSIndex += 1
            }
        }
    }
    
    private func speakText(_ text: String) {
        guard !coachAudioMuted else { return }
        
        ttsService.speakText(text) { success in
            if !success {
                print("Failed to speak text: \(text)")
            }
        }
    }
    
    private func togglePlayPause() {
        if isPlaying {
            player?.pause()
        } else {
            player?.rate = playbackSpeed
        }
        // isPlaying will be updated automatically by the time observer
    }
    
    private func skipBackward() {
        let newTime = max(0, currentTime - 5)
        seekToTime(newTime)
    }
    
    private func skipForward() {
        let newTime = min(duration, currentTime + 5)
        seekToTime(newTime)
    }
    
    private func seekToTime(_ time: Double) {
        let cmTime = CMTime(seconds: time, preferredTimescale: 600)
        player?.seek(to: cmTime)
        
        // Find next TTS entry after seek - don't interrupt current TTS
        guard let data = analysisData else { return }
        // Frame numbers in JSON are based on normal playback at 30 FPS
        // Time is the actual video time, so we calculate frame directly
        let currentFrame = Int(time * 30)
        
        // Find the appropriate TTS index for the new position
        var newTTSIndex = data.coachingScript.lines.count // Default to end
        for (index, line) in data.coachingScript.lines.enumerated() {
            if line.startFrameNumber > currentFrame {
                newTTSIndex = index
                break
            }
        }
        
        // Only update TTS index if we're not currently speaking
        // This allows current TTS to complete naturally
        if !ttsService.isSpeaking {
            currentTTSIndex = newTTSIndex
        }
    }
    
    private func cyclePlaybackSpeed() {
        switch playbackSpeed {
        case 0.25:
            playbackSpeed = 0.5
        case 0.5:
            playbackSpeed = 1.0
        case 1.0:
            playbackSpeed = 0.25
        default:
            playbackSpeed = 0.25
        }
        
        // Apply new speed immediately if playing
        if isPlaying {
            player?.rate = playbackSpeed
        }
    }
    
    private func formatTime(_ time: Double) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        let frames = Int((time - Double(Int(time))) * 30)
        return String(format: "%02d:%02d.%02d", minutes, seconds, frames)
    }
    
    private func cleanupPlayer() {
        if let timeObserver = timeObserver {
            player?.removeTimeObserver(timeObserver)
        }
        player?.pause()
        ttsService.stopSpeaking()
    }
}

struct VideoPlayerView: UIViewRepresentable {
    let player: AVPlayer
    
    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        let playerLayer = AVPlayerLayer(player: player)
        playerLayer.videoGravity = .resizeAspect
        view.layer.addSublayer(playerLayer)
        
        DispatchQueue.main.async {
            playerLayer.frame = view.bounds
        }
        
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {
        if let playerLayer = uiView.layer.sublayers?.first as? AVPlayerLayer {
            playerLayer.frame = uiView.bounds
        }
    }
}

// Data models for coaching analysis
struct VideoCoachingAnalysisData: Codable {
    let swings: [VideoSwingData]
    let summary: VideoSummaryData
    let coachingScript: VideoCoachingScriptData
}

struct VideoSwingData: Codable {
    let score: Int
    let phases: VideoSwingPhases
    let comments: [String]
}

struct VideoSwingPhases: Codable {
    let setup: VideoPhaseData
    let backswing: VideoPhaseData
    let downswing: VideoPhaseData
    let followThrough: VideoPhaseData
    
    enum CodingKeys: String, CodingKey {
        case setup, backswing, downswing
        case followThrough = "follow_through"
    }
}

struct VideoPhaseData: Codable {
    let startFrame: Int
    let endFrame: Int
    
    enum CodingKeys: String, CodingKey {
        case startFrame = "start_frame"
        case endFrame = "end_frame"
    }
}

struct VideoSummaryData: Codable {
    let highlights: [String]
    let improvements: [String]
}

struct VideoCoachingScriptData: Codable {
    let lines: [VideoCoachingLine]
}

struct VideoCoachingLine: Codable {
    let text: String
    let startFrameNumber: Int
    
    enum CodingKeys: String, CodingKey {
        case text
        case startFrameNumber = "start_frame_number"
    }
}

import Combine

#Preview {
    CoachingVideoView()
}