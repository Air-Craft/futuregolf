import SwiftUI

struct ProcessingPhaseView: View {
    @ObservedObject var viewModel: RecordingViewModel
    
    var body: some View {
        VStack(spacing: 24) {
            ZStack {
                Circle()
                    .stroke(Color.white.opacity(0.3), lineWidth: 6)
                    .frame(width: 80, height: 80)
                
                Circle()
                    .trim(from: 0, to: 0.7)
                    .stroke(
                        LinearGradient(
                            colors: [.white, .white.opacity(0.5)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        style: StrokeStyle(lineWidth: 6, lineCap: .round)
                    )
                    .frame(width: 80, height: 80)
                    .rotationEffect(.degrees(-90))
                    .animation(
                        .linear(duration: 2)
                        .repeatForever(autoreverses: false),
                        value: viewModel.currentPhase == .processing
                    )
                
                Image(systemName: "figure.golf")
                    .font(.title)
                    .foregroundColor(.white)
            }
            
            Text("Processing your swings...")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.white)
            
            Text("This may take a moment")
                .font(.body)
                .foregroundColor(.white.opacity(0.8))
        }
        .liquidGlassBackground(intensity: .medium, cornerRadius: 16)
        .padding(.horizontal)
    }
}
