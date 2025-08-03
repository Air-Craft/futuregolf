import Foundation
import SwiftUI
// import Swinject

// MARK: - Dependency Injection Container
// Note: Uncomment Swinject import after adding the package dependency

@MainActor
class DIContainer {
    static let shared = DIContainer()
    
    // Temporarily using a simple dictionary-based container until Swinject is added
    private var services: [String: Any] = [:]
    
    // When Swinject is added, uncomment:
    // private let container = Container()
    
    private init() {
        registerDependencies()
    }
    
    // MARK: - Registration
    private func registerDependencies() {
        // Register core services
        registerConnectivityService()
        registerAnalysisStorage()
        registerVideoProcessing()
        registerTTSService()
        registerAudioRouteManager()
        registerAppState()
        
        // Register ViewModels
        registerViewModels()
    }
    
    private func registerConnectivityService() {
        // When using Swinject:
        // container.register(ConnectivityService.self) { _ in
        //     ConnectivityService.shared
        // }.inObjectScope(.container)
        
        services["ConnectivityService"] = ConnectivityService.shared
    }
    
    private func registerAnalysisStorage() {
        // When using Swinject:
        // container.register(AnalysisStorageManager.self) { _ in
        //     AnalysisStorageManager()
        // }.inObjectScope(.container)
        
        services["AnalysisStorageManager"] = AnalysisStorageManager()
    }
    
    private func registerVideoProcessing() {
        // When using Swinject:
        // container.register(VideoProcessingService.self) { resolver in
        //     VideoProcessingService(
        //         storageManager: resolver.resolve(AnalysisStorageManager.self)!,
        //         connectivityService: resolver.resolve(ConnectivityService.self)!
        //     )
        // }.inObjectScope(.container)
        
        let storage = services["AnalysisStorageManager"] as! AnalysisStorageManager
        let connectivity = services["ConnectivityService"] as! ConnectivityService
        services["VideoProcessingService"] = VideoProcessingService(
            storageManager: storage,
            connectivityService: connectivity
        )
    }
    
    private func registerTTSService() {
        // When using Swinject:
        // container.register(TTSService.self) { _ in
        //     TTSService.shared
        // }.inObjectScope(.container)
        
        services["TTSService"] = TTSService.shared
    }
    
    private func registerAudioRouteManager() {
        // When using Swinject:
        // container.register(AudioRouteManager.self) { _ in
        //     AudioRouteManager.shared
        // }.inObjectScope(.container)
        
        services["AudioRouteManager"] = AudioRouteManager.shared
    }
    
    private func registerAppState() {
        // When using Swinject:
        // container.register(AppState.self) { resolver in
        //     AppState(
        //         analysisStorage: resolver.resolve(AnalysisStorageManager.self)!
        //     )
        // }.inObjectScope(.container)
        
        let storage = services["AnalysisStorageManager"] as! AnalysisStorageManager
        services["AppState"] = AppState(analysisStorage: storage)
    }
    
    private func registerViewModels() {
        // ViewModels are created per-view, so they would use .transient scope in Swinject
        // For now, we'll create them on-demand
    }
    
    // MARK: - Resolution
    func resolveOptional<T>(_ type: T.Type) -> T? {
        // When using Swinject:
        // return container.resolve(type)
        
        let typeName = String(describing: type)
        return services[typeName] as? T
    }
    
    func resolve<T>(_ type: T.Type) -> T {
        // When using Swinject:
        // return container.resolve(type)!
        
        let typeName = String(describing: type)
        guard let service = services[typeName] as? T else {
            fatalError("Service \(typeName) not registered in DI container")
        }
        return service
    }
    
    // MARK: - Factory Methods for ViewModels
    func makeRecordingViewModel() -> RecordingViewModel {
        // When using Swinject:
        // return container.resolve(RecordingViewModel.self)!
        
        let appState = resolve(AppState.self)
        return RecordingViewModel(dependencies: nil, appState: appState)
    }
    
    func makeSwingAnalysisViewModel(videoURL: URL, analysisId: String) -> SwingAnalysisViewModel {
        // When using Swinject:
        // return container.resolve(SwingAnalysisViewModel.self, arguments: videoURL, analysisId)!
        
        let appState = resolve(AppState.self)
        let storage = resolve(AnalysisStorageManager.self)
        let videoProcessing = resolve(VideoProcessingService.self)
        return SwingAnalysisViewModel(
            videoURL: videoURL,
            analysisId: analysisId,
            analysisStorage: storage,
            videoProcessingService: videoProcessing,
            appState: appState
        )
    }
}

// MARK: - DI Environment Key
struct DIContainerKey: EnvironmentKey {
    static let defaultValue = DIContainer.shared
}

extension EnvironmentValues {
    var diContainer: DIContainer {
        get { self[DIContainerKey.self] }
        set { self[DIContainerKey.self] = newValue }
    }
}

// MARK: - View Extension for easy DI access
extension View {
    func withDIContainer(_ container: DIContainer = .shared) -> some View {
        self.environment(\.diContainer, container)
    }
}