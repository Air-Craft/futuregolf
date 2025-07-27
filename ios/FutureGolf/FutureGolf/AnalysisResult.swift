import Foundation

struct AnalysisResult: Identifiable {
    let id: String
    let status: String
    let swingPhases: [SwingPhase]
    let keyPoints: [String]
    let overallAnalysis: String
    let coachingScript: String
}