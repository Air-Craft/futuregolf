import Foundation

struct AnalysisResult: Identifiable, Equatable {
    let id: String
    let status: String
    let swingPhases: [SwingPhase]
    let keyPoints: [String]
    let overallAnalysis: String
    let coachingScript: String
    
    // Metrics for display
    let swingSpeed: Int
    let tempo: String
    let balance: Int
}

struct SwingPhase: Identifiable, Equatable {
    let id = UUID()
    let name: String
    let timestamp: Double
    let description: String
    let feedback: String
}