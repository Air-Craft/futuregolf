import SwiftUI

struct AnalysisContentView: View {
    @ObservedObject var viewModel: SwingAnalysisViewModel
    @Binding var showVideoPlayer: Bool
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Video Thumbnail
                videoThumbnailSection
                
                // Overview Box
                overviewSection
                
                // Analysis Section
                analysisSection
                
                // Summary Box
                summarySection
            }
            .padding(.bottom, 40)
        }
    }
    
    // MARK: - Video Thumbnail Section
    private var videoThumbnailSection: some View {
        Button(action: {
            showVideoPlayer = true
            LiquidGlassHaptics.impact(.medium)
        }) {
            ZStack {
                if let thumbnail = viewModel.videoThumbnail {
                    Image(uiImage: thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(height: 250)
                } else {
                    Rectangle()
                        .fill(Material.ultraThin)
                        .frame(height: 250)
                }
                
                // Play Button Overlay (only show if thumbnail is available and not loading)
                if viewModel.videoThumbnail != nil {
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
        .disabled(viewModel.videoThumbnail == nil)
        .padding(.horizontal)
        .accessibilityLabel("Play swing analysis video")
        .accessibilityHint("Double tap to watch your swing with coaching overlay")
        .accessibilityIdentifier("VideoThumbnail")
    }
    
    // MARK: - Overview Section
    private var overviewSection: some View {
        LiquidGlassCard(glassIntensity: .medium) {
            VStack(spacing: 16) {
                // Stats Row
                HStack(spacing: 0) {
                    statItem(
                        title: "Overall Score",
                        value: viewModel.overallScore,
                        icon: "star.fill",
                        color: .yellow
                    )
                    
                    Divider()
                        .frame(height: 40)
                        .padding(.horizontal)
                    
                    statItem(
                        title: "Avg Head Speed",
                        value: viewModel.avgHeadSpeed,
                        icon: "speedometer",
                        color: .fairwayGreen
                    )
                }
                
                Divider()
                
                // Compliment and Critique
                VStack(spacing: 12) {
                    feedbackItem(
                        text: viewModel.topCompliment,
                        icon: "checkmark.circle.fill",
                        color: .fairwayGreen
                    )
                    
                    feedbackItem(
                        text: viewModel.topCritique,
                        icon: "exclamationmark.triangle.fill",
                        color: .orange
                    )
                }
            }
            .padding()
        }
        .padding(.horizontal)
    }
    
    // MARK: - Analysis Section
    private var analysisSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Key Moments")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.glassText)
                .padding(.horizontal)
            
            ScrollView(.horizontal, showsIndicators: false) {
                LazyHStack(spacing: 16) {
                    ForEach(viewModel.keyMoments) { moment in
                        KeyMomentCard(moment: moment)
                    }
                }
                .padding(.horizontal)
            }
        }
    }
    
    // MARK: - Summary Section
    private var summarySection: some View {
        LiquidGlassCard(glassIntensity: .light) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Analysis Summary")
                    .font(.headline)
                    .foregroundColor(.glassText)
                
                Text(viewModel.summaryText)
                    .font(.body)
                    .foregroundColor(.secondary)
                    .lineSpacing(4)
            }
            .padding()
        }
        .padding(.horizontal)
    }
    
    // MARK: - Helper Views
    private func statItem(title: String, value: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
            Text(value)
                .font(.title)
                .fontWeight(.bold)
                .foregroundColor(.glassText)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.glassSecondaryText)
        }
        .frame(maxWidth: .infinity)
    }
    
    private func feedbackItem(text: String, icon: String, color: Color) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundColor(color)
            
            Text(text)
                .font(.subheadline)
                .foregroundColor(.glassText)
                .multilineTextAlignment(.leading)
            
            Spacer()
        }
    }
}
