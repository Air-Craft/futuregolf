import SwiftUI
import Foundation

struct TimeDisplayView: View {
    var recordingTime: TimeInterval
    
    var body: some View {
        VStack(spacing: 8) {
            Text(formatTime(recordingTime))
                .font(.system(size: 32, weight: .medium, design: .monospaced))
                .foregroundColor(.white)
            
            Text("Recording Time")
                .font(.caption)
                .foregroundColor(.white.opacity(0.7))
                .textCase(.uppercase)
                .tracking(1)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        let milliseconds = Int((time.truncatingRemainder(dividingBy: 1)) * 100)
        return String(format: "%02d:%02d.%02d", minutes, seconds, milliseconds)
    }
}
