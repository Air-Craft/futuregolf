import Foundation
import os.log

/// Service responsible for debug operations like clearing data
@MainActor
class DebugService {
    static let shared = DebugService()
    
    private let logger = Logger(subsystem: "com.plumbly.FutureGolf", category: "DebugService")
    
    private init() {}
    
    /// Delete all swing entries (videos and analysis data)
    func deleteAllSwingEntries(analysisStorage: AnalysisStorageManager, videoProcessing: VideoProcessingService) async {
        logger.info("🗑️ Starting deletion of all swing entries...")
        
        var deletedVideos = 0
        var deletedAnalyses = 0
        var totalSizeFreed: Int64 = 0
        
        // Get all analyses
        let allAnalyses = analysisStorage.storedAnalyses
        logger.info("🗑️ Found \(allAnalyses.count) analyses to delete")
        
        // Delete each analysis and its associated video
        for analysis in allAnalyses {
            // Delete video file if it exists
            let videoURL = analysis.videoURL
            do {
                let attributes = try FileManager.default.attributesOfItem(atPath: videoURL.path)
                let fileSize = attributes[FileAttributeKey.size] as? Int64 ?? 0
                totalSizeFreed += fileSize
                
                try FileManager.default.removeItem(at: videoURL)
                deletedVideos += 1
                logger.info("🗑️ Deleted video: \(videoURL.lastPathComponent) (\(fileSize) bytes)")
            } catch {
                logger.error("🗑️ Failed to delete video \(videoURL.lastPathComponent): \(error)")
            }
            
            // Delete analysis record
            analysisStorage.deleteAnalysis(id: analysis.id)
            deletedAnalyses += 1
            logger.info("🗑️ Deleted analysis: \(analysis.id)")
        }
        
        // Clear any pending video processing queue
        videoProcessing.clearAllPendingVideos()
        logger.info("🗑️ Cleared video processing queue")
        
        // Clear UserDefaults entries related to recordings
        clearRecordingUserDefaults()
        
        // Log summary
        let sizeInMB = Double(totalSizeFreed) / (1024 * 1024)
        logger.info("""
            🗑️ Deletion complete:
            - Analyses deleted: \(deletedAnalyses)
            - Videos deleted: \(deletedVideos)
            - Space freed: \(String(format: "%.2f", sizeInMB)) MB
            """)
        
        // Show toast notification
        ToastManager.shared.show(
            "Debug: Deleted \(deletedAnalyses) analyses and \(deletedVideos) videos",
            type: .success,
            duration: 3.0
        )
    }
    
    /// Clear UserDefaults entries related to recordings
    private func clearRecordingUserDefaults() {
        let defaults = UserDefaults.standard
        
        // Keys that might be used for recording-related data
        let keysToRemove = [
            "lastRecordingURL",
            "lastAnalysisId",
            "pendingVideoQueue",
            "recordingPreferences"
        ]
        
        for key in keysToRemove {
            if defaults.object(forKey: key) != nil {
                defaults.removeObject(forKey: key)
                logger.info("🗑️ Cleared UserDefaults key: \(key)")
            }
        }
        
        defaults.synchronize()
    }
    
    /// Perform all debug launch operations if configured
    func performDebugLaunchOperations(deps: AppDependencies) async {
        guard Config.isDebugEnabled else { return }
        
        // Delete all swing entries if configured
        if Config.deleteAllSwingEntriesAtLaunch {
            logger.warning("⚠️ DELETE_SWING_DATA_AT_LAUNCH is enabled - deleting all swing data!")
            await deleteAllSwingEntries(
                analysisStorage: deps.analysisStorage,
                videoProcessing: deps.videoProcessing
            )
        }
    }
}

// MARK: - AnalysisStorageManager Extension

extension AnalysisStorageManager {
    /// Get all analyses
    func getAllAnalyses() -> [StoredAnalysis] {
        return storedAnalyses
    }
}

// MARK: - VideoProcessingService Extension

extension VideoProcessingService {
    /// Clear all pending videos from the processing queue
    func clearAllPendingVideos() {
        processingQueue.removeAll()
        // Clear any active processing state
        isProcessing = false
        currentProcessingId = nil
    }
}