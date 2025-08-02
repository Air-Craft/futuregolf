import SwiftUI

struct AnalysisSectionView: View {
    @ObservedObject var viewModel: SwingAnalysisViewModel
    
    var body: some View {
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
}
