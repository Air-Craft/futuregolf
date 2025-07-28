import SwiftUI
import PhotosUI
import AVKit

struct ContentView: View {
    @State private var viewModel = VideoAnalysisViewModel()
    @State private var showVideoPreview = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Video Preview Section
                    if let videoURL = viewModel.selectedVideoURL {
                        LiquidGlassCard(
                            cornerRadius: 20,
                            glassIntensity: .ultraLight,
                            depthLevel: .elevated
                        ){
                            VideoPlayer(player: AVPlayer(url: videoURL))
                                .frame(height: 300)
                                .overlay(alignment: .topTrailing) {
                                    // Video info overlay
                                    HStack(spacing: 8) {
                                        Image(systemName: "video.fill")
                                            .font(.caption)
                                        Text("Ready to Analyze")
                                            .font(.caption)
                                            .fontWeight(.medium)
                                    }
                                    .foregroundColor(.white)
                                    .padding(8)
                                    .background(.ultraThinMaterial, in: Capsule())
                                    .padding(12)
                                }
                        }
                        .padding(.horizontal)
                        .liquidGlassTransition(isVisible: showVideoPreview)
                        .onAppear {
                            withAnimation(.liquidGlassSpring) {
                                showVideoPreview = true
                            }
                        }
                    }
                    
                    // Action Buttons Section
                    VStack(spacing: 16) {
                        // Video Selection Button
                        PhotosPicker(
                            selection: $viewModel.selectedItem,
                            matching: .videos
                        ) {
                            HStack {
                                Image(systemName: "photo.stack")
                                    .font(.system(size: 20))
                                Text("Select Video from Library")
                                    .fontWeight(.medium)
                            }
                            .foregroundColor(.glassText)
                            .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
                        .padding(.horizontal)
                        .onChange(of: viewModel.selectedItem) { _, newItem in
                            Task {
                                LiquidGlassHaptics.selection()
                                showVideoPreview = false
                                await viewModel.loadVideo(from: newItem)
                            }
                        }
                        
                        // Upload Progress
                        if viewModel.isUploading {
                            LiquidGlassCard(
                                content: {
                                    HStack(spacing: 12) {
                                        ProgressView()
                                            .progressViewStyle(CircularProgressViewStyle(tint: .fairwayGreen))
                                        Text("Uploading video...")
                                            .font(.subheadline)
                                            .foregroundColor(.glassSecondaryText)
                                    }
                                    .padding()
                                    .frame(maxWidth: .infinity)
                                },
                                cornerRadius: 12,
                                glassIntensity: .light
                            )
                            .padding(.horizontal)
                            .depthLayer(level: .raised)
                        }
                        
                        // Analyze Button
                        if viewModel.selectedVideoURL != nil && !viewModel.isUploading {
                            Button(action: {
                                Task {
                                    LiquidGlassHaptics.impact(.medium)
                                    await viewModel.uploadVideo()
                                }
                            }) {
                                HStack {
                                    Image(systemName: "waveform.badge.magnifyingglass")
                                        .font(.system(size: 20))
                                    Text("Analyze Swing")
                                        .fontWeight(.semibold)
                                }
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
                            .padding(.horizontal)
                            .depthLayer(level: .elevated)
                        }
                        
                        // View Analysis Results Button
                        if let analysisResult = viewModel.analysisResult {
                            NavigationLink(destination: AnalysisResultView(result: analysisResult)) {
                                HStack {
                                    Image(systemName: "chart.line.text.clipboard")
                                        .font(.system(size: 20))
                                    Text("View Analysis Results")
                                        .fontWeight(.medium)
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .font(.system(size: 14, weight: .semibold))
                                }
                                .foregroundColor(.glassText)
                                .padding(.horizontal, 20)
                                .padding(.vertical, 16)
                                .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.plain)
                            .liquidGlassBackground(intensity: .medium, cornerRadius: 16)
                            .depthLayer(level: .raised)
                            .padding(.horizontal)
                        }
                    }
                    
                    // Tips Section
                    if viewModel.selectedVideoURL == nil {
                        LiquidGlassCard(
                            content: {
                                VStack(alignment: .leading, spacing: 12) {
                                    HStack {
                                        Image(systemName: "lightbulb.fill")
                                            .font(.title3)
                                            .foregroundColor(.fairwayGreen)
                                        Text("Quick Tips")
                                            .font(.headline)
                                            .foregroundColor(.glassText)
                                    }
                                    
                                    VStack(alignment: .leading, spacing: 8) {
                                        TipRow(icon: "camera.fill", text: "Record from down-the-line view")
                                        TipRow(icon: "figure.golf", text: "Include full swing in frame")
                                        TipRow(icon: "sun.max.fill", text: "Ensure good lighting")
                                    }
                                }
                                .padding()
                            },
                            cornerRadius: 16,
                            glassIntensity: .ultraLight
                        )
                        .padding(.horizontal)
                    }
                    
                    Spacer(minLength: 20)
                }
                .padding(.vertical)
            }
            .background(Color.glassBackground.ignoresSafeArea())
            .navigationTitle("Swing Analysis")
            .navigationBarTitleDisplayMode(.large)
            .liquidGlassNavigationBar()
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK") { 
                    LiquidGlassHaptics.impact(.light)
                }
            } message: {
                Text(viewModel.errorMessage)
            }
        }
    }
}

// Helper view for tips
struct TipRow: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(.glassSecondaryText)
                .frame(width: 20)
            Text(text)
                .font(.subheadline)
                .foregroundColor(.glassSecondaryText)
        }
    }
}

#Preview {
    ContentView()
}
