import SwiftUI
import Combine
import AVFoundation

@MainActor
@Observable
class SwingAnalysisViewModel: ObservableObject {
    // Overall State
    var isLoading = true
    var isOffline = false
    var showError = false
    var errorMessage = ""

    // Processing State
    var processingProgress: Double = 0.0
    var processingStatus = "Checking connection"
    var processingDetail = "Preparing for analysis..."

    // Analysis Data
    var analysisResult: AnalysisResult?
    var videoThumbnail: UIImage?
    var keyMoments: [KeyMoment] = []

    // Display Data
    var overallScore: String = "--"
    var avgHeadSpeed: String = "-- mph"
    var topCompliment: String = "Loading..."
    var topCritique: String = "Loading..."
    var summaryText: String = "Analysis in progress..."
    
    // TTS State
    var isAnalysisTTSReady = false

    // Dependencies
    private var analysisService: AnalysisService?
    private var thumbnailService: ThumbnailService
    private var ttsCacheService: TTSCacheService
    private var reportGenerator: AnalysisReportGenerator
    private var connectivityService: ConnectivityService?
    private var storageManager: AnalysisStorageManager?

    // Private state
    private var cancellables = Set<AnyCancellable>()
    private var analysisId: String?
    var videoURL: URL?

    init(dependencies: AppDependencies?) {
        self.analysisService = AnalysisService(dependencies: dependencies)
        self.thumbnailService = ThumbnailService(dependencies: dependencies)
        self.ttsCacheService = TTSCacheService()
        self.reportGenerator = AnalysisReportGenerator()
        self.connectivityService = dependencies?.connectivity
        self.storageManager = dependencies?.analysisStorage
        
        setupBindings()
    }

    private func setupBindings() {
        thumbnailService.$thumbnail
            .receive(on: DispatchQueue.main)
            .sink { [weak self] image in
                self?.videoThumbnail = image
            }
            .store(in: &cancellables)

        ttsCacheService.$isReady
            .receive(on: DispatchQueue.main)
            .sink { [weak self] isReady in
                self?.isAnalysisTTSReady = isReady
            }
            .store(in: &cancellables)
        
        connectivityService?.$isConnected
            .removeDuplicates()
            .receive(on: DispatchQueue.main)
            .sink { [weak self] isConnected in
                self?.handleConnectivityChange(isConnected: isConnected)
            }
            .store(in: &cancellables)
    }

    func startNewAnalysis(videoURL: URL) {
        self.videoURL = videoURL
        
        let testConfig = TestConfiguration.shared
        if testConfig.isUITesting {
            handleTestMode(testConfig: testConfig, videoURL: videoURL)
            return
        }
        
        Task {
            do {
                let id = try await analysisService?.startNewAnalysis(videoURL: videoURL)
                self.analysisId = id
                await thumbnailService.generateThumbnail(for: id!, from: videoURL)
                monitorAnalysisProgress(id: id!)
            } catch {
                showError(message: error.localizedDescription)
            }
        }
    }

    func loadExistingAnalysis(id: String) {
        self.analysisId = id
        
        let testConfig = TestConfiguration.shared
        if testConfig.isUITesting {
            handleTestMode(testConfig: testConfig, videoURL: nil, analysisId: id)
            return
        }
        
        Task {
            if let storedAnalysis = storageManager?.getAnalysis(id: id) {
                self.videoURL = storedAnalysis.videoURL
                if let thumbData = storedAnalysis.thumbnailData, let thumb = UIImage(data: thumbData) {
                    self.videoThumbnail = thumb
                } else {
                    await thumbnailService.generateThumbnail(for: id, from: storedAnalysis.videoURL)
                }

                if storedAnalysis.status == .completed, let result = storedAnalysis.analysisResult {
                    handleCompletedAnalysis(result: result)
                } else {
                    try? await analysisService?.loadExistingAnalysis(id: id)
                    monitorAnalysisProgress(id: id)
                }
            } else {
                showError(message: "Analysis not found")
            }
        }
    }
    
    private func monitorAnalysisProgress(id: String) {
        // This would ideally be driven by updates from the AnalysisService,
        // but for now, we'll poll the storage manager as before.
        Task {
            while isLoading {
                if let analysis = storageManager?.getAnalysis(id: id) {
                    switch analysis.status {
                    case .completed:
                        if let result = analysis.analysisResult {
                            handleCompletedAnalysis(result: result)
                        }
                        return
                    case .failed:
                        showError(message: analysis.lastError ?? "Analysis failed")
                        return
                    case .uploading:
                        processingStatus = "Uploading video"
                        processingProgress = analysis.uploadProgress * 0.3
                    case .analyzing:
                        processingStatus = "Analyzing"
                        processingProgress = 0.3 + (0.7 * min(processingProgress, 0.98))
                    case .pending:
                        break
                    }
                }
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
        }
    }

    private func handleCompletedAnalysis(result: AnalysisResult) {
        self.analysisResult = result
        updateDisplayData(from: result)
        generateKeyMoments(from: result)
        ttsCacheService.startMonitoring(for: result)
        
        Task {
            if let id = self.analysisId, let url = self.videoURL {
                _ = try? await reportGenerator.generateReport(for: id, videoURL: url, result: result, thumbnail: self.videoThumbnail)
            }
        }
        
        withAnimation(.liquidGlassSpring) {
            self.isLoading = false
        }
    }

    private func handleConnectivityChange(isConnected: Bool) {
        if isConnected {
            if self.isOffline {
                self.isOffline = false
                ToastManager.shared.show("Connection restored", type: .success)
                
                if let id = self.analysisId {
                    Task {
                        try? await analysisService?.loadExistingAnalysis(id: id)
                    }
                }
            }
        } else {
            if self.isLoading {
                self.isOffline = true
                self.isLoading = false
                self.processingStatus = "Waiting for connectivity"
                self.processingDetail = "Your swing will be analyzed when connection is restored"
                ToastManager.shared.show("Waiting for connectivity...", type: .warning, duration: .infinity, id: "connectivity")
            }
        }
    }

    private func showError(message: String) {
        self.errorMessage = message
        self.showError = true
        self.isLoading = false
    }

    // MARK: - UI Updates
    func updateDisplayData(from result: AnalysisResult) {
        overallScore = "\(result.balance)"
        avgHeadSpeed = "\(result.swingSpeed) mph"
        topCompliment = result.keyPoints.first ?? ""
        topCritique = result.keyPoints.count > 1 ? result.keyPoints[1] : "Keep practicing"
        summaryText = result.overallAnalysis
    }

    func generateKeyMoments(from result: AnalysisResult) {
        guard let url = videoURL else { return }
        
        keyMoments = result.swingPhases.map { phase in
            KeyMoment(phaseName: phase.name, timestamp: phase.timestamp, thumbnail: nil, feedback: phase.feedback)
        }
        
        Task {
            for i in 0..<keyMoments.count {
                if let thumb = await thumbnailService.generateThumbnailAsync(from: url, at: keyMoments[i].timestamp) {
                    keyMoments[i].thumbnail = thumb
                }
            }
        }
    }
    
    // MARK: - Test Mode
    private func handleTestMode(testConfig: TestConfiguration, videoURL: URL?, analysisId: String? = nil) {
        // Simplified for brevity. The original test mode logic can be moved here
        // and adapted to work with the new services if needed.
        self.isLoading = false
        let mockResult = testConfig.createMockAnalysisResult()
        handleCompletedAnalysis(result: mockResult)
    }

    func cleanup() {
        cancellables.forEach { $0.cancel() }
        cancellables.removeAll()
        ttsCacheService.stopMonitoring()
    }
}

