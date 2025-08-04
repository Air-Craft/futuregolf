import SwiftUI

struct VideoThumbnailView: View {
    @ObservedObject var viewModel: SwingAnalysisViewModel
    @Binding var showVideoPlayer: Bool
    
    private var videoThumbnailHeight: CGFloat {
        let screenWidth = UIScreen.main.bounds.width
        let padding: CGFloat = 32
        let availableWidth = screenWidth - padding
        let height = (availableWidth * 9) / 16
        
        if UIDevice.current.userInterfaceIdiom == .pad {
            return min(height, 400)
        }
        return min(height, 250)
    }
    
    var body: some View {
        Button(action: {
            showVideoPlayer = true
            LiquidGlassHaptics.impact(.medium)
        }) {
            ZStack {
                if let thumbnail = viewModel.videoThumbnail {
                    Image(uiImage: thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(height: videoThumbnailHeight)
                } else {
                    Rectangle()
                        .fill(Material.ultraThin)
                        .frame(height: videoThumbnailHeight)
                }
                
                if viewModel.videoThumbnail != nil {
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 70))
                        .foregroundColor(.white)
                        .background(
                            Circle()
                                .fill(Color.black.opacity(0.3))
                                .blur(radius: 10)
                        )
                }
            }
        }
        .disabled(viewModel.videoThumbnail == nil)
        .padding(.horizontal)
        .accessibilityLabel("Play swing analysis video")
        .accessibilityHint("Double tap to watch your swing with coaching overlay")
        .accessibilityIdentifier("playVideoButton")
    }
}
