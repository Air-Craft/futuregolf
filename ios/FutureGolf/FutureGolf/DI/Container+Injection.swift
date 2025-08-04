import Foundation
import Factory

extension Container {
    // MARK: - App State
    var appState: Factory<AppState> {
        self { AppState() }.singleton
    }

    // MARK: - ViewModels
    var swingAnalysisViewModel: Factory<SwingAnalysisViewModel> {
        self { SwingAnalysisViewModel() }
    }
    
    var recordingViewModel: Factory<RecordingViewModel> {
        self { RecordingViewModel() }
    }
    
    var videoAnalysisViewModel: Factory<VideoAnalysisViewModel> {
        self { VideoAnalysisViewModel() }
    }

    // MARK: - Services
    var analysisService: Factory<AnalysisService> {
        self { AnalysisService() }
    }

    var videoProcessingService: Factory<VideoProcessingService> {
        self { VideoProcessingService() }.cached
    }

    var analysisStorageManager: Factory<AnalysisStorageManager> {
        self { AnalysisStorageManager() }.cached
    }
    
    var connectivityService: Factory<ConnectivityService> {
        self { ConnectivityService.shared }.singleton
    }
    
    var ttsService: Factory<TTSService> {
        self { TTSService.shared }.singleton
    }
    
    var audioRouteManager: Factory<AudioRouteManager> {
        self { AudioRouteManager.shared }.singleton
    }
    
    var thumbnailService: Factory<ThumbnailService> {
        self { ThumbnailService() }
    }
    
    var ttsCacheService: Factory<TTSCacheService> {
        self { TTSCacheService() }
    }
    
    var reportGenerator: Factory<AnalysisReportGenerator> {
        self { AnalysisReportGenerator() }
    }
    
    var recordingService: Factory<RecordingService> {
        self { RecordingService() }
    }
    
    var cameraService: Factory<CameraService> {
        self { CameraService() }
    }
    
    var voiceCommandService: Factory<VoiceCommandService> {
        self { VoiceCommandService() }
    }
    
    var recordingAPIService: Factory<RecordingAPIService> {
        self { RecordingAPIService.shared }.singleton
    }
    
    var apiClient: Factory<APIClient> {
        self { APIClient() }
    }
}