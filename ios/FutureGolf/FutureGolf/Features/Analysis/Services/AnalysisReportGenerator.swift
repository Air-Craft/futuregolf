import Foundation
import UIKit

@MainActor
class AnalysisReportGenerator {
    private let mediaStorage = AnalysisMediaStorage.shared

    func generateReport(for analysisId: String, videoURL: URL, result: AnalysisResult, thumbnail: UIImage?) async throws -> AnalysisReport {
        let newAnalysisId = try await mediaStorage.createAnalysisSession(videoURL: videoURL)
        
        if let thumb = thumbnail {
            try await mediaStorage.saveThumbnail(analysisId: newAnalysisId, image: thumb)
        }
        
        var keyMomentReports: [KeyMomentReport] = []
        for phase in result.swingPhases {
            let frameImage = try await mediaStorage.extractFrame(from: videoURL, at: phase.timestamp)
            let framePath = try await mediaStorage.saveKeyFrame(
                analysisId: newAnalysisId,
                phase: phase.name,
                frameNumber: Int(phase.timestamp * 30), // Assuming 30fps
                image: frameImage
            )
            keyMomentReports.append(KeyMomentReport(
                phase: phase.name,
                timestamp: phase.timestamp,
                framePath: framePath,
                feedback: phase.feedback
            ))
        }
        
        let coachingLines = parseCoachingScript(result.coachingScript)
        var coachingLineReports: [CoachingLineReport] = []
        for (index, line) in coachingLines.enumerated() {
            if let audioData = await TTSService.shared.cacheManager.getCachedAudio(for: line.text) {
                let ttsPath = try await mediaStorage.saveTTSAudio(
                    analysisId: newAnalysisId,
                    lineIndex: index,
                    audioData: audioData
                )
                coachingLineReports.append(CoachingLineReport(
                    text: line.text,
                    startFrame: line.startFrameNumber,
                    ttsPath: ttsPath
                ))
            }
        }
        
        let report = AnalysisReport(
            id: newAnalysisId,
            createdAt: Date(),
            videoPath: "video.mp4",
            thumbnailPath: "thumbnail.jpg",
            overallScore: result.balance,
            avgHeadSpeed: "\(result.swingSpeed) mph",
            topCompliment: result.keyPoints.first ?? "Great swing!",
            topCritique: result.keyPoints.count > 1 ? result.keyPoints[1] : "Keep practicing",
            summary: result.overallAnalysis,
            keyMoments: keyMomentReports,
            coachingScript: coachingLineReports
        )
        
        try await mediaStorage.saveAnalysisJSON(analysisId: newAnalysisId, analysisResult: result)
        try await mediaStorage.saveAnalysisReport(analysisId: newAnalysisId, report: report)
        
        print("📁 Analysis report saved to: \(newAnalysisId)")
        return report
    }

    private func parseCoachingScript(_ script: String) -> [(text: String, startFrameNumber: Int)] {
        var lines: [(text: String, startFrameNumber: Int)] = []
        let sentences = script.components(separatedBy: CharacterSet(charactersIn: ".!?"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        
        for (index, sentence) in sentences.enumerated() {
            lines.append((
                text: sentence + ".",
                startFrameNumber: index * 60 // Placeholder
            ))
        }
        return lines
    }
}
