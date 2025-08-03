import SwiftUI
import AVFoundation

struct RecordingScreen: View {
    @EnvironmentObject var deps: AppDependencies
    @State private var viewModel: RecordingViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var showCancelConfirmation = false
    @State private var shouldNavigateToAnalysis = false
    @State private var deviceOrientation = UIDevice.current.orientation
    @State private var currentZoom: CGFloat = 1.0
    @State private var showZoomIndicator = false
    
    init() {
        _viewModel = State(initialValue: RecordingViewModel())
    }
    
    var body: some View {
        ZStack {
            if let session = viewModel.captureSession {
                CameraPreviewView(session: session)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .ignoresSafeArea(.all)
                    .accessibilityIdentifier("CameraPreview")
                    .gesture(
                        MagnificationGesture()
                            .onChanged(handleZoomGesture)
                            .onEnded { _ in
                                withAnimation(.easeOut(duration: 2)) {
                                    showZoomIndicator = false
                                }
                            }
                    )
            } else {
                ZStack {
                    Color.black.ignoresSafeArea()
                    ProgressView()
                }
            }
            
            VStack(spacing: 0) {
                TopControlsView(viewModel: viewModel, onCancel: handleCancel)
                Spacer()
                centerContentView
                Spacer()
                if viewModel.currentPhase == .recording {
                    TimeDisplayView(recordingTime: viewModel.recordingTime)
                }
            }
            .padding()
            
            if viewModel.currentFrameRate > 0 {
                VStack {
                    HStack {
                        Spacer()
                        FramerateDisplayView(frameRate: viewModel.currentFrameRate)
                    }
                    .padding(.top, viewModel.currentPhase == .setup ? 60 : 16)
                    Spacer()
                }
                .padding(.horizontal)
            }
            
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
            
            if viewModel.showProgressCircles {
                VStack {
                    ProgressCirclesView(circles: viewModel.progressCircles)
                    Spacer()
                }
            }
        }
        .navigationBarHidden(true)
        .preferredColorScheme(.dark)
        .onAppear(perform: setupScreen)
        .onDisappear(perform: viewModel.cleanup)
        .onReceive(NotificationCenter.default.publisher(for: UIDevice.orientationDidChangeNotification)) { _ in
            deviceOrientation = UIDevice.current.orientation
        }
        .onChange(of: viewModel.currentPhase, handlePhaseChange)
        .onChange(of: deps.currentRecordingId, handleCurrentRecordingIdChanged)
        .navigationDestination(isPresented: $shouldNavigateToAnalysis, destination: analysisDestination)
        .confirmationDialog("Cancel Recording", isPresented: $showCancelConfirmation, actions: cancelConfirmationActions, message: cancelConfirmationMessage)
        .alert("Recording Error", isPresented: .constant(viewModel.currentPhase == .error), actions: errorAlertActions, message: errorAlertMessage)
        .accessibilityIdentifier("RecordingScreen")
    }
    
    @ViewBuilder
    private var centerContentView: some View {
        switch viewModel.currentPhase {
        case .setup:
            SetupPhaseView(viewModel: viewModel)
        case .recording:
            RecordingPhaseView(viewModel: viewModel)
        case .processing:
            ProcessingPhaseView(viewModel: viewModel)
        case .error:
            EmptyView()
        }
    }
    
    private func setupScreen() {
        viewModel.dependencies = deps
        Task {
            do {
                try await viewModel.setupCamera()
                viewModel.ttsService.speakText("Alright. Get yourself into a position where we can see your whole swing, and let me know when you're ready.") { _ in
                    Task { try? await viewModel.startVoiceRecognition() }
                }
            } catch {
                viewModel.handle(error: error)
            }
        }
        UIDevice.current.beginGeneratingDeviceOrientationNotifications()
    }
    
    private func handlePhaseChange(oldValue: RecordingPhase, newValue: RecordingPhase) {
        if newValue == .processing && deps.currentRecordingId != nil {
            shouldNavigateToAnalysis = true
        }
    }
    
    private func handleCurrentRecordingIdChanged(oldValue: String?, newValue: String?) {
        if let id = newValue, viewModel.currentPhase == .processing {
            shouldNavigateToAnalysis = true
        }
    }
    
    private func handleCancel() {
        if viewModel.currentPhase == .recording {
            viewModel.ttsService.pauseSpeaking()
            showCancelConfirmation = true
        } else {
            dismiss()
        }
    }
    
    private func handleZoomGesture(_ value: MagnificationGesture.Value) {
        if value < 1.0 {
            let newZoom = currentZoom * value
            if newZoom >= 0.5 && newZoom <= 1.0 {
                currentZoom = newZoom
                viewModel.setZoomLevel(currentZoom)
                withAnimation(.easeIn(duration: 0.1)) {
                    showZoomIndicator = true
                }
            }
        }
    }
    
    private func analysisDestination() -> some View {
        SwingAnalysisView(dependencies: deps).environmentObject(deps)
    }
    
    @ViewBuilder
    private func cancelConfirmationActions() -> some View {
        Button("Cancel Recording", role: .destructive) { dismiss() }
        Button("Continue Recording", role: .cancel) {}
    }
    
    private func cancelConfirmationMessage() -> some View {
        Text("Are you sure you want to cancel? Your recording will be lost.")
    }
    
    @ViewBuilder
    private func errorAlertActions() -> some View {
        if let error = viewModel.errorType {
            if error == .cameraPermissionDenied {
                Button("Settings") {
                    if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
                        UIApplication.shared.open(settingsURL)
                    }
                }
            }
            Button("Retry") {
                Task {
                    viewModel.resetState()
                    await setupScreen()
                }
            }
            Button("Cancel", role: .cancel) { dismiss() }
        }
    }
    
    private func errorAlertMessage() -> some View {
        Text(viewModel.errorType?.localizedDescription ?? "Unknown error occurred")
    }
}

#Preview {
    RecordingScreen()
        .preferredColorScheme(.dark)
}
