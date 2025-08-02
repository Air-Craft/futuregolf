import SwiftUI

struct FramerateDisplayView: View {
    var frameRate: Double
    
    var body: some View {
        Text("\(Int(frameRate)) FPS")
            .font(.system(size: 12, weight: .medium, design: .monospaced))
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 6))
            .opacity(0.8)
    }
}
