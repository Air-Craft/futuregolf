import Foundation

struct AnalysisResult: Identifiable, Equatable, Codable {
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

struct SwingPhase: Identifiable, Equatable, Codable {
    let id: UUID
    let name: String
    let timestamp: Double
    let description: String
    let feedback: String
    
    init(name: String, timestamp: Double, description: String, feedback: String) {
        self.id = UUID()
        self.name = name
        self.timestamp = timestamp
        self.description = description
        self.feedback = feedback
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        self.name = try container.decode(String.self, forKey: .name)
        self.timestamp = try container.decode(Double.self, forKey: .timestamp)
        self.description = try container.decode(String.self, forKey: .description)
        self.feedback = try container.decode(String.self, forKey: .feedback)
    }
    
    enum CodingKeys: String, CodingKey {
        case id, name, timestamp, description, feedback
    }
}