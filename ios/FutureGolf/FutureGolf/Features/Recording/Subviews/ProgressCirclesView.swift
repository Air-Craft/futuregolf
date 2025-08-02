import SwiftUI

struct ProgressCirclesView: View {
    let circles: [ProgressCircle]
    
    var body: some View {
        HStack(spacing: 16) {
            ForEach(Array(circles.enumerated()), id: \.element.id) { index, circle in
                ZStack {
                    Circle()
                        .fill(circle.isCompleted ? Color.green : Color.white.opacity(0.3))
                        .frame(width: 50, height: 50)
                    
                    if circle.isCompleted {
                        Image(systemName: "checkmark")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .scaleEffect(circle.isCompleted ? 1 : 0)
                            .animation(.spring(response: 0.4, dampingFraction: 0.6), value: circle.isCompleted)
                    } else {
                        Text("\(index + 1)")
                            .font(.title2)
                            .fontWeight(.semibold)
                            .foregroundColor(.white)
                    }
                }
                .scaleEffect(circle.isCompleted ? 1.1 : 1.0)
                .animation(.spring(response: 0.3, dampingFraction: 0.7), value: circle.isCompleted)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
    }
}
