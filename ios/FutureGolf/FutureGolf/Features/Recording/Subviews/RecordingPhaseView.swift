import SwiftUI

struct RecordingPhaseView: View {
    @ObservedObject var viewModel: RecordingViewModel
    
    var body: some View {
        VStack(spacing: 24) {
            Text("\(viewModel.swingCount) of \(viewModel.targetSwingCount) swings")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(.ultraThinMaterial, in: Capsule())
        }
        .animation(.spring(response: 0.5, dampingFraction: 0.8), value: viewModel.swingCount)
    }
}
