import SwiftUI

struct DebugIconView: View {
    @State private var showDebugPanel = false
    
    var body: some View {
        if Config.isDebugPanelEnabled {
            VStack {
                Spacer()
                HStack {
                    Spacer()
                    Button(action: {
                        showDebugPanel = true
                    }) {
                        Image(systemName: "ladybug.fill")
                            .font(.title3)
                            .foregroundColor(.white)
                            .padding(10)
                            .background(Color.red.opacity(0.8))
                            .clipShape(Circle())
                            .shadow(radius: 4)
                    }
                    .padding()
                }
            }
            .sheet(isPresented: $showDebugPanel) {
                DebugPanelView()
            }
        }
    }
}

// MARK: - View Extension for Easy Integration

extension View {
    func debugIcon() -> some View {
        self.overlay(alignment: .bottomTrailing) {
            DebugIconView()
        }
    }
}

#Preview {
    Color.gray
        .debugIcon()
}