import SwiftUI

struct ZoomIndicatorView: View {
    let zoomLevel: CGFloat
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "minus.magnifyingglass")
                .font(.system(size: 14))
            
            Text(String(format: "%.1fx", zoomLevel))
                .font(.system(size: 16, weight: .medium, design: .monospaced))
            
            Image(systemName: "plus.magnifyingglass")
                .font(.system(size: 14))
        }
        .foregroundColor(.white)
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
    }
}
