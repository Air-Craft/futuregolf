import SwiftUI
import AVKit
import AVFoundation

// MARK: - Spacing Constants
private enum Spacing {
    static let small: CGFloat = 8
    static let medium: CGFloat = 16
    static let large: CGFloat = 24
    static let extraLarge: CGFloat = 32
}

struct SwingAnalysisView: View {
    let videoURL: URL
    let analysisId: String?
    
    @StateObject private var viewModel = SwingAnalysisViewModel()
    @State private var showVideoPlayer = false
    @State private var expandedSection = false
    @State private var showProgressToast = false
    @State private var showPreviousAnalyses = false
    @Environment(\.dismiss) private var dismiss
    @Environment(\.horizontalSizeClass) private var sizeClass
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                Color(UIColor.systemBackground)
                    .ignoresSafeArea()
                
                Group {
                    if viewModel.isOffline {
                        offlineView
                            .transition(.opacity.combined(with: .scale))
                    } else if viewModel.isLoading {
                        processingView
                            .transition(.opacity.combined(with: .scale))
                    } else if viewModel.analysisResult != nil {
                        analysisContentView
                            .liquidGlassTransition(isVisible: !viewModel.isLoading)
                    } else {
                        // Show offline view as default when no result yet
                        offlineView
                            .transition(.opacity.combined(with: .scale))
                    }
                }
                .onAppear {
                    print("🎬 SwingAnalysisView: View appeared")
                    print("🎬 isOffline: \(viewModel.isOffline)")
                    print("🎬 isLoading: \(viewModel.isLoading)")
                    print("🎬 analysisResult: \(viewModel.analysisResult != nil)")
                }
            }
            .navigationTitle(viewModel.isOffline ? "Waiting for Connection" : viewModel.isLoading ? "Processing Swing" : "Swing Analysis")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: {
                        showPreviousAnalyses = true
                    }) {
                        HStack(spacing: 4) {
                            Image(systemName: "chevron.left")
                            Text("Back")
                        }
                    }
                }
                
                if !viewModel.isLoading {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button(action: {
                            // Share functionality
                        }) {
                            Image(systemName: "square.and.arrow.up")
                                .symbolRenderingMode(.hierarchical)
                        }
                    }
                }
            }
            .onAppear {
                print("🎬 SwingAnalysisView: onAppear triggered")
                print("🎬 videoURL: \(videoURL)")
                print("🎬 analysisId: \(analysisId ?? "nil")")
                
                // Always proceed - let the view model handle connectivity
                if let id = analysisId {
                    print("🎬 Loading existing analysis: \(id)")
                    viewModel.loadExistingAnalysis(id: id)
                } else {
                    print("🎬 Starting new analysis")
                    viewModel.startNewAnalysis(videoURL: videoURL)
                }
            }
            .onChange(of: viewModel.isLoading) { _, isLoading in
                if !isLoading && viewModel.analysisResult != nil {
                    // Play completion sound
                    AudioServicesPlaySystemSound(1057)
                }
            }
            .onDisappear {
                if viewModel.isLoading {
                    showProgressToast = true
                }
                viewModel.cleanup()
            }
            .sheet(isPresented: $showVideoPlayer) {
                if let result = viewModel.analysisResult {
                    NavigationStack {
                        VideoPlayerWithCoaching(
                            analysisResult: result,
                            videoURL: videoURL
                        )
                        .toolbar {
                            ToolbarItem(placement: .navigationBarTrailing) {
                                Button("Done") {
                                    showVideoPlayer = false
                                }
                            }
                        }
                    }
                }
            }
            // Progress Toast Overlay
            .overlay(alignment: .bottom) {
                if showProgressToast && viewModel.isLoading {
                    ProgressToastView(
                        progress: viewModel.processingProgress,
                        message: viewModel.processingStatus
                    )
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
            .fullScreenCover(isPresented: $showPreviousAnalyses) {
                NavigationStack {
                    PreviousAnalysesView()
                }
            }
        }
    }
    
    // MARK: - Computed Properties
    private var videoThumbnailHeight: CGFloat {
        if UIDevice.current.userInterfaceIdiom == .pad {
            return 400
        }
        return UIDevice.current.orientation.isLandscape ? 200 : 300
    }
    
    // MARK: - Offline View
    private var offlineView: some View {
        VStack(spacing: Spacing.extraLarge) {
            // Video Thumbnail
            ZStack {
                if let thumbnail = viewModel.videoThumbnail {
                    Image(uiImage: thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(maxHeight: videoThumbnailHeight)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                } else {
                    RoundedRectangle(cornerRadius: 16)
                        .fill(Material.ultraThin)
                        .frame(height: videoThumbnailHeight)
                }
                
                // Offline indicator overlay
                VStack(spacing: 16) {
                    Image(systemName: "wifi.slash")
                        .font(.system(size: 48))
                        .foregroundColor(.white)
                    
                    Text("Waiting for Connection")
                        .font(.headline)
                        .foregroundColor(.white)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.black.opacity(0.6))
                .clipShape(RoundedRectangle(cornerRadius: 16))
            }
            .padding(.horizontal)
            
            // Progress Bar at 0
            VStack(alignment: .leading, spacing: 8) {
                ProgressView(value: 0.0)
                    .tint(.gray)
                    .scaleEffect(y: 2)
                
                Text("Waiting for connectivity...")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal)
            
            // Status Message
            VStack(spacing: 8) {
                Text("Your swing will be analyzed when connection is restored")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                
                Text("We'll notify you when it's ready")
                    .font(.caption)
                    .foregroundColor(.secondary.opacity(0.8))
            }
            .padding(.horizontal)
            
            Spacer()
        }
        .padding(.vertical)
    }
    
    // MARK: - Processing View
    private var processingView: some View {
        VStack(spacing: Spacing.extraLarge) {
            // Video Thumbnail with Processing Indicator
            ZStack {
                if let thumbnail = viewModel.videoThumbnail {
                    Image(uiImage: thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(maxHeight: videoThumbnailHeight)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                        .overlay {
                            RoundedRectangle(cornerRadius: 16)
                                .fill(Color.black.opacity(0.4))
                        }
                } else {
                    RoundedRectangle(cornerRadius: 16)
                        .fill(Color.gray.opacity(0.3))
                        .frame(height: videoThumbnailHeight)
                }
                
                // Processing indicator
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                        .tint(.white)
                    
                    Text(viewModel.processingStatus)
                        .font(.headline)
                        .foregroundColor(.white)
                }
            }
            .padding(.horizontal)
            
            // Progress Bar
            VStack(alignment: .leading, spacing: 8) {
                ProgressView(value: viewModel.processingProgress)
                    .tint(.fairwayGreen)
                    .scaleEffect(y: 2)
                    .animation(.liquidGlassSmooth, value: viewModel.processingProgress)
                
                Text(viewModel.processingDetail)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal)
            
            // Collapsed Analysis Section
            LiquidGlassCard {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Analysis Details")
                            .font(.headline)
                            .foregroundColor(.glassText)
                        Text("Processing swing data...")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Image(systemName: "chevron.down.circle.fill")
                        .font(.title2)
                        .foregroundColor(.secondary)
                        .rotationEffect(.degrees(expandedSection ? 180 : 0))
                }
                .padding()
            }
            .padding(.horizontal)
            .onTapGesture {
                withAnimation(.liquidGlassSpring) {
                    expandedSection.toggle()
                }
            }
            
            Spacer()
        }
        .padding(.top)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    // MARK: - Analysis Content View
    private var analysisContentView: some View {
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
                        .frame(maxHeight: videoThumbnailHeight)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                } else {
                    RoundedRectangle(cornerRadius: 16)
                        .fill(Material.ultraThin)
                        .frame(height: videoThumbnailHeight)
                }
                
                // Play Button Overlay
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
                LazyHStack(spacing: Spacing.medium) {
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

// MARK: - Key Moment Card
struct KeyMomentCard: View {
    let moment: KeyMoment
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Thumbnail
            if let image = moment.thumbnail {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 200, height: 150)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            } else {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Material.ultraThin)
                    .frame(width: 200, height: 150)
            }
            
            // Text Content
            VStack(alignment: .leading, spacing: 4) {
                Text(moment.phaseName)
                    .font(.headline)
                    .foregroundColor(.glassText)
                
                Text(moment.feedback)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
            }
            .padding(.horizontal, 8)
            .padding(.bottom, 8)
        }
        .frame(width: 200)
        .liquidGlassBackground(intensity: .light, cornerRadius: 16)
    }
}

// MARK: - Data Models
struct KeyMoment: Identifiable {
    let id = UUID()
    let phaseName: String
    let timestamp: Double
    let thumbnail: UIImage?
    let feedback: String
}


// MARK: - Preview
#Preview {
    SwingAnalysisView(
        videoURL: URL(fileURLWithPath: "/path/to/video.mp4"),
        analysisId: nil
    )
}