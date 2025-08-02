import SwiftUI

struct ProcessingView: View {
    @ObservedObject var viewModel: SwingAnalysisViewModel
    
    var body: some View {
        VStack(spacing: 24) {
            // Video Thumbnail with loading/error states and overlays
            ZStack {
                if let thumbnail = viewModel.videoThumbnail {
                    Image(uiImage: thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(height: 250)
                } else {
                    Rectangle()
                        .fill(Color.gray.opacity(0.3))
                        .frame(height: 250)
                }
                
                // Overlay based on analysis state (only show if we have thumbnail or it failed to load)
                if viewModel.isOffline || viewModel.isLoading || !viewModel.isAnalysisTTSReady {
                    // Busy indicator while waiting for analysis
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(1.5)
                        .background(
                            Circle()
                                .fill(Color.black.opacity(0.6))
                                .frame(width: 60, height: 60)
                        )
                } else if viewModel.analysisResult != nil && viewModel.isAnalysisTTSReady {
                    // Play button when TTS is ready
                    Button(action: {
                        // showVideoPlayer = true
                        // LiquidGlassHaptics.impact(.medium)
                    }) {
                        Image(systemName: "play.circle.fill")
                            .font(.system(size: 70))
                            .foregroundColor(.white)
                            .background(
                                Circle()
                                    .fill(Color.black.opacity(0.3))
                                    .blur(radius: 10)
                            )
                    }
                }
            }
            .padding(.horizontal)
            
            // Processing Status
            HStack(spacing: 12) {
                if viewModel.isLoading && !viewModel.isOffline {
                    ProgressView()
                        .scaleEffect(0.8)
                }
                
                Text(viewModel.processingStatus)
                    .font(.headline)
                    .foregroundColor(.primary)
            }
            .padding(.horizontal)
            
            // Progress Bar
            VStack(alignment: .leading, spacing: 8) {
                ProgressView(value: viewModel.isOffline ? 0.0 : viewModel.processingProgress)
                    .tint(viewModel.isOffline ? .gray : .fairwayGreen)
                    .scaleEffect(y: 2)
                    .animation(.liquidGlassSmooth, value: viewModel.processingProgress)
                
                Text(viewModel.processingDetail)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal)
            
            Spacer()
        }
        .padding(.top)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
