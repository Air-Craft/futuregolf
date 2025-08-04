import SwiftUI
import AVKit
import Factory

struct HomeView: View {
    @InjectedObservable(\.appState) private var appState: AppState
    @State private var viewModel: VideoAnalysisViewModel
    
    init() {
        _viewModel = State(initialValue: Container.shared.videoAnalysisViewModel())
    }
    
    @State private var player: AVPlayer?
    
    var body: some View {
        ZStack {
            // Full-screen background video player that goes UNDER status bar
            if let player = player {
                FullScreenVideoPlayer(player: player)
                    .ignoresSafeArea(.all)
                    .onAppear {
                        player.play()
                    }
            }
            
            // Main content overlay
            VStack(spacing: 0) {
                // Top spacer to push content down from status bar
                Spacer(minLength: 60)
                
                // Title Section
                titleSection
                    .padding(.horizontal, 24)
                
                Spacer()
                
                // Four pill buttons
                buttonSection
                    .padding(.horizontal, 24)
                
                // Bottom spacer for safe area
                Spacer(minLength: 80)
                
                // Debug button (shown when enabled in Config)
                if Config.isDebugPanelEnabled {
                    HStack {
                        Spacer()
                        Button(action: {
                            // showDebugPanel = true
                        }) {
                            Image(systemName: "ladybug.fill")
                                .font(.title2)
                                .foregroundColor(.white)
                                .padding(12)
                                .background(Color.red.opacity(0.8))
                                .clipShape(Circle())
                        }
                        .padding()
                    }
                }
            }
        }
        .ignoresSafeArea(.all)
        .onAppear {
            setupBackgroundVideo()
        }
    }
    
    // MARK: - Title Section
    private var titleSection: some View {
        VStack(spacing: 8) {
            // Main fancy script title
            Text("Golf Swing\nAnalyzer")
                .font(.custom("Snell Roundhand", size: 72))
                .kerning(0.0)
                .foregroundStyle(
                    LinearGradient(
                        colors: [.white, .white.opacity(0.8)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .shadow(color: .black.opacity(0.5), radius: 8, x: 0, y: 2)
//                .liquidGlassBackground(
//                    intensity: .light,
//                    cornerRadius: 20,
//                    specularHighlight: true
//                )
                .padding(.horizontal, 6)
                .padding(.top, 12)
            
            // Subtitle
            Text("Powered by Edge AI")
                .font(.system(size: 14, weight: .medium, design: .monospaced))
                .foregroundColor(.white.opacity(0.9))
                .tracking(1.5)
                .textCase(.uppercase)
//                .liquidGlassBackground(
//                    intensity: .ultraLight,
//                    cornerRadius: 12,
//                    specularHighlight: false
//                )
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
        }
    }
    
    // MARK: - Button Section
    private var buttonSection: some View {
        VStack(spacing: 16) {
            // Button 1: Analyze My Swing (Camera)
            Button(action: {
                appState.navigateTo(.recording)
                LiquidGlassHaptics.impact(.medium)
            }) {
                HStack {
                    Image(systemName: "camera.fill")
                        .font(.title2)
                    Text("Analyze My Swing")
                        .font(.title3)
                        .fontWeight(.semibold)
                    Spacer()
                }
                .foregroundColor(.black)
                .padding(.horizontal, 24)
                .padding(.vertical, 16)
            }
            .buttonStyle(LiquidGlassPillButtonStyle())
            
            // Button 2: Upload Swing Video
            Button(action: {
                LiquidGlassHaptics.impact(.medium)
            }) {
                HStack {
                    Image(systemName: "square.and.arrow.up.fill")
                        .font(.title2)
                    Text("Upload Swing Video")
                        .font(.title3)
                        .fontWeight(.semibold)
                    Spacer()
                }
                .foregroundColor(.black)
                .padding(.horizontal, 24)
                .padding(.vertical, 16)
            }
            .buttonStyle(LiquidGlassPillButtonStyle())
            
            // Button 3: Previous Swing Analyses (using Button instead of NavigationLink to avoid styling issues)
            Button(action: {
                // Navigate programmatically instead of using NavigationLink
                // showPreviousAnalyses = true
                appState.navigateTo(.previousAnalyses)
                LiquidGlassHaptics.impact(.medium)
            }) {
                HStack {
                    Image(systemName: "clock.arrow.circlepath")
                        .font(.title2)
                    Text("Previous Swing Analyses")
                        .font(.title3)
                        .fontWeight(.semibold)
                    Spacer()
                }
                .foregroundColor(.black)
                .padding(.horizontal, 24)
                .padding(.vertical, 16)
            }
            .buttonStyle(LiquidGlassPillButtonStyle())
            
            // Button 4: TMP Video Analysis Demo
            Button(action: {
                // showCoachingVideo = true
                LiquidGlassHaptics.impact(.medium)
            }) {
                HStack {
                    Image(systemName: "play.tv.fill")
                        .font(.title2)
                    Text("TMP Video Analysis Demo")
                        .font(.title3)
                        .fontWeight(.semibold)
                    Spacer()
                }
                .foregroundColor(.black)
                .padding(.horizontal, 24)
                .padding(.vertical, 16)
            }
            .buttonStyle(LiquidGlassPillButtonStyle())
        }
    }
    
    private func setupBackgroundVideo() {
        guard let path = Bundle.main.path(forResource: "home_bg_video", ofType: "mp4") else {
            print("Video file not found in bundle")
            return
        }
        
        let url = URL(fileURLWithPath: path)
        let playerItem = AVPlayerItem(url: url)
        
        let newPlayer = AVPlayer(playerItem: playerItem)
        newPlayer.isMuted = true
        
        NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime,
            object: playerItem,
            queue: .main
        ) { _ in
            newPlayer.seek(to: .zero)
            newPlayer.play()
        }
        
        self.player = newPlayer
    }
    
    private func createDemoAnalysisResult() -> AnalysisResult {
        return AnalysisResult(
            id: "demo-123",
            status: "completed",
            swingPhases: [
                SwingPhase(
                    name: "Setup",
                    timestamp: 0.0,
                    description: "Initial stance and club positioning",
                    feedback: "Great posture! Keep your shoulders relaxed and maintain this spine angle throughout the swing."
                ),
                SwingPhase(
                    name: "Backswing",
                    timestamp: 0.8,
                    description: "Club movement to the top of the swing",
                    feedback: "Excellent shoulder rotation. Try to keep your left arm a bit straighter for more power."
                ),
                SwingPhase(
                    name: "Downswing",
                    timestamp: 2.1,
                    description: "Transition and acceleration through impact",
                    feedback: "Good hip rotation! Focus on maintaining lag for increased club head speed."
                ),
                SwingPhase(
                    name: "Impact",
                    timestamp: 2.8,
                    description: "Ball contact moment",
                    feedback: "Solid contact! Your hands are in a great position at impact."
                ),
                SwingPhase(
                    name: "Follow Through",
                    timestamp: 3.2,
                    description: "Post-impact club path and finish position",
                    feedback: "Complete your rotation and hold the finish for better balance and consistency."
                )
            ],
            keyPoints: [
                "Excellent tempo throughout the swing",
                "Good weight transfer from back to front foot",
                "Strong grip and hand position",
                "Room to improve shoulder turn in backswing"
            ],
            overallAnalysis: "Your swing demonstrates solid fundamentals with good tempo and balance. The main areas for improvement are maintaining a straighter left arm in the backswing and completing your follow-through for better consistency.",
            coachingScript: "Focus on these key points: 1) Keep your left arm extended during the backswing, 2) Maintain the lag angle longer in the downswing, 3) Complete your rotation and hold your finish position for 2 seconds.",
            swingSpeed: 92,
            tempo: "3:1",
            balance: 87
        )
    }
}

// MARK: - Custom Liquid Glass Pill Button Style
struct LiquidGlassPillButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .frame(maxWidth: .infinity, alignment: .leading)
            .background {
                Capsule()
                    .fill(Material.ultraThinMaterial)
                    .overlay {
                        Capsule()
                            .fill(Color.white.opacity(0.12))
                    }
                    .overlay {
                        // Specular highlight effect
                        GeometryReader { geometry in
                            LinearGradient(
                                gradient: Gradient(stops: [
                                    .init(color: .clear, location: 0),
                                    .init(color: Color.white.opacity(0.2), location: 0.3),
                                    .init(color: Color.white.opacity(0.08), location: 0.7),
                                    .init(color: .clear, location: 1)
                                ]),
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                            .clipShape(Capsule())
                        }
                    }
                    .overlay {
                        Capsule()
                            .stroke(Color.white.opacity(0.25), lineWidth: 1.5)
                    }
                    .shadow(color: Color.black.opacity(0.1), radius: 6, x: 0, y: 3)
            }
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .opacity(configuration.isPressed ? 0.85 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.6), value: configuration.isPressed)
    }
}

// MARK: - Full Screen Video Player

struct FullScreenVideoPlayer: UIViewRepresentable {
    let player: AVPlayer
    
    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        view.backgroundColor = .black
        
        let playerLayer = AVPlayerLayer(player: player)
        playerLayer.videoGravity = .resizeAspectFill // This ensures it fills the entire screen
        playerLayer.frame = UIScreen.main.bounds // Use full screen bounds
        
        view.layer.addSublayer(playerLayer)
        
        // Set up observer to update frame on bounds change
        context.coordinator.playerLayer = playerLayer
        
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {
        // Update the player layer frame to match the full screen
        context.coordinator.playerLayer?.frame = UIScreen.main.bounds
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator {
        var playerLayer: AVPlayerLayer?
    }
}

// Placeholder for Tutorial View
struct TutorialView: View {
    var body: some View {
        Text("Tutorial Coming Soon")
            .navigationTitle("Tutorial")
    }
}

#Preview {
    HomeView()
}
