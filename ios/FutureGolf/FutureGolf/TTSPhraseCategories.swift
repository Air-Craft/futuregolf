
import Foundation
import CryptoKit

/// Categories of TTS phrases
enum TTSPhraseCategory: String, CaseIterable {
    case recordingJourney = "recording"
    case analysisResults = "analysis"
    case generalUI = "ui"
}

/// Protocol for cacheable TTS phrases
protocol TTSCacheablePhrase {
    var id: String { get }
    var text: String { get }
    var category: TTSPhraseCategory { get }
    var priority: Int { get } // Lower number = higher priority
}

extension TTSCacheablePhrase {
    /// Generate a unique hash for this phrase text
    var hash: String {
        let data = text.data(using: .utf8) ?? Data()
        let digest = SHA256.hash(data: data)
        return digest.compactMap { String(format: "%02x", $0) }.joined()
    }
    
    /// Expected filename for the cached audio
    var filename: String {
        return "\(hash).mp3"
    }
}

/// Recording journey phrases
struct RecordingPhrase: TTSCacheablePhrase {
    let id: String
    let text: String
    let category: TTSPhraseCategory = .recordingJourney
    let priority: Int
    
    // Static phrases for recording journey
    static let setupPositioning = RecordingPhrase(
        id: "setup_positioning",
        text: "Alright. Get yourself into a position where we can see your whole swing, and let me know when you're ready.",
        priority: 1
    )
    
    static let recordingStarted = RecordingPhrase(
        id: "recording_started",
        text: "Great. I'm now recording. Begin swinging when you're ready.",
        priority: 1
    )
    
    static let firstSwingDone = RecordingPhrase(
        id: "first_swing_done",
        text: "Great. Take another when you're ready.",
        priority: 2
    )
    
    static let secondSwingDone = RecordingPhrase(
        id: "second_swing_done",
        text: "Ok one more to go.",
        priority: 2
    )
    
    static let recordingComplete = RecordingPhrase(
        id: "recording_complete",
        text: "That's great. I'll get to work analyzing your swings.",
        priority: 1
    )
    
    static let recordingTimeout = RecordingPhrase(
        id: "recording_timeout",
        text: "That's taken longer than I had planned. I'll analyze what we have.",
        priority: 3
    )
    
    static var allPhrases: [RecordingPhrase] {
        return [setupPositioning, recordingStarted, firstSwingDone, secondSwingDone, recordingComplete, recordingTimeout]
    }
}

/// Analysis result phrases (can be dynamic)
struct AnalysisPhrase: TTSCacheablePhrase {
    let id: String
    let text: String
    let category: TTSPhraseCategory = .analysisResults
    let priority: Int
    
    // Common analysis phrases
    static let analysisComplete = AnalysisPhrase(
        id: "analysis_complete",
        text: "Your swing analysis is complete. Let me walk you through the results.",
        priority: 1
    )
    
    static let overallGood = AnalysisPhrase(
        id: "overall_good",
        text: "Overall, you have a solid swing with good fundamentals.",
        priority: 2
    )
    
    static let needsImprovement = AnalysisPhrase(
        id: "needs_improvement",
        text: "There are a few areas we can work on to improve your swing.",
        priority: 2
    )
    
    static func keyMomentPhrase(for phaseName: String) -> AnalysisPhrase {
        return AnalysisPhrase(
            id: "key_moment_\(phaseName.lowercased().replacingOccurrences(of: " ", with: "_"))",
            text: "Let's look at your \(phaseName.lowercased()).",
            priority: 3
        )
    }
    
    static var commonPhrases: [AnalysisPhrase] {
        return [analysisComplete, overallGood, needsImprovement]
    }
}

/// Manager for all TTS phrases
class TTSPhraseManager {
    static let shared = TTSPhraseManager()
    
    private var cachedPhrases: [String: any TTSCacheablePhrase] = [:]
    
    init() {
        // Register all static phrases
        registerStaticPhrases()
    }
    
    private func registerStaticPhrases() {
        // Register recording phrases
        for phrase in RecordingPhrase.allPhrases {
            cachedPhrases[phrase.text] = phrase
        }
        
        // Register common analysis phrases
        for phrase in AnalysisPhrase.commonPhrases {
            cachedPhrases[phrase.text] = phrase
        }
    }
    
    /// Register a new phrase for caching
    func registerPhrase(_ phrase: any TTSCacheablePhrase) {
        cachedPhrases[phrase.text] = phrase
    }
    
    /// Get phrase by text
    func phraseFor(text: String) -> (any TTSCacheablePhrase)? {
        return cachedPhrases[text]
    }
    
    /// Check if text is cacheable
    func isCacheable(text: String) -> Bool {
        return cachedPhrases[text] != nil
    }
    
    /// Get all phrases sorted by priority
    func getAllPhrases() -> [any TTSCacheablePhrase] {
        return Array(cachedPhrases.values).sorted { $0.priority < $1.priority }
    }
    
    /// Get phrases by category
    func getPhrases(for category: TTSPhraseCategory) -> [any TTSCacheablePhrase] {
        return cachedPhrases.values
            .filter { $0.category == category }
            .sorted { $0.priority < $1.priority }
    }
    
    /// Pre-cache analysis phrases from analysis result
    func registerAnalysisPhrases(from result: AnalysisResult) {
        // Cache phrases for each swing phase
        for phase in result.swingPhases {
            let phrase = AnalysisPhrase.keyMomentPhrase(for: phase.name)
            registerPhrase(phrase)
            
            // Also cache the feedback text
            let feedbackPhrase = AnalysisPhrase(
                id: "feedback_\(phase.name.lowercased().replacingOccurrences(of: " ", with: "_"))",
                text: phase.feedback,
                priority: 4
            )
            registerPhrase(feedbackPhrase)
        }
        
        // Cache the overall analysis
        let overallPhrase = AnalysisPhrase(
            id: "overall_analysis",
            text: result.overallAnalysis,
            priority: 2
        )
        registerPhrase(overallPhrase)
        
        // Cache key points
        for (index, point) in result.keyPoints.enumerated() {
            let pointPhrase = AnalysisPhrase(
                id: "key_point_\(index)",
                text: point,
                priority: 5
            )
            registerPhrase(pointPhrase)
        }
    }
}

// MARK: - Updated Cache Metadata

/// Generic cached phrase metadata
struct GenericCachedPhrase: Codable {
    let hash: String
    let text: String
    let filename: String
    let size: Int64
    let created: Date
    let category: String
    let priority: Int
    
    init(phrase: any TTSCacheablePhrase, size: Int64) {
        self.hash = phrase.hash
        self.text = phrase.text
        self.filename = phrase.filename
        self.size = size
        self.created = Date()
        self.category = phrase.category.rawValue
        self.priority = phrase.priority
    }
}
