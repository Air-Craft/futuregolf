import SwiftUI

struct ProgressToastView: View {
    let progress: Double
    let message: String
    
    var body: some View {
        HStack(spacing: 12) {
            // Progress indicator
            ZStack {
                Circle()
                    .stroke(Color.white.opacity(0.3), lineWidth: 3)
                    .frame(width: 30, height: 30)
                
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(Color.fairwayGreen, style: StrokeStyle(lineWidth: 3, lineCap: .round))
                    .frame(width: 30, height: 30)
                    .rotationEffect(.degrees(-90))
                    .animation(.liquidGlassSmooth, value: progress)
                
                Text("\(Int(progress * 100))%")
                    .font(.caption2)
                    .fontWeight(.medium)
                    .foregroundColor(.white)
            }
            
            // Message
            Text(message)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(.white)
                .lineLimit(1)
            
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .liquidGlassBackground(intensity: .heavy, cornerRadius: 25, specularHighlight: true)
        .depthLayer(level: .floating)
        .padding(.horizontal)
        .padding(.bottom, 50)
    }
}

// MARK: - Error View
struct SwingAnalysisErrorView: View {
    let error: Error
    let onRetry: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 50))
                .foregroundColor(.orange)
            
            Text("Analysis Error")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.glassText)
            
            Text(error.localizedDescription)
                .font(.body)
                .foregroundColor(.glassSecondaryText)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            Button(action: onRetry) {
                HStack {
                    Image(systemName: "arrow.clockwise")
                    Text("Retry Analysis")
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding(.horizontal, 24)
                .padding(.vertical, 12)
            }
            .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
        }
        .padding()
        .liquidGlassBackground(intensity: .medium, cornerRadius: 20)
        .depthLayer(level: .elevated)
        .padding()
    }
}

#Preview("Progress Toast") {
    ZStack {
        Color.black
        
        VStack(spacing: 20) {
            ProgressToastView(progress: 0.3, message: "Analyzing swing...")
            ProgressToastView(progress: 0.7, message: "Processing data...")
            ProgressToastView(progress: 0.95, message: "Almost complete...")
        }
    }
}

#Preview("Error View") {
    ZStack {
        Color.gray.opacity(0.1)
        
        SwingAnalysisErrorView(
            error: NSError(domain: "Test", code: 0, userInfo: [NSLocalizedDescriptionKey: "Unable to analyze video. Please check your internet connection and try again."]),
            onRetry: {}
        )
    }
}