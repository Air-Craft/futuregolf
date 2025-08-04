import Foundation
import Factory

extension Container {
    // MARK: - App State
    @MainActor var appState: Factory<AppState> {
        self { @MainActor in AppState() }.singleton
    }

    // MARK: - ViewModels
    @MainActor var swingAnalysisViewModel: Factory<SwingAnalysisViewModel> {
        self { @MainActor in SwingAnalysisViewModel() }
    }
    
    @MainActor var recordingViewModel: Factory<RecordingViewModel> {
        self { @MainActor in RecordingViewModel() }
    }
    
    @MainActor var videoAnalysisViewModel: Factory<VideoAnalysisViewModel> {
        self { @MainActor in VideoAnalysisViewModel() }
    }

    // MARK: - Services
    @MainActor var analysisService: Factory<AnalysisService> {
        self { @MainActor in AnalysisService() }
    }

    @MainActor var videoProcessingService: Factory<VideoProcessingService> {
        self { @MainActor in VideoProcessingService() }.cached
    }

    @MainActor var analysisStorageManager: Factory<AnalysisStorageManager> {
        self { AnalysisStorageManager() }.cached
    }
    
    var connectivityService: Factory<ConnectivityService> {
        self { ConnectivityService() }.singleton
    }
    
    var ttsService: Factory<TTSService> {
        self { TTSService.shared }.singleton
    }
    
    @MainActor var audioRouteManager: Factory<AudioRouteManager> {
        self { @MainActor in AudioRouteManager() }.singleton
    }
    
    @MainActor var thumbnailService: Factory<ThumbnailService> {
        self { @MainActor in ThumbnailService() }
    }
    
    @MainActor var ttsCacheService: Factory<TTSCacheService> {
        self { @MainActor in TTSCacheService() }
    }
    
    @MainActor var reportGenerator: Factory<AnalysisReportGenerator> {
        self { @MainActor in AnalysisReportGenerator() }
    }
    
    var recordingService: Factory<RecordingService> {
        self { RecordingService() }
    }
    
    @MainActor var cameraService: Factory<CameraService> {
        self { @MainActor in CameraService() }
    }
    
    @MainActor var voiceCommandService: Factory<VoiceCommandService> {
        self { @MainActor in VoiceCommandService() }
    }
    
    @MainActor var recordingAPIService: Factory<RecordingAPIService> {
        self { @MainActor in RecordingAPIService.shared }.singleton
    }
    
    var apiClient: Factory<APIClient> {
        self { APIClient() }
    }
}
