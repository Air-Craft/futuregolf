import SwiftUI

struct SummarySectionView: View {
    @ObservedObject var viewModel: SwingAnalysisViewModel
    
    var body: some View {
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
}
