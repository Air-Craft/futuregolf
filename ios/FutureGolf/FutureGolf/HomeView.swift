import SwiftUI
import AVKit

struct HomeView: View {
    @State private var animateContent = false
    @State private var showUploadFlow = false
    @State private var selectedVideoURL: URL?
    @State private var showAnalysisView = false
    @State private var showDemoVideo = false
    @State private var showCoachingVideo = false
    @State private var viewModel = VideoAnalysisViewModel()
    @State private var player: AVPlayer?
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background video player
                if let player = player {
                    VideoPlayer(player: player)
                        .disabled(true) // Disable user interaction
                        .ignoresSafeArea()
                        .opacity(0.3) // Make it subtle
                        .blur(radius: 1) // Slight blur for background effect
                        .onAppear {
                            player.play()
                        }
                }
                
                ScrollView {
                    VStack(spacing: 24) {
                    // Welcome Section
                    welcomeSection
                        .opacity(animateContent ? 1 : 0)
                        .offset(y: animateContent ? 0 : 20)
                        .animation(.spring(response: 0.6, dampingFraction: 0.8), value: animateContent)
                    
                    // Quick Actions
                    quickActionsSection
                        .opacity(animateContent ? 1 : 0)
                        .offset(y: animateContent ? 0 : 30)
                        .animation(.spring(response: 0.7, dampingFraction: 0.8).delay(0.1), value: animateContent)
                    
                    // Recent Analysis Preview
                    if false { // Temporarily hidden to make space
                        recentAnalysisSection
                            .opacity(animateContent ? 1 : 0)
                            .offset(y: animateContent ? 0 : 40)
                            .animation(.spring(response: 0.8, dampingFraction: 0.8).delay(0.2), value: animateContent)
                    }
                    }
                    .padding()
                }
            }
            .navigationTitle("FutureGolf")
            .navigationBarTitleDisplayMode(.large)
            .sheet(isPresented: $showUploadFlow) {
                UploadVideoJourneyView(viewModel: viewModel)
            }
            .sheet(isPresented: $showAnalysisView) {
                if let result = viewModel.analysisResult {
                    NavigationStack {
                        AnalysisResultView(result: result)
                            .navigationBarTitleDisplayMode(.inline)
                            .toolbar {
                                ToolbarItem(placement: .navigationBarTrailing) {
                                    Button("Done") {
                                        showAnalysisView = false
                                    }
                                }
                            }
                    }
                }
            }
            .onChange(of: viewModel.analysisResult) { _, newResult in
                if newResult != nil {
                    showAnalysisView = true
                }
            }
            .onAppear {
                withAnimation {
                    animateContent = true
                }
                setupBackgroundVideo()
            }
            .sheet(isPresented: $showDemoVideo) {
                NavigationStack {
                    // Create demo analysis result
                    let demoResult = createDemoAnalysisResult()
                    let videoPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!.appendingPathComponent("golf1.mp4")
                    
                    VideoPlayerWithCoaching(
                        analysisResult: demoResult,
                        videoURL: videoPath
                    )
                    .navigationBarTitleDisplayMode(.inline)
                    .navigationTitle("Demo Analysis")
                    .toolbar {
                        ToolbarItem(placement: .navigationBarLeading) {
                            Button("Done") {
                                showDemoVideo = false
                            }
                        }
                    }
                }
            }
            .sheet(isPresented: $showCoachingVideo) {
                NavigationStack {
                    CoachingVideoView()
                        .navigationBarTitleDisplayMode(.inline)
                        .toolbar {
                            ToolbarItem(placement: .navigationBarLeading) {
                                Button("Done") {
                                    showCoachingVideo = false
                                }
                            }
                        }
                }
            }
        }
    }
    
    private func setupBackgroundVideo() {
        guard let path = Bundle.main.path(forResource: "golf1", ofType: "mp4") else {
            print("Video file not found in bundle")
            return
        }
        
        let url = URL(fileURLWithPath: path)
        let playerItem = AVPlayerItem(url: url)
        
        // Create player
        let newPlayer = AVPlayer(playerItem: playerItem)
        newPlayer.isMuted = true // Mute background video
        
        // Loop the video
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
    
    private var welcomeSection: some View {
        VStack(alignment: .center, spacing: 20) {
            // Main App Title with fancy styling and translucent background
            VStack(spacing: 12) {
                Text("Golf Swing Analyzer")
                    .font(.system(size: 28, weight: .black, design: .rounded))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.blue, .cyan, .green],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .shadow(color: .black.opacity(0.5), radius: 3, x: 0, y: 2)
                
                Text("Powered by Edge AI")
                    .font(.system(size: 16, weight: .semibold, design: .rounded))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.orange, .red],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .tracking(1.2)
            }
            .padding(.vertical, 20)
            .padding(.horizontal, 24)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(.white.opacity(0.2), lineWidth: 1)
            )
            
            // Greeting text with translucent background
            VStack(spacing: 6) {
                Text(greetingText)
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                
                Text("Ready to perfect your swing?")
                    .font(.subheadline)
                    .foregroundColor(.white.opacity(0.8))
            }
            .padding(.vertical, 16)
            .padding(.horizontal, 20)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(.white.opacity(0.2), lineWidth: 1)
            )
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, 20)
    }
    
    private var quickActionsSection: some View {
        VStack(spacing: 16) {
            // Primary Action - New Analysis
            Button(action: {
                showUploadFlow = true
                HapticManager.impact(.medium)
            }) {
                HStack {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("New Analysis", systemImage: "camera.viewfinder")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("Upload and analyze your swing video")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    
                    Spacer()
                    
                    Image(systemName: "arrow.right.circle.fill")
                        .font(.largeTitle)
                        .symbolRenderingMode(.hierarchical)
                        .foregroundStyle(.tint)
                }
                .padding()
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
            
            // Coaching Video Button (4th Button)
            Button(action: {
                showCoachingVideo = true
                HapticManager.impact(.medium)
            }) {
                HStack {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("🎥 Video Coaching", systemImage: "play.tv.fill")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("Watch demo with AI coaching voice")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    
                    Spacer()
                    
                    Image(systemName: "arrow.right.circle.fill")
                        .font(.largeTitle)
                        .symbolRenderingMode(.hierarchical)
                        .foregroundStyle(.tint)
                }
                .padding()
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
            
            // Secondary Actions
            HStack(spacing: 16) {
                NavigationLink(destination: PreviousAnalysesView()) {
                    VStack(spacing: 12) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.title)
                            .symbolRenderingMode(.hierarchical)
                        
                        Text("History")
                            .font(.headline)
                        
                        Text("View past\nanalyses")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                }
                .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
                
                NavigationLink(destination: TutorialView()) {
                    VStack(spacing: 12) {
                        Image(systemName: "play.circle")
                            .font(.title)
                            .symbolRenderingMode(.hierarchical)
                        
                        Text("Tutorial")
                            .font(.headline)
                        
                        Text("Learn to use\nthe app")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                }
                .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
            }
            
        }
    }
    
    private var recentAnalysisSection: some View {
        LiquidGlassCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Label("Recent Analysis", systemImage: "chart.line.uptrend.xyaxis")
                        .font(.headline)
                    
                    Spacer()
                    
                    if let date = viewModel.lastAnalysisDate {
                        Text(date, style: .relative)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                
                if let result = viewModel.lastAnalysisResult {
                    HStack(spacing: 20) {
                        metricView(
                            title: "Swing Speed",
                            value: "\(result.swingSpeed)",
                            unit: "mph",
                            icon: "speedometer"
                        )
                        
                        metricView(
                            title: "Tempo",
                            value: "\(result.tempo)",
                            unit: "ratio",
                            icon: "metronome"
                        )
                        
                        metricView(
                            title: "Balance",
                            value: "\(result.balance)",
                            unit: "%",
                            icon: "figure.stand"
                        )
                    }
                    
                    Button(action: {
                        viewModel.loadLastAnalysis()
                        HapticManager.impact(.light)
                    }) {
                        Label("View Full Analysis", systemImage: "arrow.right")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
                }
            }
        }
    }
    
    private var tipsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Quick Tips", systemImage: "lightbulb")
                .font(.headline)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 16) {
                    tipCard(
                        icon: "camera",
                        title: "Camera Setup",
                        description: "Position camera at waist height, 10 feet away"
                    )
                    
                    tipCard(
                        icon: "sun.max",
                        title: "Lighting",
                        description: "Ensure good lighting for best analysis results"
                    )
                    
                    tipCard(
                        icon: "figure.golf",
                        title: "Full Swing",
                        description: "Capture your entire swing from address to finish"
                    )
                }
            }
        }
    }
    
    private func tipCard(icon: String, title: String, description: String) -> some View {
        LiquidGlassCard {
            VStack(alignment: .leading, spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .symbolRenderingMode(.hierarchical)
                    .foregroundStyle(.tint)
                
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(width: 160)
        }
    }
    
    private func metricView(title: String, value: String, unit: String, icon: String) -> some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.title3)
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.tint)
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(unit)
                .font(.caption2)
                .foregroundStyle(.secondary)
            
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
    
    private var greetingText: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12:
            return "Good Morning"
        case 12..<17:
            return "Good Afternoon"
        case 17..<22:
            return "Good Evening"
        default:
            return "Welcome"
        }
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