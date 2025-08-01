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
    @EnvironmentObject var deps: AppDependencies
    @StateObject private var viewModel = SwingAnalysisViewModel()
    @State private var showVideoPlayer = false
    @State private var expandedSection = false
    @State private var showProgressToast = false
    @State private var showPreviousAnalyses = false
    @Environment(\.dismiss) private var dismiss
    @Environment(\.horizontalSizeClass) private var sizeClass
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    
    // For UI testing compatibility
    let overrideVideoURL: URL?
    let overrideAnalysisId: String?
    
    init(videoURL: URL? = nil, analysisId: String? = nil) {
        self.overrideVideoURL = videoURL
        self.overrideAnalysisId = analysisId
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                Color(UIColor.systemBackground)
                    .ignoresSafeArea()
                
                Group {
                    if viewModel.isLoading || viewModel.isOffline {
                        processingView
                            .transition(.opacity.combined(with: .scale))
                    } else if viewModel.analysisResult != nil {
                        analysisContentView
                            .liquidGlassTransition(isVisible: !viewModel.isLoading)
                    } else {
                        // Show processing view as default when no result yet
                        processingView
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
                
                // Use override values for UI testing, otherwise use global state
                let videoURL = overrideVideoURL ?? deps.currentRecordingURL
                let analysisId = overrideAnalysisId ?? deps.currentRecordingId
                
                print("🎬 videoURL: \(videoURL?.absoluteString ?? "nil")")
                print("🎬 analysisId: \(analysisId ?? "nil")")
                
                guard let videoURL = videoURL else {
                    assertionFailure("SwingAnalysisView presented without video URL")
                    return
                }
                
                // Pass dependencies to view model
                viewModel.dependencies = deps
                
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
            .accessibilityIdentifier("SwingAnalysisView")
            .sheet(isPresented: $showVideoPlayer) {
                if let result = viewModel.analysisResult {
                    NavigationStack {
                        VideoPlayerWithCoaching(
                            analysisResult: result,
                            videoURL: overrideVideoURL ?? deps.currentRecordingURL ?? viewModel.videoURL ?? URL(fileURLWithPath: "")
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
        // Fixed height based on 16:9 aspect ratio
        let screenWidth = UIScreen.main.bounds.width
        let padding: CGFloat = 32 // 16 on each side
        let availableWidth = screenWidth - padding
        // Calculate height for 16:9 aspect ratio
        let height = (availableWidth * 9) / 16
        
        // Cap at reasonable maximum for iPad
        if UIDevice.current.userInterfaceIdiom == .pad {
            return min(height, 400)
        }
        return min(height, 250)
    }
    
    // MARK: - Offline View
    private var offlineView: some View {
        VStack(spacing: Spacing.extraLarge) {
            // Video Thumbnail with loading/error states
            ZStack {
                if let thumbnail = viewModel.videoThumbnail {
                    Image(uiImage: thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(height: videoThumbnailHeight)
                } else if viewModel.isThumbnailLoading {
                    // Thumbnail loading state
                    VStack(spacing: 12) {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(1.2)
                        
                        if viewModel.thumbnailLoadingProgress > 0 {
                            ProgressView(value: viewModel.thumbnailLoadingProgress)
                                .tint(.white)
                                .scaleEffect(y: 1.5)
                                .frame(width: 120)
                        }
                        
                        Text("Loading thumbnail...")
                            .font(.caption)
                            .foregroundColor(.white)
                    }
                    .frame(height: videoThumbnailHeight)
                    .frame(maxWidth: .infinity)
                    .background(Color.black.opacity(0.7))
                    .cornerRadius(8)
                } else if let errorMessage = viewModel.thumbnailErrorMessage {
                    // Thumbnail error state
                    VStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.title2)
                            .foregroundColor(.orange)
                        
                        Text("Thumbnail unavailable")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Text(errorMessage)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(height: videoThumbnailHeight)
                    .frame(maxWidth: .infinity)
                    .background(Color.gray.opacity(0.1))
                    .cornerRadius(8)
                } else {
                    // Default loading state
                    Rectangle()
                        .fill(Color.gray.opacity(0.3))
                        .frame(height: videoThumbnailHeight)
                }
                
                // Always show busy indicator when offline (analysis processing)
                if viewModel.isOffline {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(1.5)
                        .background(
                            Circle()
                                .fill(Color.black.opacity(0.6))
                                .frame(width: 60, height: 60)
                        )
                }
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
            
            // Expandable Analysis Section (UI Scaffolding)
            LiquidGlassCard {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Analysis Details")
                            .font(.headline)
                            .foregroundColor(.glassText)
                        Text("Waiting for connection to analyze swing")
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
            
            // Expanded content when tapped
            if expandedSection {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Your swing video has been saved and will be analyzed as soon as connection is restored.")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .padding(.horizontal)
                    
                    // Placeholder sections
                    ForEach(["Key Points", "Technique Analysis", "Recommendations"], id: \.self) { section in
                        LiquidGlassCard {
                            VStack(alignment: .leading, spacing: 8) {
                                Text(section)
                                    .font(.headline)
                                    .foregroundColor(.glassText)
                                Text("Waiting for analysis...")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .padding()
                        }
                        .padding(.horizontal)
                        .opacity(0.6)
                    }
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
            
            Spacer()
        }
        .padding(.top)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    // MARK: - Processing View
    private var processingView: some View {
        VStack(spacing: Spacing.extraLarge) {
            // Video Thumbnail with loading/error states and overlays
            ZStack {
                if let thumbnail = viewModel.videoThumbnail {
                    Image(uiImage: thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(height: videoThumbnailHeight)
                } else if viewModel.isThumbnailLoading {
                    // Thumbnail loading state
                    VStack(spacing: 12) {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(1.2)
                        
                        if viewModel.thumbnailLoadingProgress > 0 {
                            ProgressView(value: viewModel.thumbnailLoadingProgress)
                                .tint(.white)
                                .scaleEffect(y: 1.5)
                                .frame(width: 120)
                        }
                        
                        Text("Loading thumbnail...")
                            .font(.caption)
                            .foregroundColor(.white)
                    }
                    .frame(height: videoThumbnailHeight)
                    .frame(maxWidth: .infinity)
                    .background(Color.black.opacity(0.7))
                    .cornerRadius(8)
                } else if let errorMessage = viewModel.thumbnailErrorMessage {
                    // Thumbnail error state
                    VStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.title2)
                            .foregroundColor(.orange)
                        
                        Text("Thumbnail unavailable")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Text(errorMessage)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(height: videoThumbnailHeight)
                    .frame(maxWidth: .infinity)
                    .background(Color.gray.opacity(0.1))
                    .cornerRadius(8)
                } else {
                    Rectangle()
                        .fill(Color.gray.opacity(0.3))
                        .frame(height: videoThumbnailHeight)
                }
                
                // Overlay based on analysis state (only show if we have thumbnail or it failed to load)
                if !viewModel.isThumbnailLoading {
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
                            showVideoPlayer = true
                            LiquidGlassHaptics.impact(.medium)
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
            
            // Collapsed Analysis Section
            LiquidGlassCard {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Analysis Details")
                            .font(.headline)
                            .foregroundColor(.glassText)
                        Text(viewModel.isOffline ? "Waiting for connection..." : 
                             !viewModel.isAnalysisTTSReady ? "Preparing coaching audio..." : 
                             "Processing swing data...")
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
            
            // Expanded content for processing view
            if expandedSection {
                VStack(alignment: .leading, spacing: 16) {
                    Text(viewModel.isOffline ? "Your swing will be analyzed when connection is restored." : 
                         !viewModel.isAnalysisTTSReady ? "Preparing audio for your personalized coaching session..." :
                         "Analyzing your swing technique...")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .padding(.horizontal)
                    
                    // Placeholder sections
                    ForEach(["Key Points", "Technique Analysis", "Recommendations"], id: \.self) { section in
                        LiquidGlassCard {
                            VStack(alignment: .leading, spacing: 8) {
                                Text(section)
                                    .font(.headline)
                                    .foregroundColor(.glassText)
                                Text(viewModel.isOffline ? "Waiting for connection..." : 
                                     !viewModel.isAnalysisTTSReady ? "Preparing audio..." :
                                     "Processing...")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .padding()
                        }
                        .padding(.horizontal)
                        .opacity(0.6)
                    }
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
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
                        .frame(height: videoThumbnailHeight)
                } else if viewModel.isThumbnailLoading {
                    // Thumbnail loading state (non-interactive)
                    VStack(spacing: 12) {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(1.2)
                        
                        if viewModel.thumbnailLoadingProgress > 0 {
                            ProgressView(value: viewModel.thumbnailLoadingProgress)
                                .tint(.white)
                                .scaleEffect(y: 1.5)
                                .frame(width: 120)
                        }
                        
                        Text("Loading thumbnail...")
                            .font(.caption)
                            .foregroundColor(.white)
                    }
                    .frame(height: videoThumbnailHeight)
                    .frame(maxWidth: .infinity)
                    .background(Color.black.opacity(0.7))
                    .cornerRadius(8)
                } else if let errorMessage = viewModel.thumbnailErrorMessage {
                    // Thumbnail error state
                    VStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.title2)
                            .foregroundColor(.orange)
                        
                        Text("Thumbnail unavailable")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Text(errorMessage)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(height: videoThumbnailHeight)
                    .frame(maxWidth: .infinity)
                    .background(Color.gray.opacity(0.1))
                    .cornerRadius(8)
                } else {
                    Rectangle()
                        .fill(Material.ultraThin)
                        .frame(height: videoThumbnailHeight)
                }
                
                // Play Button Overlay (only show if thumbnail is available and not loading)
                if viewModel.videoThumbnail != nil && !viewModel.isThumbnailLoading {
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
        .disabled(viewModel.videoThumbnail == nil || viewModel.isThumbnailLoading)
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
    SwingAnalysisView()
        .environmentObject(AppDependencies())
}