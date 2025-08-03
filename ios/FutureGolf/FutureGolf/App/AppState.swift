import Foundation
import SwiftUI
import Combine

// MARK: - Global App State
@MainActor
class AppState: ObservableObject {
    // MARK: - Navigation State
    @Published var navigationPath = NavigationPath()
    @Published var currentScreen: AppScreen = .home
    
    // MARK: - Analysis Data
    @Published var analyses: [AnalysisResult] = []
    @Published var activeAnalysisId: String?
    
    // Computed property for active analysis
    var activeAnalysis: AnalysisResult? {
        get {
            if let id = activeAnalysisId {
                return analyses.first { $0.id == id }
            }
            return nil
        }
        set {
            if let analysis = newValue {
                // If it's a new analysis not in the list, add it
                if !analyses.contains(where: { $0.id == analysis.id }) {
                    analyses.append(analysis)
                }
                activeAnalysisId = analysis.id
            } else {
                activeAnalysisId = nil
            }
        }
    }
    
    // MARK: - Recording State
    @Published var currentRecordingId: String?
    @Published var currentRecordingURL: URL?
    @Published var isRecording: Bool = false
    
    // MARK: - UI State
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var showError: Bool = false
    
    // MARK: - Dependencies
    private let analysisStorage: AnalysisStorageManager
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    init(analysisStorage: AnalysisStorageManager) {
        self.analysisStorage = analysisStorage
        loadAnalyses()
        setupObservers()
    }
    
    // MARK: - Data Loading
    private func loadAnalyses() {
        Task {
            await loadStoredAnalyses()
        }
    }
    
    @MainActor
    private func loadStoredAnalyses() async {
        // Load all completed analyses from storage
        let storedAnalyses = analysisStorage.getAllAnalyses()
            .filter { $0.analysisResult != nil }
            .compactMap { $0.analysisResult }
        
        self.analyses = storedAnalyses
    }
    
    // MARK: - Observers
    private func setupObservers() {
        // Listen for analysis updates from storage
        NotificationCenter.default.publisher(for: NSNotification.Name("AnalysisUpdated"))
            .sink { [weak self] notification in
                if let analysisId = notification.userInfo?["analysisId"] as? String {
                    Task { @MainActor in
                        await self?.refreshAnalysis(id: analysisId)
                    }
                }
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Analysis Management
    func addAnalysis(_ analysis: AnalysisResult) {
        if !analyses.contains(where: { $0.id == analysis.id }) {
            analyses.append(analysis)
        }
    }
    
    func updateAnalysis(_ analysis: AnalysisResult) {
        if let index = analyses.firstIndex(where: { $0.id == analysis.id }) {
            analyses[index] = analysis
        } else {
            addAnalysis(analysis)
        }
    }
    
    func removeAnalysis(id: String) {
        analyses.removeAll { $0.id == id }
        if activeAnalysisId == id {
            activeAnalysisId = nil
        }
    }
    
    @MainActor
    private func refreshAnalysis(id: String) async {
        if let storedAnalysis = analysisStorage.getAnalysis(id: id),
           let result = storedAnalysis.analysisResult {
            updateAnalysis(result)
        }
    }
    
    // MARK: - Recording Management
    func startRecording(id: String, url: URL) {
        currentRecordingId = id
        currentRecordingURL = url
        isRecording = true
    }
    
    func stopRecording() {
        isRecording = false
    }
    
    func clearRecording() {
        currentRecordingId = nil
        currentRecordingURL = nil
        isRecording = false
    }
    
    // MARK: - Navigation
    func navigate(to screen: AppScreen) {
        currentScreen = screen
        
        switch screen {
        case .home:
            navigationPath = NavigationPath()
        case .recording:
            // Recording is presented as full screen cover, not in navigation stack
            break
        case .analysis(let id):
            activeAnalysisId = id
            navigationPath.append(screen)
        case .previousAnalyses:
            navigationPath.append(screen)
        case .settings:
            navigationPath.append(screen)
        case .about:
            navigationPath.append(screen)
        case .support:
            navigationPath.append(screen)
        }
    }
    
    func navigateBack() {
        if !navigationPath.isEmpty {
            navigationPath.removeLast()
        }
    }
    
    func navigateToRoot() {
        navigationPath = NavigationPath()
        currentScreen = .home
    }
    
    // MARK: - Error Handling
    func showError(_ message: String) {
        errorMessage = message
        showError = true
    }
    
    func clearError() {
        errorMessage = nil
        showError = false
    }
}

// MARK: - Navigation Screens
enum AppScreen: Hashable {
    case home
    case recording
    case analysis(id: String)
    case previousAnalyses
    case settings
    case about
    case support
}

// MARK: - Placeholder Analysis
extension AppState {
    /// Creates a placeholder analysis for new recordings that haven't been processed yet
    func createPlaceholderAnalysis(for recordingId: String) -> AnalysisResult {
        return AnalysisResult(
            id: recordingId,
            status: "processing",
            swingPhases: [],
            keyPoints: [],
            overallAnalysis: "Analysis in progress...",
            coachingScript: "",
            swingSpeed: 0,
            tempo: "0:0",
            balance: 0
        )
    }
}