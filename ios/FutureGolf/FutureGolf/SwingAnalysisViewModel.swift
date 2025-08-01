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
    
    private let apiClient = APIClient()
    private var progressTimer: Timer?
    var videoURL: URL?
    private let storageManager = AnalysisStorageManager.shared
    private let connectivityService = ConnectivityService.shared
    private let processingService = VideoProcessingService.shared
    private var analysisId: String?
    private var connectivityCallbackId: UUID?
    private var connectivityCancellable: AnyCancellable?
    
    func startNewAnalysis(videoURL: URL) {
        print("🎆 SwingAnalysisViewModel: startNewAnalysis called")
        print("🎆 videoURL: \(videoURL)")
        
        self.videoURL = videoURL
        
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
            
            // Show connectivity toast
            ToastManager.shared.show("Waiting for connectivity...", type: .warning, duration: .infinity, id: "connectivity")
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
            
            // Update storage manager with results
            storageManager.updateAnalysisResult(id: self.analysisId ?? "", result: result)
            
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
    }
}

