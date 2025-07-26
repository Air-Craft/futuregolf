import SwiftUI

struct AboutView: View {
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    Image(systemName: "figure.golf")
                        .font(.system(size: 80))
                        .foregroundColor(.green)
                        .padding(.top)
                    
                    Text("FutureGolf")
                        .font(.largeTitle)
                        .bold()
                    
                    Text("AI-Powered Golf Swing Analysis")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    
                    VStack(alignment: .leading, spacing: 16) {
                        FeatureRow(
                            icon: "camera.viewfinder",
                            title: "Video Analysis",
                            description: "Upload your swing videos for instant AI analysis"
                        )
                        
                        FeatureRow(
                            icon: "brain",
                            title: "AI Coaching",
                            description: "Get personalized feedback powered by advanced AI"
                        )
                        
                        FeatureRow(
                            icon: "chart.line.uptrend.xyaxis",
                            title: "Track Progress",
                            description: "Monitor your improvement over time"
                        )
                        
                        FeatureRow(
                            icon: "person.2",
                            title: "Pro Comparisons",
                            description: "Compare your swing to professional golfers"
                        )
                    }
                    .padding(.horizontal)
                    
                    VStack(spacing: 8) {
                        Text("Version 1.0.0")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text("© 2025 FutureGolf")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical)
                }
            }
            .navigationTitle("About")
        }
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
    }
}

#Preview {
    AboutView()
}