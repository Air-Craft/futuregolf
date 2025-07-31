import SwiftUI
import AVFoundation

struct RecordingScreen: View {
    @StateObject private var viewModel = RecordingViewModel()
    @Environment(\.dismiss) private var dismiss
    @State private var showCancelConfirmation = false
    @State private var cameraPreview: AVCaptureVideoPreviewLayer?
    @State private var showSwingAnalysis = false
    @State private var recordedVideoURL: URL?
    
    var body: some View {
        ZStack {
            // Camera Preview Background
            CameraPreviewView(viewModel: viewModel)
                .ignoresSafeArea(.all)
                .accessibilityIdentifier("CameraPreview")
            
            // Main UI Overlay
            VStack(spacing: 0) {
                // Top Controls
                topControlsView
                
                Spacer()
                
                // Center Content based on phase
                centerContentView
                
                Spacer()
                
                // Bottom Time Display
                if viewModel.currentPhase == .recording {
                    timeDisplayView
                }
            }
            .padding()
            
            // Framerate Display (Top Right Corner, below camera flip button)
            if viewModel.currentFrameRate > 0 {
                VStack {
                    HStack {
                        Spacer()
                        framerateDisplayView
                    }
                    .padding(.top, viewModel.currentPhase == .setup ? 60 : 16) // Space for camera flip button when in setup
                    Spacer()
                }
                .padding(.horizontal)
            }
        }
        .navigationBarHidden(true)
        .preferredColorScheme(.dark) // Better visibility over camera feed
        .onAppear {
            setupRecordingScreen()
        }
        .onDisappear {
            viewModel.cleanup()
        }
        .onChange(of: viewModel.currentPhase) { oldValue, newValue in
            if newValue == .processing {
                // Start a delay before showing SwingAnalysisView
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    if let videoURL = viewModel.recordedVideoURL {
                        recordedVideoURL = videoURL
                        showSwingAnalysis = true
                    }
                }
            }
        }
        .fullScreenCover(isPresented: $showSwingAnalysis) {
            if let videoURL = recordedVideoURL {
                NavigationStack {
                    SwingAnalysisView(videoURL: videoURL, analysisId: nil)
                }
            }
        }
        .confirmationDialog("Cancel Recording", isPresented: $showCancelConfirmation) {
            Button("Cancel Recording", role: .destructive) {
                dismiss()
            }
            Button("Continue Recording", role: .cancel) { }
        } message: {
            Text("Are you sure you want to cancel? Your recording will be lost.")
        }
        .alert("Recording Error", isPresented: .constant(viewModel.currentPhase == .error)) {
            if let error = viewModel.errorType {
                Button("Settings") {
                    if error == .cameraPermissionDenied {
                        openSettings()
                    }
                }
                Button("Retry") {
                    Task {
                        await retrySetup()
                    }
                }
                Button("Cancel") {
                    dismiss()
                }
            }
        } message: {
            Text(viewModel.errorType?.localizedDescription ?? "Unknown error occurred")
        }
        .accessibilityIdentifier("RecordingScreen")
    }
    
    // MARK: - Top Controls
    
    private var topControlsView: some View {
        HStack {
            // Cancel Button (Upper Left)
            Button(action: {
                if viewModel.currentPhase == .recording {
                    viewModel.ttsService.pauseSpeaking()
                    showCancelConfirmation = true
                } else {
                    dismiss()
                }
            }) {
                Image(systemName: "xmark")
                    .font(.title2)
                    .foregroundColor(.white)
                    .frame(width: 44, height: 44)
                    .background(.ultraThinMaterial, in: Circle())
            }
            .accessibilityIdentifier("Cancel")
            .accessibilityLabel("Cancel recording")
            
            Spacer()
            
            // Camera Switch Button
            if viewModel.currentPhase == .setup {
                Button(action: {
                    withAnimation(.spring(response: 0.3)) {
                        viewModel.switchCamera()
                    }
                    LiquidGlassHaptics.impact(.light)
                }) {
                    Image(systemName: "camera.rotate")
                        .font(.title2)
                        .foregroundColor(.white)
                        .frame(width: 44, height: 44)
                        .background(.ultraThinMaterial, in: Circle())
                }
                .accessibilityIdentifier("Switch Camera")
                .accessibilityLabel("Switch between front and rear camera")
            }
        }
    }
    
    // MARK: - Center Content
    
    private var centerContentView: some View {
        VStack(spacing: 24) {
            switch viewModel.currentPhase {
            case .setup:
                setupPhaseView
            case .recording:
                recordingPhaseView
            case .processing:
                processingPhaseView
            case .error:
                EmptyView() // Handled by alert
            }
        }
    }
    
    // MARK: - Setup Phase View
    
    private var setupPhaseView: some View {
        VStack(spacing: 32) {
            // Positioning Indicator (Fade white line art)
            if viewModel.showPositioningIndicator {
                PositioningIndicatorView(isLeftHanded: viewModel.isLeftHandedMode)
                    .transition(.opacity.combined(with: .scale))
            }
            
            // Instructions
            VStack(spacing: 16) {
                Text("Position yourself in frame")
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                    .multilineTextAlignment(.center)
                
                Text("Say \"begin\" when you're ready to start recording")
                    .font(.body)
                    .foregroundColor(.white.opacity(0.8))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
            .liquidGlassBackground(intensity: .medium, cornerRadius: 16)
            .padding(.horizontal)
            
            // Left-handed Mode Toggle
            Button(action: {
                withAnimation(.spring(response: 0.3)) {
                    viewModel.toggleLeftHandedMode()
                }
                LiquidGlassHaptics.impact(.light)
            }) {
                HStack {
                    Image(systemName: viewModel.isLeftHandedMode ? "checkmark.circle.fill" : "circle")
                        .font(.title3)
                    Text("Left-Handed Mode")
                        .font(.headline)
                }
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .background(.ultraThinMaterial, in: Capsule())
            }
            .accessibilityIdentifier("Left-Handed Mode")
            .accessibilityLabel("Toggle left-handed mode for positioning indicator")
            
            #if DEBUG
            // Debug buttons for testing cache
            VStack(spacing: 10) {
                Button("Debug: Force Cache Warm") {
                    print("🐛 DEBUG: Forcing cache warm...")
                    TTSService.shared.cacheManager.warmCache()
                }
                .font(.caption)
                .foregroundColor(.orange)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(.ultraThinMaterial, in: Capsule())
                
                Button("Debug: List Cache") {
                    print("🐛 DEBUG: Listing cache contents...")
                    TTSService.shared.cacheManager.debugListCachedFiles()
                }
                .font(.caption)
                .foregroundColor(.orange)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(.ultraThinMaterial, in: Capsule())
                
                Button("Debug: Test TTS Server") {
                    print("🐛 DEBUG: Testing TTS server...")
                    Task {
                        // First test basic connectivity
                        print("🐛 DEBUG: Server URL: \(Config.serverBaseURL)")
                        
                        do {
                            // Test health endpoint first
                            let healthURL = URL(string: "\(Config.serverBaseURL)/health")!
                            print("🐛 DEBUG: Testing health endpoint: \(healthURL)")
                            
                            var healthRequest = URLRequest(url: healthURL)
                            healthRequest.timeoutInterval = Config.healthCheckTimeout
                            
                            let (healthData, healthResponse) = try await URLSession.shared.data(for: healthRequest)
                            
                            if let httpResponse = healthResponse as? HTTPURLResponse {
                                print("🐛 DEBUG: Health check - Status: \(httpResponse.statusCode)")
                                if let responseString = String(data: healthData, encoding: .utf8) {
                                    print("🐛 DEBUG: Health response: \(responseString)")
                                }
                            }
                            
                            // Then test TTS endpoint
                            let testPhrase = "Test connection"
                            let urlString = "\(Config.serverBaseURL)/api/v1/tts/coaching"
                            print("🐛 DEBUG: Testing TTS URL: \(urlString)")
                            
                            guard let url = URL(string: urlString) else {
                                print("🐛 DEBUG: Invalid URL")
                                return
                            }
                            
                            let requestBody = ["text": testPhrase, "voice": "onyx", "model": "tts-1-hd", "speed": 0.9]
                            var request = URLRequest(url: url)
                            request.httpMethod = "POST"
                            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
                            request.timeoutInterval = Config.ttsSynthesisTimeout
                            
                            let (data, response) = try await URLSession.shared.data(for: request)
                            
                            if let httpResponse = response as? HTTPURLResponse {
                                print("🐛 DEBUG: TTS Server Response: \(httpResponse.statusCode)")
                                print("🐛 DEBUG: Data size: \(data.count) bytes")
                                print("🐛 DEBUG: ✅ Server is working!")
                            }
                        } catch let error as URLError {
                            print("🐛 DEBUG: Network Error Code: \(error.code.rawValue)")
                            print("🐛 DEBUG: Network Error: \(error.localizedDescription)")
                            print("🐛 DEBUG: ❌ Cannot reach server at \(Config.serverBaseURL)")
                            print("🐛 DEBUG: Check that:")
                            print("🐛 DEBUG:   1. Backend server is running")
                            print("🐛 DEBUG:   2. IP address \(Config.serverBaseURL) is correct")
                            print("🐛 DEBUG:   3. Device is on same network as server")
                        } catch {
                            print("🐛 DEBUG: Unexpected Error: \(error)")
                        }
                    }
                }
                .font(.caption)
                .foregroundColor(.orange)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(.ultraThinMaterial, in: Capsule())
            }
            .padding(.top, 20)
            #endif
        }
    }
    
    // MARK: - Recording Phase View
    
    private var recordingPhaseView: some View {
        VStack(spacing: 24) {
            // Progress Indicator (3 circles)
            if viewModel.showProgressCircles {
                ProgressCirclesView(circles: viewModel.progressCircles)
                    .transition(.scale.combined(with: .opacity))
            }
            
            // Swing Count Display
            Text("\(viewModel.swingCount) of \(viewModel.targetSwingCount) swings")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(.ultraThinMaterial, in: Capsule())
        }
        .animation(.spring(response: 0.5, dampingFraction: 0.8), value: viewModel.swingCount)
    }
    
    // MARK: - Processing Phase View
    
    private var processingPhaseView: some View {
        VStack(spacing: 24) {
            // Loading Animation
            ZStack {
                Circle()
                    .stroke(Color.white.opacity(0.3), lineWidth: 6)
                    .frame(width: 80, height: 80)
                
                Circle()
                    .trim(from: 0, to: 0.7)
                    .stroke(
                        LinearGradient(
                            colors: [.white, .white.opacity(0.5)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        style: StrokeStyle(lineWidth: 6, lineCap: .round)
                    )
                    .frame(width: 80, height: 80)
                    .rotationEffect(.degrees(-90))
                    .animation(
                        .linear(duration: 2)
                        .repeatForever(autoreverses: false),
                        value: viewModel.currentPhase == .processing
                    )
                
                Image(systemName: "figure.golf")
                    .font(.title)
                    .foregroundColor(.white)
            }
            
            Text("Processing your swings...")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.white)
            
            Text("This may take a moment")
                .font(.body)
                .foregroundColor(.white.opacity(0.8))
        }
        .liquidGlassBackground(intensity: .medium, cornerRadius: 16)
        .padding(.horizontal)
    }
    
    // MARK: - Framerate Display
    
    private var framerateDisplayView: some View {
        Text("\(Int(viewModel.currentFrameRate)) FPS")
            .font(.system(size: 12, weight: .medium, design: .monospaced))
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 6))
            .opacity(0.8)
    }
    
    // MARK: - Time Display
    
    private var timeDisplayView: some View {
        VStack(spacing: 8) {
            Text(formatTime(viewModel.recordingTime))
                .font(.system(size: 32, weight: .medium, design: .monospaced))
                .foregroundColor(.white)
            
            Text("Recording Time")
                .font(.caption)
                .foregroundColor(.white.opacity(0.7))
                .textCase(.uppercase)
                .tracking(1)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    // MARK: - Setup Methods
    
    private func setupRecordingScreen() {
        Task {
            do {
                try await viewModel.setupCamera()
                try await viewModel.startVoiceRecognition()
                // Play welcome message once setup is complete
                viewModel.ttsService.speakText("Alright. Get yourself into a position where we can see your whole swing, and let me know when you're ready.")
            } catch {
                handleSetupError(error)
            }
        }
    }
    
    private func retrySetup() async {
        viewModel.currentPhase = .setup
        viewModel.errorType = nil
        await setupRecordingScreen()
    }
    
    private func handleSetupError(_ error: Error) {
        if let recordingError = error as? RecordingError {
            viewModel.errorType = recordingError
            viewModel.currentPhase = .error
        }
    }
    
    private func openSettings() {
        if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(settingsURL)
        }
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        let milliseconds = Int((time.truncatingRemainder(dividingBy: 1)) * 100)
        return String(format: "%02d:%02d.%02d", minutes, seconds, milliseconds)
    }
}

// MARK: - Positioning Indicator View

struct PositioningIndicatorView: View {
    let isLeftHanded: Bool
    @State private var opacity: Double = 0.8
    
    var body: some View {
        VStack(spacing: 16) {
            // Golfer silhouette with club
            golferSilhouette
            
            // Distance guide
            distanceGuide
        }
        .opacity(opacity)
        .onAppear {
            withAnimation(.easeInOut(duration: 2).repeatForever(autoreverses: true)) {
                opacity = 0.4
            }
        }
    }
    
    private var golferSilhouette: some View {
        ZStack {
            // Golfer figure
            Image(systemName: "figure.golf")
                .font(.system(size: 100))
                .foregroundColor(.white.opacity(0.6))
                .scaleEffect(x: isLeftHanded ? -1 : 1, y: 1) // Mirror for left-handed
            
            // Positioning frame
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.white.opacity(0.4), style: StrokeStyle(lineWidth: 2, dash: [10, 5]))
                .frame(width: 200, height: 300)
        }
    }
    
    private var distanceGuide: some View {
        VStack(spacing: 8) {
            Text("10 feet away")
                .font(.headline)
                .foregroundColor(.white)
            
            Text("Full body in frame")
                .font(.subheadline)
                .foregroundColor(.white.opacity(0.8))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
}

// MARK: - Progress Circles View

struct ProgressCirclesView: View {
    let circles: [ProgressCircle]
    
    var body: some View {
        HStack(spacing: 16) {
            ForEach(Array(circles.enumerated()), id: \.element.id) { index, circle in
                ZStack {
                    Circle()
                        .fill(circle.isCompleted ? Color.green : Color.white.opacity(0.3))
                        .frame(width: 50, height: 50)
                    
                    if circle.isCompleted {
                        Image(systemName: "checkmark")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .scaleEffect(circle.isCompleted ? 1 : 0)
                            .animation(.spring(response: 0.4, dampingFraction: 0.6), value: circle.isCompleted)
                    } else {
                        Text("\(index + 1)")
                            .font(.title2)
                            .fontWeight(.semibold)
                            .foregroundColor(.white)
                    }
                }
                .scaleEffect(circle.isCompleted ? 1.1 : 1.0)
                .animation(.spring(response: 0.3, dampingFraction: 0.7), value: circle.isCompleted)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
    }
}

// MARK: - Camera Preview View

struct CameraPreviewView: UIViewRepresentable {
    @ObservedObject var viewModel: RecordingViewModel
    
    func makeUIView(context: Context) -> UIView {
        print("🐛 CameraPreviewView: Creating preview view")
        
        let view = UIView()
        view.backgroundColor = .black
        
        // Store reference to update bounds later
        context.coordinator.previewView = view
        
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {
        print("🐛 CameraPreviewView: Updating preview view, bounds: \(uiView.bounds)")
        
        // Update coordinator with current view
        context.coordinator.previewView = uiView
        
        // Setup or update the preview layer
        context.coordinator.setupPreviewLayer(for: viewModel.captureSession, in: uiView)
    }
    
    func makeCoordinator() -> CameraPreviewCoordinator {
        return CameraPreviewCoordinator()
    }
    
    class CameraPreviewCoordinator: NSObject {
        weak var previewView: UIView?
        private var previewLayer: AVCaptureVideoPreviewLayer?
        
        func setupPreviewLayer(for session: AVCaptureSession?, in view: UIView) {
            guard let session = session else {
                print("🐛 CameraPreviewCoordinator: No capture session available")
                return
            }
            
            // Remove existing preview layer if present
            if let existingLayer = previewLayer {
                existingLayer.removeFromSuperlayer()
                previewLayer = nil
            }
            
            print("🐛 CameraPreviewCoordinator: Setting up preview layer with session")
            
            let newPreviewLayer = AVCaptureVideoPreviewLayer(session: session)
            newPreviewLayer.videoGravity = .resizeAspectFill
            newPreviewLayer.frame = view.bounds
            
            // Set background color for debugging
            newPreviewLayer.backgroundColor = UIColor.red.cgColor
            
            view.layer.addSublayer(newPreviewLayer)
            previewLayer = newPreviewLayer
            
            print("🐛 CameraPreviewCoordinator: Preview layer added with frame: \(newPreviewLayer.frame)")
            
            // Start session on background queue
            DispatchQueue.global(qos: .userInitiated).async {
                print("🐛 CameraPreviewCoordinator: Starting capture session...")
                if !session.isRunning {
                    session.startRunning()
                    DispatchQueue.main.async {
                        print("🐛 CameraPreviewCoordinator: Capture session started successfully")
                        // Remove red background once session is running
                        newPreviewLayer.backgroundColor = UIColor.clear.cgColor
                    }
                } else {
                    print("🐛 CameraPreviewCoordinator: Capture session already running")
                    DispatchQueue.main.async {
                        newPreviewLayer.backgroundColor = UIColor.clear.cgColor
                    }
                }
            }
        }
        
        deinit {
            previewLayer?.removeFromSuperlayer()
        }
    }
}

// MARK: - Haptics Helper (removed - using existing LiquidGlassHaptics from design system)

// MARK: - Preview

#Preview {
    RecordingScreen()
        .preferredColorScheme(.dark)
}
