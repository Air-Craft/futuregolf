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
    @StateObject private var viewModel: SwingAnalysisViewModel
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
    
    @MainActor
    init(videoURL: URL? = nil, analysisId: String? = nil, dependencies: AppDependencies) {
        self.overrideVideoURL = videoURL
        self.overrideAnalysisId = analysisId
        _viewModel = StateObject(wrappedValue: SwingAnalysisViewModel(dependencies: dependencies))
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
                // viewModel.dependencies = deps
                
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
        ProcessingView(viewModel: viewModel)
    }
    
    // MARK: - Analysis Content View
    private var analysisContentView: some View {
        AnalysisContentView(viewModel: viewModel, showVideoPlayer: $showVideoPlayer)
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
    var thumbnail: UIImage?
    let feedback: String
}


// MARK: - Preview
#Preview {
    SwingAnalysisView(dependencies: AppDependencies())
        .environmentObject(AppDependencies())
}