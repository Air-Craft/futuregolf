import Foundation
import UIKit
import AVFoundation

// MARK: - Analysis Media Storage
/// Manages folder-based storage for analysis sessions with all associated media
@MainActor
class AnalysisMediaStorage {
    static let shared = AnalysisMediaStorage()
    
    private let documentsDirectory: URL
    private let swingAnalysesDirectory: URL
    
    private init() {
        documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        swingAnalysesDirectory = documentsDirectory.appendingPathComponent("SwingAnalyses")
        
        // Create main directory if needed
        createDirectoryIfNeeded(at: swingAnalysesDirectory)
    }
    
    // MARK: - Public Methods
    
    /// Generate a new analysis ID based on timestamp
    func generateAnalysisId() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd-HHmmss"
        formatter.timeZone = TimeZone.current
        return formatter.string(from: Date())
    }
    
    /// Create a new analysis folder and return the ID
    func createAnalysisSession(videoURL: URL) throws -> String {
        let analysisId = generateAnalysisId()
        let analysisDirectory = swingAnalysesDirectory.appendingPathComponent(analysisId)
        
        // Create directories
        try FileManager.default.createDirectory(at: analysisDirectory, withIntermediateDirectories: true)
        
        let keyframesDirectory = analysisDirectory.appendingPathComponent("keyframes")
        try FileManager.default.createDirectory(at: keyframesDirectory, withIntermediateDirectories: true)
        
        let ttsCacheDirectory = analysisDirectory.appendingPathComponent("tts_cache")
        try FileManager.default.createDirectory(at: ttsCacheDirectory, withIntermediateDirectories: true)
        
        // Copy video to analysis folder
        let destinationVideoURL = analysisDirectory.appendingPathComponent("video.mp4")
        try FileManager.default.copyItem(at: videoURL, to: destinationVideoURL)
        
        return analysisId
    }
    
    /// Get the directory URL for an analysis
    func getAnalysisDirectory(id: String) -> URL {
        return swingAnalysesDirectory.appendingPathComponent(id)
    }
    
    /// Save thumbnail for an analysis
    func saveThumbnail(analysisId: String, image: UIImage) throws {
        let analysisDirectory = getAnalysisDirectory(id: analysisId)
        let thumbnailURL = analysisDirectory.appendingPathComponent("thumbnail.jpg")
        
        guard let data = image.jpegData(compressionQuality: 0.8) else {
            throw MediaStorageError.imageConversionFailed
        }
        
        try data.write(to: thumbnailURL)
    }
    
    /// Save key frame image
    func saveKeyFrame(analysisId: String, phase: String, frameNumber: Int, image: UIImage) throws -> String {
        let analysisDirectory = getAnalysisDirectory(id: analysisId)
        let keyframesDirectory = analysisDirectory.appendingPathComponent("keyframes")
        
        let filename = "\(phase.lowercased().replacingOccurrences(of: " ", with: "_"))_\(String(format: "%03d", frameNumber)).jpg"
        let frameURL = keyframesDirectory.appendingPathComponent(filename)
        
        guard let data = image.jpegData(compressionQuality: 0.8) else {
            throw MediaStorageError.imageConversionFailed
        }
        
        try data.write(to: frameURL)
        return "keyframes/\(filename)"
    }
    
    /// Save TTS audio file
    func saveTTSAudio(analysisId: String, lineIndex: Int, audioData: Data) throws -> String {
        let analysisDirectory = getAnalysisDirectory(id: analysisId)
        let ttsCacheDirectory = analysisDirectory.appendingPathComponent("tts_cache")
        
        let filename = "coaching_line_\(lineIndex).mp3"
        let audioURL = ttsCacheDirectory.appendingPathComponent(filename)
        
        try audioData.write(to: audioURL)
        return "tts_cache/\(filename)"
    }
    
    /// Save analysis JSON
    func saveAnalysisJSON(analysisId: String, analysisResult: AnalysisResult) throws {
        let analysisDirectory = getAnalysisDirectory(id: analysisId)
        let analysisURL = analysisDirectory.appendingPathComponent("analysis.json")
        
        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        let data = try encoder.encode(analysisResult)
        try data.write(to: analysisURL)
    }
    
    /// Save complete analysis report
    func saveAnalysisReport(analysisId: String, report: AnalysisReport) throws {
        let analysisDirectory = getAnalysisDirectory(id: analysisId)
        let reportURL = analysisDirectory.appendingPathComponent("report.json")
        
        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(report)
        try data.write(to: reportURL)
    }
    
    /// Load analysis report
    func loadAnalysisReport(analysisId: String) throws -> AnalysisReport? {
        let analysisDirectory = getAnalysisDirectory(id: analysisId)
        let reportURL = analysisDirectory.appendingPathComponent("report.json")
        
        guard FileManager.default.fileExists(atPath: reportURL.path) else {
            return nil
        }
        
        let data = try Data(contentsOf: reportURL)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(AnalysisReport.self, from: data)
    }
    
    /// Get all analysis IDs sorted by date (newest first)
    func getAllAnalysisIds() -> [String] {
        do {
            let contents = try FileManager.default.contentsOfDirectory(
                at: swingAnalysesDirectory,
                includingPropertiesForKeys: [.isDirectoryKey],
                options: [.skipsHiddenFiles]
            )
            
            return contents
                .filter { url in
                    var isDirectory: ObjCBool = false
                    FileManager.default.fileExists(atPath: url.path, isDirectory: &isDirectory)
                    return isDirectory.boolValue
                }
                .map { $0.lastPathComponent }
                .sorted { $0 > $1 } // Reverse chronological order
        } catch {
            print("Error listing analysis folders: \(error)")
            return []
        }
    }
    
    /// Delete an analysis and all its media
    func deleteAnalysis(id: String) throws {
        let analysisDirectory = getAnalysisDirectory(id: id)
        if FileManager.default.fileExists(atPath: analysisDirectory.path) {
            try FileManager.default.removeItem(at: analysisDirectory)
        }
    }
    
    /// Extract frame from video at specific time
    func extractFrame(from videoURL: URL, at time: Double) async throws -> UIImage {
        return try await withCheckedThrowingContinuation { continuation in
            let asset = AVURLAsset(url: videoURL)
            let imageGenerator = AVAssetImageGenerator(asset: asset)
            imageGenerator.appliesPreferredTrackTransform = true
            imageGenerator.maximumSize = CGSize(width: 800, height: 600)
            
            let cmTime = CMTime(seconds: time, preferredTimescale: 1000)
            
            imageGenerator.generateCGImagesAsynchronously(
                forTimes: [NSValue(time: cmTime)]
            ) { _, cgImage, _, _, error in
                if let error = error {
                    continuation.resume(throwing: error)
                } else if let cgImage = cgImage {
                    let image = UIImage(cgImage: cgImage)
                    continuation.resume(returning: image)
                } else {
                    continuation.resume(throwing: MediaStorageError.frameExtractionFailed)
                }
            }
        }
    }
    
    // MARK: - Private Methods
    
    private func createDirectoryIfNeeded(at url: URL) {
        if !FileManager.default.fileExists(atPath: url.path) {
            try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        }
    }
}

// MARK: - Error Types
enum MediaStorageError: LocalizedError {
    case imageConversionFailed
    case frameExtractionFailed
    case directoryCreationFailed
    
    var errorDescription: String? {
        switch self {
        case .imageConversionFailed:
            return "Failed to convert image to JPEG format"
        case .frameExtractionFailed:
            return "Failed to extract frame from video"
        case .directoryCreationFailed:
            return "Failed to create storage directory"
        }
    }
}

// MARK: - Analysis Report Model
struct AnalysisReport: Codable {
    let id: String
    let createdAt: Date
    let videoPath: String
    let thumbnailPath: String
    let overallScore: Int
    let avgHeadSpeed: String
    let topCompliment: String
    let topCritique: String
    let summary: String
    let keyMoments: [KeyMomentReport]
    let coachingScript: [CoachingLineReport]
}

struct KeyMomentReport: Codable {
    let phase: String
    let timestamp: Double
    let framePath: String
    let feedback: String
}

struct CoachingLineReport: Codable {
    let text: String
    let startFrame: Int
    let ttsPath: String
}