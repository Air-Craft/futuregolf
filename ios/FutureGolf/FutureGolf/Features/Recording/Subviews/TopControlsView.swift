import SwiftUI

struct TopControlsView: View {
    @ObservedObject var viewModel: RecordingViewModel
    var onCancel: () -> Void
    
    var body: some View {
        HStack {
            Button(action: onCancel) {
                Image(systemName: "xmark")
                    .font(.title2)
                    .foregroundColor(.white)
                    .frame(width: 44, height: 44)
                    .background(.ultraThinMaterial, in: Circle())
            }
            .accessibilityIdentifier("Cancel")
            .accessibilityLabel("Cancel recording")
            
            Spacer()
            
            if viewModel.currentPhase == .setup {
                Button(action: {
                    withAnimation(.spring(response: 0.3)) {
                        viewModel.switchCamera()
                    }
                    LiquidGlassHaptics.impact(.light)
                }) {
                    Image(systemName: "camera.rotate")
                        .font(.title2)
                        .foregroundColor(.white)
                        .frame(width: 44, height: 44)
                        .background(.ultraThinMaterial, in: Circle())
                }
                .accessibilityIdentifier("Switch Camera")
                .accessibilityLabel("Switch between front and rear camera")
            }
        }
    }
}
