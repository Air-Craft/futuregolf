import SwiftUI
import AVFoundation

struct RecordingScreen: View {
    @EnvironmentObject var deps: AppDependencies
    @State private var viewModel = RecordingViewModel()
    @Environment(\.dismiss) private var dismiss
    @State private var showCancelConfirmation = false
    @State private var cameraPreview: AVCaptureVideoPreviewLayer?
    @State private var shouldNavigateToAnalysis = false
    @State private var deviceOrientation = UIDevice.current.orientation
    @State private var currentZoom: CGFloat = 1.0
    @State private var showZoomIndicator = false
    
    var body: some View {
        ZStack {
            // Camera Preview Background
            CameraPreviewView(viewModel: viewModel)
                .ignoresSafeArea(.all)
                .accessibilityIdentifier("CameraPreview")
                .gesture(
                    MagnificationGesture()
                        .onChanged { value in
                            handleZoomGesture(value)
                        }
                        .onEnded { _ in
                            withAnimation(.easeOut(duration: 2)) {
                                showZoomIndicator = false
                            }
                        }
                )
            
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
            
            // Zoom Indicator
            if showZoomIndicator {
                VStack {
                    Spacer()
                    HStack {
                        Spacer()
                        ZoomIndicatorView(zoomLevel: currentZoom)
                            .transition(.opacity.combined(with: .scale))
                    }
                    .padding(.trailing, 20)
                    .padding(.bottom, 100)
                }
            }
        }
        .navigationBarHidden(true)
        .preferredColorScheme(.dark) // Better visibility over camera feed
        .onAppear {
            viewModel.dependencies = deps
            setupRecordingScreen()
            setupOrientationObserver()
        }
        .onDisappear {
            viewModel.cleanup()
        }
        .onReceive(NotificationCenter.default.publisher(for: UIDevice.orientationDidChangeNotification)) { _ in
            let newOrientation = UIDevice.current.orientation
            if newOrientation != deviceOrientation {
                deviceOrientation = newOrientation
                viewModel.updateOrientation(newOrientation)
            }
        }
        .onChange(of: viewModel.currentPhase) { oldValue, newValue in
            print("🎹 RecordingScreen: currentPhase changed from \(oldValue) to \(newValue)")
            
            if newValue == .processing && deps.currentRecordingId != nil {
                print("🎹 Recording complete, navigating to analysis")
                shouldNavigateToAnalysis = true
            }
        }
        .navigationDestination(isPresented: $shouldNavigateToAnalysis) {
            SwingAnalysisView(dependencies: deps)
                .environmentObject(deps)
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
            
            // Removed left-handed mode toggle as requested
            
            // Debug buttons moved to debug panel
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
                
                // Play welcome message first, THEN start voice recognition
                // This prevents the TTS from triggering voice commands
                viewModel.ttsService.speakText("Alright. Get yourself into a position where we can see your whole swing, and let me know when you're ready.") { _ in
                    // Start voice recognition after TTS completes
                    Task {
                        try? await viewModel.startVoiceRecognition()
                    }
                }
            } catch {
                handleSetupError(error)
            }
        }
    }
    
    private func setupOrientationObserver() {
        // Enable orientation changes
        UIDevice.current.beginGeneratingDeviceOrientationNotifications()
        
        // Set initial orientation
        deviceOrientation = UIDevice.current.orientation
        viewModel.updateOrientation(deviceOrientation)
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
    
    private func handleZoomGesture(_ value: CGFloat) {
        // Only allow zoom out (value < 1.0)
        if value < 1.0 {
            let newZoom = currentZoom * value
            
            // Limit zoom range from 0.5x to 1.0x
            if newZoom >= 0.5 && newZoom <= 1.0 {
                currentZoom = newZoom
                viewModel.setZoomLevel(currentZoom)
                
                withAnimation(.easeIn(duration: 0.1)) {
                    showZoomIndicator = true
                }
            }
        }
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
    var viewModel: RecordingViewModel
    
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
            
            // Set black background to prevent flash
            newPreviewLayer.backgroundColor = UIColor.black.cgColor
            
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
                    }
                } else {
                    print("🐛 CameraPreviewCoordinator: Capture session already running")
                }
            }
        }
        
        deinit {
            previewLayer?.removeFromSuperlayer()
        }
    }
}

// MARK: - Zoom Indicator View

struct ZoomIndicatorView: View {
    let zoomLevel: CGFloat
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "minus.magnifyingglass")
                .font(.system(size: 14))
            
            Text(String(format: "%.1fx", zoomLevel))
                .font(.system(size: 16, weight: .medium, design: .monospaced))
            
            Image(systemName: "plus.magnifyingglass")
                .font(.system(size: 14))
        }
        .foregroundColor(.white)
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
    }
}

// MARK: - Haptics Helper (removed - using existing LiquidGlassHaptics from design system)

// MARK: - Preview

#Preview {
    RecordingScreen()
        .preferredColorScheme(.dark)
}
