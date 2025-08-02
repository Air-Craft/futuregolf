import SwiftUI

struct PositioningIndicatorView: View {
    let isLeftHanded: Bool
    @State private var opacity: Double = 0.8
    
    var body: some View {
        VStack(spacing: 16) {
            golferSilhouette
            distanceGuide
        }
        .opacity(opacity)
        .onAppear {
            withAnimation(.easeInOut(duration: 2).repeatForever(autoreverses: true)) {
                opacity = 0.4
            }
        }
    }
    
    private var golferSilhouette: some View {
        ZStack {
            Image(systemName: "figure.golf")
                .font(.system(size: 100))
                .foregroundColor(.white.opacity(0.6))
                .scaleEffect(x: isLeftHanded ? -1 : 1, y: 1)
            
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.white.opacity(0.4), style: StrokeStyle(lineWidth: 2, dash: [10, 5]))
                .frame(width: 200, height: 300)
        }
    }
    
    private var distanceGuide: some View {
        VStack(spacing: 8) {
            Text("10 feet away")
                .font(.headline)
                .foregroundColor(.white)
            
            Text("Full body in frame")
                .font(.subheadline)
                .foregroundColor(.white.opacity(0.8))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 8))
    }
}
