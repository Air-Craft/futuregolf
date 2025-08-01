import Foundation
import SwiftUI
import Combine

/// Central dependency container for the app
/// Uses proper DI pattern with @EnvironmentObject
@MainActor
class AppDependencies: ObservableObject {
    // Core services
    let analysisStorage: AnalysisStorageManager
    let videoProcessing: VideoProcessingService
    let connectivity: ConnectivityService
    let ttsService = TTSService.shared // Keep as singleton for now
    let audioRouteManager = AudioRouteManager.shared // Keep as singleton for now
    
    // Current recording state
    @Published var currentRecordingId: String?
    @Published var currentRecordingURL: URL?
    
    init() {
        // Initialize services
        self.connectivity = ConnectivityService()
        self.analysisStorage = AnalysisStorageManager()
        self.videoProcessing = VideoProcessingService(
            storageManager: analysisStorage,
            connectivityService: connectivity
        )
        
        // Start connectivity monitoring
        connectivity.startMonitoring()
        
        // Set up video processing to monitor connectivity
        videoProcessing.setupConnectivityMonitoring(connectivityService: connectivity)
    }
    
    /// Clear current recording state
    func clearCurrentRecording() {
        currentRecordingId = nil
        currentRecordingURL = nil
    }
    
    /// Set current recording
    func setCurrentRecording(url: URL, id: String) {
        currentRecordingURL = url
        currentRecordingId = id
    }
}