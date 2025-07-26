import SwiftUI

struct AnalysisResultView: View {
    let result: AnalysisResult
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Golf Swing Analysis")
                    .font(.largeTitle)
                    .bold()
                    .padding(.horizontal)
                
                VStack(alignment: .leading, spacing: 16) {
                    Text("Overall Analysis")
                        .font(.headline)
                    
                    Text(result.overallAnalysis)
                        .font(.body)
                        .padding()
                        .background(.regularMaterial)
                        .backgroundStyle(.quaternary)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                }
                .padding(.horizontal)
                
                VStack(alignment: .leading, spacing: 16) {
                    Text("Key Points")
                        .font(.headline)
                    
                    ForEach(result.keyPoints, id: \.self) { point in
                        HStack(alignment: .top) {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text(point)
                                .font(.body)
                        }
                        .padding(.vertical, 4)
                    }
                }
                .padding(.horizontal)
                
                VStack(alignment: .leading, spacing: 16) {
                    Text("Swing Phases")
                        .font(.headline)
                    
                    ForEach(result.swingPhases, id: \.name) { phase in
                        VStack(alignment: .leading, spacing: 8) {
                            Text(phase.name)
                                .font(.subheadline)
                                .bold()
                            
                            Text("Frames: \(phase.startFrame) - \(phase.endFrame)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            
                            ForEach(phase.keyObservations, id: \.self) { observation in
                                Text("• \(observation)")
                                    .font(.body)
                                    .padding(.leading)
                            }
                        }
                        .padding()
                        .background(.thinMaterial)
                        .backgroundStyle(.blue)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    }
                }
                .padding(.horizontal)
                
                VStack(alignment: .leading, spacing: 16) {
                    Text("Coaching Feedback")
                        .font(.headline)
                    
                    Text(result.coachingScript)
                        .font(.body)
                        .padding()
                        .background(.ultraThinMaterial)
                        .backgroundStyle(.purple)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                }
                .padding(.horizontal)
                .padding(.bottom)
            }
        }
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationStack {
        AnalysisResultView(result: AnalysisResult(
            id: "123",
            status: "completed",
            swingPhases: [
                SwingPhase(
                    name: "Backswing",
                    startFrame: 10,
                    endFrame: 45,
                    keyObservations: ["Good rotation", "Maintains spine angle"]
                )
            ],
            keyPoints: ["Great tempo", "Good balance throughout swing"],
            overallAnalysis: "Your golf swing shows excellent fundamentals with room for minor improvements.",
            coachingScript: "Let's work on your follow-through to maximize distance."
        ))
    }
}