import SwiftUI

struct AnalysisContentView: View {
    @ObservedObject var viewModel: SwingAnalysisViewModel
    @Binding var showVideoPlayer: Bool
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                VideoThumbnailView(viewModel: viewModel, showVideoPlayer: $showVideoPlayer)
                OverviewSectionView(viewModel: viewModel)
                AnalysisSectionView(viewModel: viewModel)
                SummarySectionView(viewModel: viewModel)
            }
            .padding(.bottom, 40)
        }
        .accessibilityIdentifier("analysisContentScrollView")
    }
}

