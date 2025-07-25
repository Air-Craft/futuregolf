import SwiftUI

struct PreviousAnalysesView: View {
    @State private var analyses: [AnalysisResult] = []
    
    var body: some View {
        NavigationStack {
            List(analyses) { analysis in
                NavigationLink(destination: AnalysisResultView(result: analysis)) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Analysis \(analysis.id.prefix(8))")
                            .font(.headline)
                        Text(analysis.keyPoints.first ?? "No key points")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(2)
                    }
                    .padding(.vertical, 4)
                }
            }
            .navigationTitle("Previous Analyses")
            .overlay {
                if analyses.isEmpty {
                    ContentUnavailableView(
                        "No Analyses Yet",
                        systemImage: "clock.arrow.circlepath",
                        description: Text("Your previous golf swing analyses will appear here")
                    )
                }
            }
        }
    }
}

#Preview {
    PreviousAnalysesView()
}