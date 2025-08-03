import SwiftUI

struct MainNavigationView: View {
    @StateObject private var appState: AppState
    @StateObject private var deps = AppDependencies()
    @Environment(\.diContainer) var container
    
    init() {
        // Initialize AppState through DI container
        let tempContainer = DIContainer.shared
        let analysisStorage = tempContainer.resolve(AnalysisStorageManager.self)
        _appState = StateObject(wrappedValue: AppState(analysisStorage: analysisStorage))
    }
    
    var body: some View {
        NavigationStack(path: $appState.navigationPath) {
            HomeView()
                .navigationDestination(for: AppScreen.self) { screen in
                    destinationView(for: screen)
                }
                .fullScreenCover(isPresented: showRecordingBinding) {
                    RecordingNavigationWrapper(appState: appState, deps: deps)
                }
        }
        .withToastOverlay()
        .environmentObject(appState)
        .environmentObject(deps)
        .environmentObject(deps.analysisStorage)
        .environmentObject(deps.videoProcessing)
        .environmentObject(deps.connectivity)
        .withDIContainer(container)
    }
    
    @ViewBuilder
    private func destinationView(for screen: AppScreen) -> some View {
        switch screen {
        case .home:
            HomeView()
        case .recording:
            // Recording is handled as full screen cover
            EmptyView()
        case .analysis(let id):
            if let analysis = appState.analyses.first(where: { $0.id == id }),
               let videoURL = appState.currentRecordingURL ?? getStoredVideoURL(for: id) {
                SwingAnalysisView(
                    videoURL: videoURL,
                    analysisId: id,
                    dependencies: deps
                )
            } else {
                ProgressView("Loading analysis...")
            }
        case .previousAnalyses:
            PreviousAnalysesView()
        case .settings:
            SettingsView()
        case .about:
            AboutView()
        case .support:
            SupportView()
        }
    }
    
    private var showRecordingBinding: Binding<Bool> {
        Binding(
            get: { appState.currentScreen == .recording },
            set: { isShowing in
                if !isShowing {
                    appState.currentScreen = .home
                }
            }
        )
    }
    
    private func getStoredVideoURL(for analysisId: String) -> URL? {
        deps.analysisStorage.getAnalysis(id: analysisId)?.videoURL
    }
}

// MARK: - Recording Navigation Wrapper
struct RecordingNavigationWrapper: View {
    @ObservedObject var appState: AppState
    @ObservedObject var deps: AppDependencies
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            RecordingScreen()
                .environmentObject(appState)
                .environmentObject(deps)
                .environmentObject(deps.analysisStorage)
                .environmentObject(deps.videoProcessing)
                .environmentObject(deps.connectivity)
                .onChange(of: appState.currentRecordingId) { _, newId in
                    if let newId = newId {
                        // Transition to analysis after recording completes
                        dismiss()
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                            appState.navigate(to: .analysis(id: newId))
                        }
                    }
                }
        }
    }
}

#Preview {
    MainNavigationView()
}