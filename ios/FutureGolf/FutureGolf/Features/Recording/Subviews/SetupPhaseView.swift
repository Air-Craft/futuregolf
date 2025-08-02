import SwiftUI

struct SetupPhaseView: View {
    @ObservedObject var viewModel: RecordingViewModel
    
    var body: some View {
        VStack(spacing: 32) {
            if viewModel.showPositioningIndicator {
                PositioningIndicatorView(isLeftHanded: viewModel.isLeftHandedMode)
                    .transition(.opacity.combined(with: .scale))
            }
            
            VStack(spacing: 16) {
                Text("Position yourself in frame")
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                    .multilineTextAlignment(.center)
                
                Text("Say \"begin\" when you're ready to start recording")
                    .font(.body)
                    .foregroundColor(.white.opacity(0.8))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
            .liquidGlassBackground(intensity: .medium, cornerRadius: 16)
            .padding(.horizontal)
        }
    }
}

