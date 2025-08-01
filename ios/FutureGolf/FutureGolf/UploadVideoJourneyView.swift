import SwiftUI
import PhotosUI
import AVKit

struct UploadVideoJourneyView: View {
    @Bindable var viewModel: VideoAnalysisViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var currentStep = 0
    @State private var showVideoPicker = false
    @State private var isAnalyzing = false
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Progress Indicator
                progressIndicator
                
                // Content based on current step
                Group {
                    switch currentStep {
                    case 0:
                        instructionsStep
                    case 1:
                        videoSelectionStep
                    case 2:
                        videoPreviewStep
                    case 3:
                        if viewModel.showError {
                            errorView
                        } else {
                            uploadingStep
                        }
                    default:
                        EmptyView()
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .animation(.spring(response: 0.5, dampingFraction: 0.8), value: currentStep)
            }
            .liquidGlassBackground(intensity: .light)
            .navigationTitle("Upload Swing Video")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .photosPicker(
                isPresented: $showVideoPicker,
                selection: $viewModel.selectedItem,
                matching: .videos
            )
            .onChange(of: viewModel.selectedItem) { _, newItem in
                if newItem != nil {
                    Task {
                        await viewModel.loadVideo(from: newItem)
                        if viewModel.selectedVideoURL != nil {
                            withAnimation {
                                currentStep = 2
                            }
                        }
                    }
                }
            }
            .onChange(of: viewModel.analysisResult) { _, newResult in
                if newResult != nil {
                    dismiss()
                }
            }
        }
    }
    
    private var progressIndicator: some View {
        HStack(spacing: 8) {
            ForEach(0..<4) { step in
                Circle()
                    .fill(step <= currentStep ? Color.accentColor : Color.secondary.opacity(0.3))
                    .frame(width: 8, height: 8)
                    .scaleEffect(step == currentStep ? 1.5 : 1.0)
                    .animation(.spring(response: 0.3), value: currentStep)
            }
        }
        .padding()
        .background(.ultraThinMaterial, in: Capsule())
        .padding()
    }
    
    private var instructionsStep: some View {
        VStack(spacing: 24) {
            Spacer()
            
            // Icon
            Image(systemName: "video.badge.checkmark")
                .font(.system(size: 80))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.tint)
                .padding()
                .liquidGlassBackground(intensity: .medium, cornerRadius: 30)
                .depthLayer(level: .raised)
            
            // Title
            Text("Before You Begin")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            // Instructions
            VStack(alignment: .leading, spacing: 20) {
                instructionRow(
                    icon: "camera.viewfinder",
                    title: "Camera Position",
                    description: "Place camera 10 feet away at waist height"
                )
                
                instructionRow(
                    icon: "figure.golf",
                    title: "Full Swing",
                    description: "Capture from address to follow-through"
                )
                
                instructionRow(
                    icon: "sun.max",
                    title: "Good Lighting",
                    description: "Ensure clear visibility of your swing"
                )
                
                instructionRow(
                    icon: "iphone.landscape",
                    title: "Landscape Mode",
                    description: "Hold device horizontally for best results"
                )
            }
            .padding()
            .liquidGlassBackground(intensity: .light, cornerRadius: 16)
            
            Spacer()
            
            // Continue Button
            Button(action: {
                withAnimation {
                    currentStep = 1
                }
                HapticManager.impact(.medium)
            }) {
                Label("Continue", systemImage: "arrow.right")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
            .padding(.horizontal)
        }
        .padding()
    }
    
    private var videoSelectionStep: some View {
        VStack(spacing: 24) {
            Spacer()
            
            // Icon
            Image(systemName: "photo.stack")
                .font(.system(size: 80))
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.tint)
            
            Text("Select Your Video")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text("Choose a video from your photo library")
                .font(.title3)
                .foregroundStyle(.secondary)
            
            Spacer()
            
            // Selection Options
            VStack(spacing: 16) {
                Button(action: {
                    showVideoPicker = true
                    HapticManager.impact(.medium)
                }) {
                    HStack {
                        Image(systemName: "photo.on.rectangle")
                            .font(.title2)
                        Text("Choose from Library")
                            .font(.headline)
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
                
                Button(action: {
                    // TODO: Implement camera recording
                    HapticManager.impact(.light)
                }) {
                    HStack {
                        Image(systemName: "camera")
                            .font(.title2)
                        Text("Record New Video")
                            .font(.headline)
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
                .disabled(true) // For now
            }
            .padding(.horizontal)
            
            Spacer()
            
            // Back Button
            Button(action: {
                withAnimation {
                    currentStep = 0
                }
                HapticManager.impact(.light)
            }) {
                Label("Back", systemImage: "arrow.left")
            }
            .foregroundStyle(.secondary)
        }
        .padding()
    }
    
    private var videoPreviewStep: some View {
        VStack(spacing: 24) {
            // Video Preview
            if let videoURL = viewModel.selectedVideoURL {
                VideoPlayer(player: AVPlayer(url: videoURL))
                    .frame(height: 300)
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .strokeBorder(.thinMaterial, lineWidth: 1)
                    )
                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
                    .padding(.horizontal)
            }
            
            Text("Review Your Video")
                .font(.title2)
                .fontWeight(.bold)
            
            Text("Make sure the entire swing is visible")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            
            Spacer()
            
            // Action Buttons
            VStack(spacing: 12) {
                Button(action: {
                    Task {
                        withAnimation {
                            currentStep = 3
                        }
                        await viewModel.uploadVideo()
                    }
                    HapticManager.impact(.medium)
                }) {
                    Label("Analyze Video", systemImage: "waveform.badge.magnifyingglass")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
                
                Button(action: {
                    viewModel.selectedVideoURL = nil
                    viewModel.selectedItem = nil
                    showVideoPicker = true
                    HapticManager.impact(.light)
                }) {
                    Label("Choose Different Video", systemImage: "arrow.triangle.2.circlepath")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
            }
            .padding(.horizontal)
        }
        .padding()
    }
    
    private var uploadingStep: some View {
        VStack(spacing: 32) {
            Spacer()
            
            // Animated Progress
            ZStack {
                Circle()
                    .stroke(Color.secondary.opacity(0.2), lineWidth: 8)
                    .frame(width: 120, height: 120)
                
                Circle()
                    .trim(from: 0, to: 0.7)
                    .stroke(
                        LinearGradient(
                            colors: [.accentColor, .accentColor.opacity(0.5)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        style: StrokeStyle(lineWidth: 8, lineCap: .round)
                    )
                    .frame(width: 120, height: 120)
                    .rotationEffect(.degrees(-90))
                    .rotation3DEffect(
                        .degrees(isAnalyzing ? 360 : 0),
                        axis: (x: 0, y: 0, z: 1)
                    )
                    .animation(
                        .linear(duration: 2)
                        .repeatForever(autoreverses: false),
                        value: isAnalyzing
                    )
                
                Image(systemName: "figure.golf")
                    .font(.system(size: 50))
                    .symbolRenderingMode(.hierarchical)
                    .foregroundStyle(.tint)
            }
            
            VStack(spacing: 8) {
                Text("Analyzing Your Swing")
                    .font(.title)
                    .fontWeight(.bold)
                
                Text("This may take a moment...")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            
            // Status Messages
            VStack(alignment: .leading, spacing: 12) {
                statusRow(text: "Uploading video", isComplete: viewModel.uploadProgress > 0.2)
                statusRow(text: "Processing frames", isComplete: viewModel.uploadProgress > 0.4)
                statusRow(text: "Analyzing swing mechanics", isComplete: viewModel.uploadProgress > 0.6)
                statusRow(text: "Generating coaching tips", isComplete: viewModel.uploadProgress > 0.8)
            }
            
            // Progress bar
            VStack {
                if viewModel.uploadProgress > 0 {
                    ProgressView(value: viewModel.uploadProgress) {
                        Text(viewModel.uploadStatus)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .progressViewStyle(.linear)
                    .tint(.fairwayGreen)
                }
            }
            .padding()
            .liquidGlassBackground(intensity: .light, cornerRadius: 16)
            
            Spacer()
        }
        .padding()
        .onAppear {
            isAnalyzing = true
        }
        .onDisappear {
            isAnalyzing = false
        }
    }
    
    private var errorView: some View {
        VStack(spacing: 24) {
            // Error Icon
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 60))
                .symbolRenderingMode(.multicolor)
                .foregroundStyle(.red)
            
            VStack(spacing: 12) {
                Text("Upload Failed")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text(viewModel.errorMessage)
                    .font(.body)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
            
            // Error Details Card
            if let error = viewModel.currentError {
                LiquidGlassCard {
                    VStack(alignment: .leading, spacing: 16) {
                        Label("What to do:", systemImage: "lightbulb")
                            .font(.headline)
                            .foregroundColor(.glassText)
                        
                        Text(getErrorSuggestion(for: error))
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                }
                .padding(.horizontal)
            }
            
            Spacer()
            
            // Action Buttons
            VStack(spacing: 12) {
                if let error = viewModel.currentError {
                    Button(action: {
                        Task {
                            switch error {
                            case .networkUnavailable:
                                // Open settings
                                if let url = URL(string: UIApplication.openSettingsURLString) {
                                    await UIApplication.shared.open(url)
                                }
                            case .serverError, .timeout:
                                await viewModel.retryUpload()
                                withAnimation {
                                    currentStep = 3
                                }
                            case .invalidVideo, .fileTooLarge:
                                withAnimation {
                                    currentStep = 0
                                    viewModel.selectedVideoURL = nil
                                }
                            case .unauthorized:
                                // Handle sign in
                                dismiss()
                            }
                        }
                        HapticManager.impact(.medium)
                    }) {
                        Label(viewModel.currentError?.recoveryAction ?? "Try Again", systemImage: "arrow.clockwise")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
                }
                
                Button(action: {
                    withAnimation {
                        currentStep = 0
                        viewModel.selectedVideoURL = nil
                        viewModel.showError = false
                    }
                    HapticManager.impact(.light)
                }) {
                    Text("Choose Different Video")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
                
                Button(action: {
                    dismiss()
                }) {
                    Text("Cancel")
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal)
        }
        .padding()
    }
    
    private func getErrorSuggestion(for error: UploadError) -> String {
        switch error {
        case .networkUnavailable:
            return "Check your Wi-Fi or cellular connection and try again. For best results, use a stable Wi-Fi connection."
        case .serverError:
            return "Our servers are experiencing issues. Please try again in a few minutes."
        case .timeout:
            return "The upload took too long. Try with a smaller video or better internet connection."
        case .invalidVideo:
            return "Please select a video in MP4 or MOV format. The video should show a clear view of your golf swing."
        case .fileTooLarge:
            return "Try recording a shorter video (under 30 seconds) or reduce the video quality in your camera settings."
        case .unauthorized:
            return "You need to sign in to upload and analyze videos. Go to Settings to sign in."
        }
    }
    
    private func instructionRow(icon: String, title: String, description: String) -> some View {
        HStack(spacing: 16) {
            Image(systemName: icon)
                .font(.title2)
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(.tint)
                .frame(width: 40)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                Text(description)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            
            Spacer()
        }
    }
    
    private func statusRow(text: String, isComplete: Bool) -> some View {
        HStack(spacing: 12) {
            Image(systemName: isComplete ? "checkmark.circle.fill" : "circle")
                .font(.title3)
                .foregroundStyle(isComplete ? .green : .secondary)
            
            Text(text)
                .font(.subheadline)
                .foregroundStyle(isComplete ? .primary : .secondary)
            
            Spacer()
        }
    }
}

// Haptic Feedback Manager
struct HapticManager {
    static func impact(_ style: UIImpactFeedbackGenerator.FeedbackStyle) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.prepare()
        generator.impactOccurred()
    }
    
    static func notification(_ type: UINotificationFeedbackGenerator.FeedbackType) {
        let generator = UINotificationFeedbackGenerator()
        generator.prepare()
        generator.notificationOccurred(type)
    }
}

#Preview {
    UploadVideoJourneyView(viewModel: VideoAnalysisViewModel())
}