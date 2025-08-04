import Foundation
import Combine
import Factory

@MainActor
class AnalysisService: ObservableObject {
    // Dependencies
    @Injected(\.apiClient) private var apiClient
    @Injected(\.analysisStorageManager) private var storageManager
    @Injected(\.connectivityService) private var connectivityService

    init() {}

    func startNewAnalysis(videoURL: URL) async throws -> String {
        // Create analysis record
        let analysisId = storageManager.saveAnalysis(videoURL: videoURL, status: .pending)
        
        // Check connectivity
        guard connectivityService.isConnected == true else {
            // Handled by the ViewModel observing connectivity
            return analysisId
        }
        
        // Start the analysis process
        try await processAnalysis(analysisId: analysisId, videoURL: videoURL)
        
        return analysisId
    }

    func loadExistingAnalysis(id: String) async throws {
        guard let storedAnalysis = storageManager.getAnalysis(id: id) else {
            throw NSError(domain: "AnalysisService", code: 2, userInfo: [NSLocalizedDescriptionKey: "Analysis not found."])
        }

        switch storedAnalysis.status {
        case .completed:
            // Data is already loaded by the ViewModel from storage
            break
        case .pending, .failed:
            // Check connectivity and retry
            if connectivityService.isConnected == true {
                try await retryAnalysis(storedAnalysis)
            }
        case .uploading, .analyzing:
            // ViewModel should already be monitoring progress
            break
        }
    }

    private func processAnalysis(analysisId: String, videoURL: URL) async throws {
        storageManager.updateStatus(id: analysisId, status: .uploading)
        
        guard let result = await apiClient.uploadAndAnalyzeVideo(url: videoURL) else {
            let error = NSError(domain: "AnalysisService", code: 3, userInfo: [NSLocalizedDescriptionKey: "Failed to analyze video."])
            storageManager.updateStatus(id: analysisId, status: .failed, error: error.localizedDescription)
            throw error
        }
        
        storageManager.updateAnalysisResult(id: analysisId, result: result)
    }

    private func retryAnalysis(_ storedAnalysis: StoredAnalysis) async throws {
        let videoURL = storedAnalysis.videoURL
        try await processAnalysis(analysisId: storedAnalysis.id, videoURL: videoURL)
    }
}
