import Foundation
import CryptoKit

/// Enumeration of all cacheable TTS phrases used in the recording journey
enum TTSPhrases: String, CaseIterable {
    case setupPositioning = "Alright. Get yourself into a position where we can see your whole swing, and let me know when you're ready."
    case recordingStarted = "Great. I'm now recording. Begin swinging when you're ready."
    case firstSwingDone = "Great. Take another when you're ready."
    case secondSwingDone = "Ok one more to go."
    case recordingComplete = "That's great. I'll get to work analyzing your swings."
    case recordingTimeout = "That's taken longer than I had planned. I'll analyze what we have."
    
    /// Unique identifier for the phrase
    var id: String {
        return "phrase_\(self.rawValue.hashValue)"
    }
    
    /// The actual text to be spoken
    var text: String {
        return self.rawValue
    }
    
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
    
    /// Get phrase by text content
    static func phraseFor(text: String) -> TTSPhrases? {
        return allCases.first { $0.text == text }
    }
    
    /// Check if a given text is a cacheable phrase
    static func isCacheable(text: String) -> Bool {
        return phraseFor(text: text) != nil
    }
}

/// Metadata structure for TTS cache
struct TTSCacheMetadata: Codable {
    let version: String
    let lastRefresh: Date
    let phrases: [String: GenericCachedPhrase]
    
    static let currentVersion = "2.0"
    
    init(phrases: [String: GenericCachedPhrase] = [:]) {
        self.version = TTSCacheMetadata.currentVersion
        self.lastRefresh = Date()
        self.phrases = phrases
    }
}

/// Individual cached phrase metadata
struct TTSCachedPhrase: Codable {
    let hash: String
    let text: String
    let filename: String
    let size: Int64
    let created: Date
    
    init(phrase: TTSPhrases, size: Int64) {
        self.hash = phrase.hash
        self.text = phrase.text
        self.filename = phrase.filename
        self.size = size
        self.created = Date()
    }
}