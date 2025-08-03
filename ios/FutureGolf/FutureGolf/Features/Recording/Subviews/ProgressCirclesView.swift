import SwiftUI

struct ProgressCirclesView: View {
    let swingCount: Int
    let targetSwingCount: Int
    
    var body: some View {
        HStack(spacing: 16) {
            ForEach(0..<targetSwingCount, id: \.self) { index in
                let isCompleted = index < swingCount
                
                ZStack {
                    Circle()
                        .fill(isCompleted ? Color.green : Color.white.opacity(0.3))
                        .frame(width: 50, height: 50)
                    
                    if isCompleted {
                        Image(systemName: "checkmark")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .transition(.scale.animation(.spring(response: 0.4, dampingFraction: 0.6)))
                    } else {
                        Text("\(index + 1)")
                            .font(.title2)
                            .fontWeight(.semibold)
                            .foregroundColor(.white)
                    }
                }
                .scaleEffect(isCompleted ? 1.1 : 1.0)
                .animation(.spring(response: 0.3, dampingFraction: 0.7), value: isCompleted)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
    }
}
