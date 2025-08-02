import SwiftUI

struct OverviewSectionView: View {
    @ObservedObject var viewModel: SwingAnalysisViewModel
    
    var body: some View {
        LiquidGlassCard(glassIntensity: .medium) {
            VStack(spacing: 16) {
                // Stats Row
                HStack(spacing: 0) {
                    statItem(
                        title: "Overall Score",
                        value: viewModel.overallScore,
                        icon: "star.fill",
                        color: .yellow
                    )
                    
                    Divider()
                        .frame(height: 40)
                        .padding(.horizontal)
                    
                    statItem(
                        title: "Avg Head Speed",
                        value: viewModel.avgHeadSpeed,
                        icon: "speedometer",
                        color: .fairwayGreen
                    )
                }
                
                Divider()
                
                // Compliment and Critique
                VStack(spacing: 12) {
                    feedbackItem(
                        text: viewModel.topCompliment,
                        icon: "checkmark.circle.fill",
                        color: .fairwayGreen
                    )
                    
                    feedbackItem(
                        text: viewModel.topCritique,
                        icon: "exclamationmark.triangle.fill",
                        color: .orange
                    )
                }
            }
            .padding()
        }
        .padding(.horizontal)
    }
    
    private func statItem(title: String, value: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
            Text(value)
                .font(.title)
                .fontWeight(.bold)
                .foregroundColor(.glassText)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.glassSecondaryText)
        }
        .frame(maxWidth: .infinity)
    }
    
    private func feedbackItem(text: String, icon: String, color: Color) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundColor(color)
            
            Text(text)
                .font(.subheadline)
                .foregroundColor(.glassText)
                .multilineTextAlignment(.leading)
            
            Spacer()
        }
    }
}
