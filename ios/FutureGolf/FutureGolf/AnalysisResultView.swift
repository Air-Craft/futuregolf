import SwiftUI

struct AnalysisResultView: View {
    let result: AnalysisResult
    @State private var selectedPhaseIndex: Int = 0
    @State private var showContent = false
    @State private var showVideoPlayer = false
    
    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Simple header
                VStack(spacing: 16) {
                    Text("Golf Swing Analysis")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("Overall Score: \(calculateOverallScore())")
                        .font(.headline)
                        .foregroundColor(.green)
                }
                .padding()
                .background(Color.black.opacity(0.7), in: RoundedRectangle(cornerRadius: 16))
                
                // Simple video button
                Button(action: {
                    showVideoPlayer = true
                }) {
                    HStack {
                        Image(systemName: "play.circle.fill")
                            .font(.title2)
                        Text("Watch Video with Coaching")
                            .font(.headline)
                        Spacer()
                    }
                    .padding()
                    .background(Color.blue.opacity(0.7), in: RoundedRectangle(cornerRadius: 12))
                    .foregroundColor(.white)
                }
                
                // Simple metrics
                VStack(alignment: .leading, spacing: 12) {
                    Text("Metrics")
                        .font(.headline)
                    
                    VStack(spacing: 8) {
                        HStack {
                            Text("Club Speed:")
                            Spacer()
                            Text("\(result.swingSpeed) mph")
                        }
                        HStack {
                            Text("Tempo:")
                            Spacer()
                            Text(result.tempo)
                        }
                        HStack {
                            Text("Balance:")
                            Spacer()
                            Text("\(result.balance)%")
                        }
                    }
                    .padding()
                    .background(Color.gray.opacity(0.3), in: RoundedRectangle(cornerRadius: 12))
                }
                .padding(.horizontal)
            }
        }
        .background(Color.black)
        .foregroundColor(.white)
        .sheet(isPresented: $showVideoPlayer) {
            NavigationStack {
                if let videoURL = Bundle.main.url(forResource: "home_bg_video", withExtension: "mp4") {
                    VideoPlayerWithCoaching(
                        analysisResult: result,
                        videoURL: videoURL
                    )
                    .toolbar {
                        ToolbarItem(placement: .navigationBarLeading) {
                            Button("Done") {
                                showVideoPlayer = false
                            }
                        }
                    }
                }
            }
        }
    }
    
    private func calculateOverallScore() -> Int {
        let speedScore = min(100, result.swingSpeed * 100 / 120)
        let balanceScore = result.balance
        let tempoScore = result.tempo == "3:1" ? 100 : 85
        return (speedScore + balanceScore + tempoScore) / 3
    }
}

#Preview {
    AnalysisResultView(result: AnalysisResult(
        id: "123",
        status: "completed",
        swingPhases: [],
        keyPoints: ["Great tempo", "Good balance"],
        overallAnalysis: "Excellent fundamentals",
        coachingScript: "Keep up the good work",
        swingSpeed: 92,
        tempo: "3:1",
        balance: 88
    ))
}
