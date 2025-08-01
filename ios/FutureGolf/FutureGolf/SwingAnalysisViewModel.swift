import SwiftUI
import AVFoundation
import Combine

@MainActor
@Observable
class SwingAnalysisViewModel: ObservableObject {
    // Processing State
    var isLoading = true
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
    
    // Error handling
    var showError = false
    var errorMessage = ""
    
    // Offline state
    var isOffline = false
    var offlineMessage = "Waiting for connection"
    
    // TTS Cache state for this analysis
    var isAnalysisTTSReady = false
    var analysisTTSProgress: Double = 0.0
    private var ttsCacheCheckTimer: Timer?
    
    private let apiClient = APIClient()
    private var progressTimer: Timer?
    var videoURL: URL?
    private let storageManager = AnalysisStorageManager.shared
    private let mediaStorage = AnalysisMediaStorage.shared
    private let connectivityService = ConnectivityService.shared
    private let processingService = VideoProcessingService.shared
    private var analysisId: String?
    private var connectivityCallbackId: UUID?
    private var connectivityCancellable: AnyCancellable?
    
    func startNewAnalysis(videoURL: URL) {
        print("🎆 SwingAnalysisViewModel: startNewAnalysis called")
        print("🎆 videoURL: \(videoURL)")
        
        self.videoURL = videoURL
        
        // Check if we're in UI testing mode
        let testConfig = TestConfiguration.shared
        if testConfig.isUITesting {
            print("🎆 UI Testing mode detected")
            handleTestMode(testConfig: testConfig, videoURL: videoURL)
            return
        }
        
        // Create analysis record
        self.analysisId = storageManager.saveAnalysis(videoURL: videoURL, status: .pending)
        print("🎆 Created analysis ID: \(self.analysisId ?? "nil")")
        
        // Generate thumbnail asynchronously
        Task {
            await generateThumbnailAsync(from: videoURL)
        }
        
        // Set up connectivity monitoring
        setupConnectivityMonitoring()
        
        // Check connectivity
        let isConnected = connectivityService.isConnected
        print("🎆 Connectivity status: \(isConnected)")
        
        if !isConnected {
            // Show offline state
            print("🎆 Setting offline state")
            isOffline = true
            isLoading = false
            processingStatus = "Waiting for connectivity"
            processingDetail = "Your swing will be analyzed when connection is restored"
            
            // The connectivity toast is already shown by ConnectivityService
            return
        }
        
        // Connected - dismiss connectivity toast if shown
        ToastManager.shared.dismiss(id: "connectivity")
        
        print("🎆 Starting processing simulation")
        startProcessingSimulation()
        
        Task {
            await uploadAndAnalyzeVideo(url: videoURL)
        }
    }
    
    func loadExistingAnalysis(id: String) {
        print("🎆 SwingAnalysisViewModel: loadExistingAnalysis called")
        print("🎆 Analysis ID: \(id)")
        
        self.analysisId = id
        
        // Check if we're in UI testing mode
        let testConfig = TestConfiguration.shared
        if testConfig.isUITesting {
            print("🎆 UI Testing mode detected for existing analysis")
            handleTestMode(testConfig: testConfig, videoURL: nil, analysisId: id)
            return
        }
        
        // Set up connectivity monitoring
        setupConnectivityMonitoring()
        
        // Load from local storage
        Task {
            if let storedAnalysis = storageManager.getAnalysis(id: id) {
                print("🎆 Found stored analysis with status: \(storedAnalysis.status)")
                self.videoURL = storedAnalysis.videoURL
                
                // Generate thumbnail
                Task {
                    await generateThumbnailAsync(from: storedAnalysis.videoURL)
                }
                
                switch storedAnalysis.status {
                case .completed:
                    // Show results
                    if let result = storedAnalysis.analysisResult {
                        self.analysisResult = result
                        updateDisplayData(from: result)
                        self.isLoading = false
                    }
                    
                case .pending, .failed:
                    // Check connectivity and retry
                    if connectivityService.isConnected {
                        startProcessingSimulation()
                        Task {
                            await retryAnalysis(storedAnalysis)
                        }
                    } else {
                        // Show offline state
                        isOffline = true
                        isLoading = false
                        processingStatus = "Waiting for connection"
                        processingDetail = "Your swing will be analyzed when connection is restored"
                        ToastManager.shared.show("Waiting for connectivity...", type: .warning, duration: .infinity, id: "connectivity")
                    }
                    
                case .uploading, .analyzing:
                    // Show progress
                    startProcessingSimulation()
                    monitorAnalysisProgress(id: id)
                }
            } else {
                // Analysis not found
                showError = true
                errorMessage = "Analysis not found"
                isLoading = false
            }
        }
    }
    
    // MARK: - Test Mode Handling
    
    private func handleTestMode(testConfig: TestConfiguration, videoURL: URL?, analysisId: String? = nil) {
        print("🎆 Handling test mode: \(testConfig.analysisMode)")
        
        self.analysisId = analysisId ?? "test-analysis-001"
        
        // Set video URL if provided, otherwise use test video
        if let url = videoURL {
            self.videoURL = url
        } else {
            self.videoURL = Bundle.main.url(forResource: "test_video", withExtension: "mov")
        }
        
        // Generate thumbnail for test video
        if let testVideoURL = self.videoURL {
            Task {
                await generateThumbnailAsync(from: testVideoURL)
            }
        }
        
        // Handle different test modes
        switch testConfig.analysisMode {
        case .offline:
            handleOfflineTestMode(testConfig: testConfig)
        case .processing:
            handleProcessingTestMode(testConfig: testConfig)
        case .ttsCaching:
            handleTTSCachingTestMode(testConfig: testConfig)
        case .ttsComplete:
            handleTTSCompleteTestMode(testConfig: testConfig)
        case .completed:
            handleCompletedTestMode(testConfig: testConfig)
        }
    }
    
    private func handleOfflineTestMode(testConfig: TestConfiguration) {
        print("🎆 Setting up offline test mode")
        isOffline = true
        isLoading = false
        processingStatus = "Waiting for connectivity"
        processingDetail = "Your swing will be analyzed when connection is restored"
        ToastManager.shared.show("Waiting for connectivity...", type: .warning, duration: .infinity, id: "connectivity")
    }
    
    private func handleProcessingTestMode(testConfig: TestConfiguration) {
        print("🎆 Setting up processing test mode")
        isOffline = false
        isLoading = true
        processingStatus = "Analyzing swing"
        processingDetail = "Processing swing data..."
        processingProgress = 0.3
        
        // Simulate processing progress
        startProcessingSimulation()
    }
    
    private func handleTTSCachingTestMode(testConfig: TestConfiguration) {
        print("🎆 Setting up TTS caching test mode")
        isOffline = false
        isLoading = true
        processingStatus = "Preparing coaching audio"
        processingDetail = "Preparing audio for your personalized coaching session..."
        isAnalysisTTSReady = false
        analysisTTSProgress = 0.7
        
        // Load mock analysis data but keep loading state for TTS
        let mockResult = testConfig.createMockAnalysisResult()
        self.analysisResult = mockResult
        updateDisplayData(from: mockResult)
    }
    
    private func handleTTSCompleteTestMode(testConfig: TestConfiguration) {
        print("🎆 Setting up TTS complete test mode")
        isOffline = false
        isLoading = false
        isAnalysisTTSReady = true
        analysisTTSProgress = 1.0
        
        // Load mock analysis data
        let mockResult = testConfig.createMockAnalysisResult()
        self.analysisResult = mockResult
        updateDisplayData(from: mockResult)
        generateKeyMoments(from: mockResult)
    }
    
    private func handleCompletedTestMode(testConfig: TestConfiguration) {
        print("🎆 Setting up completed test mode")
        isOffline = false
        isLoading = false
        isAnalysisTTSReady = true
        
        // Load mock analysis data
        let mockResult = testConfig.createMockAnalysisResult()
        self.analysisResult = mockResult
        updateDisplayData(from: mockResult)
        generateKeyMoments(from: mockResult)
        
        // Simulate connection restore if configured
        if testConfig.shouldSimulateConnectionRestore {
            Task {
                try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
                ToastManager.shared.show("Connected", type: .success, duration: 2.0)
            }
        }
    }
    
    private func startProcessingSimulation() {
        processingProgress = 0.0
        
        progressTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self = self else { return }
                
                if self.processingProgress < 0.3 {
                    self.processingProgress += 0.01
                    self.processingStatus = "Uploading video"
                    self.processingDetail = "Uploading \(Int(self.processingProgress * 100 / 0.3))%"
                } else if self.processingProgress < 0.98 {
                    self.processingProgress += 0.005
                    self.processingStatus = "Analyzing"
                    self.processingDetail = "Processing swing data..."
                }
            }
        }
    }
    
    private func uploadAndAnalyzeVideo(url: URL) async {
        do {
            // Update status to uploading
            if let id = self.analysisId {
                storageManager.updateStatus(id: id, status: .uploading)
            }
            
            // Upload video
            guard let result = await apiClient.uploadAndAnalyzeVideo(url: url) else {
                throw NSError(domain: "SwingAnalysis", code: 0, userInfo: [NSLocalizedDescriptionKey: "Failed to analyze video"])
            }
            
            // Stop progress timer
            progressTimer?.invalidate()
            processingProgress = 1.0
            
            // Update UI with results
            self.analysisResult = result
            updateDisplayData(from: result)
            generateKeyMoments(from: result)
            
            // Pre-cache TTS phrases for analysis
            TTSPhraseManager.shared.registerAnalysisPhrases(from: result)
            
            // Start caching analysis phrases in background
            Task {
                await TTSService.shared.cacheManager.warmCache()
            }
            
            // Start monitoring TTS cache status for this analysis
            startTTSCacheMonitoring()
            
            // Update storage manager with results
            storageManager.updateAnalysisResult(id: self.analysisId ?? "", result: result)
            
            // Generate and save complete analysis report with media
            await self.generateAnalysisReport(result: result)
            
            // Play completion sound
            playCompletionSound()
            
            // Animate the UI transition
            withAnimation(.liquidGlassSpring) {
                self.isLoading = false
            }
            
        } catch {
            progressTimer?.invalidate()
            showError = true
            errorMessage = error.localizedDescription
        }
    }
    
    private func fetchAnalysisFromServer(id: String) async {
        // Implement server fetch
        // For now, using mock data
        let mockResult = AnalysisResult(
            id: id,
            status: "completed",
            swingPhases: [
                SwingPhase(name: "Setup", timestamp: 0.0, description: "Initial stance", feedback: "Good posture, maintain spine angle"),
                SwingPhase(name: "Backswing", timestamp: 1.5, description: "Club to top", feedback: "Full shoulder turn achieved"),
                SwingPhase(name: "Downswing", timestamp: 3.0, description: "Transition", feedback: "Smooth transition, watch hip rotation"),
                SwingPhase(name: "Impact", timestamp: 3.8, description: "Ball contact", feedback: "Solid contact, hands ahead of ball"),
                SwingPhase(name: "Follow Through", timestamp: 4.5, description: "Finish", feedback: "Complete the rotation")
            ],
            keyPoints: ["Great tempo", "Solid impact position", "Good balance throughout"],
            overallAnalysis: "Your swing shows good fundamentals with room for improvement in hip rotation and follow through. Focus on maintaining your spine angle throughout the swing.",
            coachingScript: "Let's work on your hip rotation...",
            swingSpeed: 95,
            tempo: "3:1",
            balance: 88
        )
        
        self.analysisResult = mockResult
        updateDisplayData(from: mockResult)
        generateKeyMoments(from: mockResult)
        
        withAnimation(.liquidGlassSpring) {
            self.isLoading = false
        }
    }
    
    func updateDisplayData(from result: AnalysisResult) {
        overallScore = "\(result.balance)"
        avgHeadSpeed = "\(result.swingSpeed) mph"
        
        // Extract compliment and critique from key points
        if result.keyPoints.count > 0 {
            topCompliment = result.keyPoints[0]
        }
        if result.keyPoints.count > 1 {
            topCritique = result.keyPoints[1]
        } else {
            topCritique = "Keep practicing your form"
        }
        
        summaryText = result.overallAnalysis
    }
    
    func generateKeyMoments(from result: AnalysisResult) {
        guard let url = videoURL else { return }
        
        // Generate key moments with placeholders, then load thumbnails asynchronously
        keyMoments = result.swingPhases.map { phase in
            KeyMoment(
                phaseName: phase.name,
                timestamp: phase.timestamp,
                thumbnail: nil, // Start with nil
                feedback: phase.feedback
            )
        }
        
        // Generate thumbnails asynchronously
        Task {
            for (index, phase) in result.swingPhases.enumerated() {
                if let thumbnail = await generateThumbnailAsync(from: url, at: phase.timestamp) {
                    await MainActor.run {
                        if index < keyMoments.count {
                            keyMoments[index] = KeyMoment(
                                phaseName: phase.name,
                                timestamp: phase.timestamp,
                                thumbnail: thumbnail,
                                feedback: phase.feedback
                            )
                        }
                    }
                }
            }
        }
    }
    
    func generateThumbnail(from url: URL, at time: Double = 0) -> UIImage? {
        let asset = AVURLAsset(url: url)
        let imageGenerator = AVAssetImageGenerator(asset: asset)
        imageGenerator.appliesPreferredTrackTransform = true
        imageGenerator.maximumSize = CGSize(width: 400, height: 300)
        
        let cmTime = CMTime(seconds: time, preferredTimescale: 1)
        
        do {
            let cgImage = try imageGenerator.copyCGImage(at: cmTime, actualTime: nil)
            return UIImage(cgImage: cgImage)
        } catch {
            print("Error generating thumbnail: \(error)")
            return nil
        }
    }
    
    private func generateThumbnail(from url: URL) {
        videoThumbnail = generateThumbnail(from: url, at: 0)
    }
    
    private func generateThumbnailAsync(from url: URL, at time: Double = 0) async -> UIImage? {
        return await withCheckedContinuation { continuation in
            Task.detached(priority: .background) {
                let asset = AVURLAsset(url: url)
                let imageGenerator = AVAssetImageGenerator(asset: asset)
                imageGenerator.appliesPreferredTrackTransform = true
                imageGenerator.maximumSize = CGSize(width: 400, height: 300)
                
                let cmTime = CMTime(seconds: time, preferredTimescale: 1)
                
                do {
                    let cgImage = try imageGenerator.copyCGImage(at: cmTime, actualTime: nil)
                    let image = UIImage(cgImage: cgImage)
                    continuation.resume(returning: image)
                } catch {
                    print("Error generating thumbnail: \(error)")
                    continuation.resume(returning: nil)
                }
            }
        }
    }
    
    private func generateThumbnailAsync(from url: URL) async {
        // Get video duration and use midway point
        let asset = AVURLAsset(url: url)
        
        do {
            let duration = try await asset.load(.duration)
            let durationSeconds = CMTimeGetSeconds(duration)
            let midwayTime = durationSeconds / 2.0
            
            print("🎬 Generating thumbnail from midway point: \(midwayTime)s of \(durationSeconds)s")
            if let thumbnail = await generateThumbnailAsync(from: url, at: midwayTime) {
                await MainActor.run {
                    self.videoThumbnail = thumbnail
                    
                    // Also save thumbnail to storage
                    if let analysisId = self.analysisId {
                        storageManager.updateThumbnail(id: analysisId, thumbnail: thumbnail)
                    }
                }
            }
        } catch {
            // Fallback to first frame
            print("🎬 Error getting duration, using first frame")
            if let thumbnail = await generateThumbnailAsync(from: url, at: 0) {
                await MainActor.run {
                    self.videoThumbnail = thumbnail
                }
            }
        }
    }
    
    private func playCompletionSound() {
        // Play a system sound
        AudioServicesPlaySystemSound(1001) // Simple completion sound
    }
    
    // MARK: - Retry and Monitoring Methods
    
    private func retryAnalysis(_ storedAnalysis: StoredAnalysis) async {
        // The VideoProcessingService will handle the actual retry
        // We just need to monitor the progress
        monitorAnalysisProgress(id: storedAnalysis.id)
    }
    
    private func monitorAnalysisProgress(id: String) {
        // Monitor the analysis progress
        Task {
            while isLoading {
                if let analysis = storageManager.getAnalysis(id: id) {
                    switch analysis.status {
                    case .completed:
                        if let result = analysis.analysisResult {
                            self.analysisResult = result
                            updateDisplayData(from: result)
                            generateKeyMoments(from: result)
                            
                            // Pre-cache TTS phrases
                            TTSPhraseManager.shared.registerAnalysisPhrases(from: result)
                            Task {
                                await TTSService.shared.cacheManager.warmCache()
                            }
                            
                            // Start monitoring TTS cache status
                            self.startTTSCacheMonitoring()
                            
                            withAnimation(.liquidGlassSpring) {
                                self.isLoading = false
                            }
                        }
                        progressTimer?.invalidate()
                        return
                        
                    case .failed:
                        progressTimer?.invalidate()
                        showError = true
                        errorMessage = analysis.lastError ?? "Analysis failed"
                        isLoading = false
                        return
                        
                    case .uploading:
                        processingStatus = "Uploading video"
                        processingProgress = analysis.uploadProgress * 0.3
                        
                    case .analyzing:
                        processingStatus = "Analyzing"
                        processingProgress = 0.3 + (0.7 * min(processingProgress, 0.98))
                        
                    case .pending:
                        // Still waiting
                        break
                    }
                }
                
                // Check every second
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
        }
    }
    
    // MARK: - Connectivity Monitoring
    
    private func setupConnectivityMonitoring() {
        // Monitor connectivity changes
        connectivityCancellable = connectivityService.$isConnected
            .removeDuplicates()
            .sink { [weak self] isConnected in
                guard let self = self else { return }
                
                if isConnected {
                    // Connected - dismiss waiting toast
                    ToastManager.shared.dismiss(id: "connectivity")
                    
                    // If we were offline and waiting, start processing
                    if self.isOffline {
                        self.isOffline = false
                        ToastManager.shared.show("Connection restored", type: .success)
                        
                        // If we have a pending analysis, start processing
                        if let analysisId = self.analysisId,
                           let analysis = self.storageManager.getAnalysis(id: analysisId),
                           (analysis.status == .pending || analysis.status == .failed) {
                            self.startProcessingSimulation()
                            Task {
                                await self.retryAnalysis(analysis)
                            }
                        }
                    }
                } else {
                    // Disconnected - show waiting toast if we need connectivity
                    if self.isLoading && !self.isOffline {
                        self.isOffline = true
                        self.isLoading = false
                        self.processingStatus = "Waiting for connectivity"
                        self.processingDetail = "Your swing will be analyzed when connection is restored"
                        ToastManager.shared.show("Waiting for connectivity...", type: .warning, duration: .infinity, id: "connectivity")
                    }
                }
            }
    }
    
    func cleanup() {
        connectivityCancellable?.cancel()
        if let callbackId = connectivityCallbackId {
            connectivityService.removeCallback(callbackId)
        }
        ttsCacheCheckTimer?.invalidate()
        ttsCacheCheckTimer = nil
    }
    
    // MARK: - TTS Cache Monitoring
    
    private func startTTSCacheMonitoring() {
        // Stop any existing timer
        ttsCacheCheckTimer?.invalidate()
        
        // Check immediately
        Task {
            await checkAnalysisTTSStatus()
        }
        
        // Then check every 0.5 seconds until ready
        ttsCacheCheckTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                
                if self.isAnalysisTTSReady {
                    self.ttsCacheCheckTimer?.invalidate()
                    self.ttsCacheCheckTimer = nil
                    return
                }
                
                await self.checkAnalysisTTSStatus()
            }
        }
    }
    
    private func checkAnalysisTTSStatus() async {
        guard let result = analysisResult else { return }
        
        // Parse coaching script into lines
        let lines = parseCoachingScript(result.coachingScript)
        
        // Also check phase feedback phrases
        var allPhrases: [String] = lines.map { $0.text }
        for phase in result.swingPhases {
            allPhrases.append(phase.feedback)
        }
        
        // Check cache status for all phrases
        var cachedCount = 0
        for phrase in allPhrases {
            if await TTSService.shared.cacheManager.getCachedAudio(for: phrase) != nil {
                cachedCount += 1
            }
        }
        
        await MainActor.run {
            self.analysisTTSProgress = Double(cachedCount) / Double(allPhrases.count)
            self.isAnalysisTTSReady = (cachedCount == allPhrases.count)
            
            if self.isAnalysisTTSReady {
                print("🎬 All TTS phrases cached for analysis")
            } else {
                print("🎬 TTS cache progress: \(cachedCount)/\(allPhrases.count)")
            }
        }
    }
    
    private func parseCoachingScript(_ script: String) -> [(text: String, startFrameNumber: Int)] {
        var lines: [(text: String, startFrameNumber: Int)] = []
        
        // Split by sentence endings
        let sentences = script.components(separatedBy: CharacterSet(charactersIn: ".!?"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        
        // For now, create simple lines without frame numbers
        // The actual frame numbers would come from more sophisticated parsing
        for (index, sentence) in sentences.enumerated() {
            lines.append((
                text: sentence + ".",
                startFrameNumber: index * 60 // Placeholder timing
            ))
        }
        
        return lines
    }
    
    // MARK: - Media Extraction and Report Generation
    
    func generateAnalysisReport(result: AnalysisResult) async {
        guard let analysisId = analysisId,
              let videoURL = videoURL else { return }
        
        do {
            // Create analysis folder and copy video
            let newAnalysisId = try mediaStorage.createAnalysisSession(videoURL: videoURL)
            
            // Update analysis ID if different
            if newAnalysisId != analysisId {
                self.analysisId = newAnalysisId
            }
            
            // Save thumbnail (already generated)
            if let thumbnail = videoThumbnail {
                try mediaStorage.saveThumbnail(analysisId: newAnalysisId, image: thumbnail)
            }
            
            // Extract key frames for each swing phase
            var keyMomentReports: [KeyMomentReport] = []
            for phase in result.swingPhases {
                let frameImage = try await mediaStorage.extractFrame(from: videoURL, at: phase.timestamp)
                let framePath = try mediaStorage.saveKeyFrame(
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
            
            // Parse coaching script and save TTS files
            let coachingLines = parseCoachingScript(result.coachingScript)
            var coachingLineReports: [CoachingLineReport] = []
            
            for (index, line) in coachingLines.enumerated() {
                // Check if TTS is already cached
                if let audioData = await TTSService.shared.cacheManager.getCachedAudio(for: line.text) {
                    let ttsPath = try mediaStorage.saveTTSAudio(
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
            
            // Create and save the complete report
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
            
            // Save analysis JSON and report
            try mediaStorage.saveAnalysisJSON(analysisId: newAnalysisId, analysisResult: result)
            try mediaStorage.saveAnalysisReport(analysisId: newAnalysisId, report: report)
            
            print("📁 Analysis report saved to: \(newAnalysisId)")
            
        } catch {
            print("❌ Error generating analysis report: \(error)")
        }
    }
}

