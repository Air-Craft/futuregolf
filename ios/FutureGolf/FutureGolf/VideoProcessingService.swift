import Foundation
import Combine

@MainActor
class VideoProcessingService: ObservableObject {
    @Published var isProcessing = false
    @Published var currentProcessingId: String?
    @Published var processingQueue: [String] = []
    
    private let storageManager: AnalysisStorageManager
    private let connectivityService: ConnectivityService
    private let apiClient = APIClient()
    
    private var activeTasks: Set<URLSessionTask> = []
    private var cancellables = Set<AnyCancellable>()
    private var connectivityCallbackId: UUID?
    private var isProcessingQueue = false
    
    init(storageManager: AnalysisStorageManager, connectivityService: ConnectivityService) {
        self.storageManager = storageManager
        self.connectivityService = connectivityService
    }
    
    deinit {
        // Cleanup is handled automatically
    }
    
    // MARK: - Public Methods
    
    /// Process all pending analyses
    func processPendingAnalyses() {
        guard connectivityService.isConnected else {
            print("📤 VideoProcessing: No connectivity, skipping processing")
            return
        }
        
        guard !isProcessingQueue else {
            print("📤 VideoProcessing: Already processing queue")
            return
        }
        
        Task {
            await processQueueSequentially()
        }
    }
    
    /// Queue a video for processing
    func queueVideo(videoURL: URL) -> String {
        let analysisId = storageManager.saveAnalysis(videoURL: videoURL, status: .pending)
        processingQueue.append(analysisId)
        
        // Try to process immediately if online
        if connectivityService.isConnected {
            processPendingAnalyses()
        }
        
        return analysisId
    }
    
    /// Cancel all active uploads
    func cancelAllActiveTasks() {
        print("📤 VideoProcessing: Cancelling \(activeTasks.count) active tasks")
        
        // Cancel all network tasks
        activeTasks.forEach { $0.cancel() }
        activeTasks.removeAll()
        
        // Update status of any uploading items back to pending
        let activeAnalyses = storageManager.getActiveAnalyses()
        for analysis in activeAnalyses {
            if analysis.status == .uploading || analysis.status == .analyzing {
                storageManager.updateStatus(id: analysis.id, status: .pending)
            }
        }
        
        isProcessing = false
        currentProcessingId = nil
    }
    
    // MARK: - Public Methods - Setup
    
    func setupConnectivityMonitoring(connectivityService: ConnectivityService) {
        // Monitor connectivity changes
        connectivityService.$isConnected
            .sink { [weak self] isConnected in
                if isConnected {
                    print("📤 VideoProcessing: Connectivity restored, checking for pending uploads")
                    self?.processPendingAnalyses()
                } else {
                    print("📤 VideoProcessing: Connectivity lost, cancelling active tasks")
                    self?.cancelAllActiveTasks()
                }
            }
            .store(in: &cancellables)
        
        // Register callback for restoration
        connectivityCallbackId = connectivityService.onConnectivityRestored { [weak self] in
            self?.processPendingAnalyses()
        }
    }
    
    private func processQueueSequentially() async {
        isProcessingQueue = true
        
        // Get all pending analyses
        let pendingAnalyses = storageManager.getPendingAnalyses()
        processingQueue = pendingAnalyses.map { $0.id }
        
        print("📤 VideoProcessing: Found \(pendingAnalyses.count) pending analyses")
        
        for analysis in pendingAnalyses {
            // Check connectivity before each upload
            guard connectivityService.isConnected else {
                print("📤 VideoProcessing: Lost connectivity, stopping queue processing")
                break
            }
            
            await processAnalysis(analysis)
        }
        
        isProcessingQueue = false
        processingQueue.removeAll()
    }
    
    private func processAnalysis(_ analysis: StoredAnalysis) async {
        currentProcessingId = analysis.id
        isProcessing = true
        
        // Update status to uploading
        storageManager.updateStatus(id: analysis.id, status: .uploading)
        
        do {
            // Check if connected (network + server)
            guard connectivityService.isConnected else {
                throw ProcessingError.serverUnreachable
            }
            
            print("📤 VideoProcessing: Starting upload for analysis \(analysis.id)")
            
            // Upload and analyze video
            guard let result = await uploadAndAnalyzeVideo(
                url: analysis.videoURL,
                analysisId: analysis.id
            ) else {
                throw ProcessingError.uploadFailed
            }
            
            // Update storage with results
            storageManager.updateAnalysisResult(id: analysis.id, result: result)
            
            print("📤 VideoProcessing: Successfully processed analysis \(analysis.id)")
            
            // Send notification if app is in background
            await sendCompletionNotification(for: analysis)
            
        } catch {
            print("📤 VideoProcessing: Failed to process analysis \(analysis.id): \(error)")
            
            let errorMessage: String
            switch error {
            case ProcessingError.serverUnreachable:
                errorMessage = "Server unreachable"
            case ProcessingError.uploadFailed:
                errorMessage = "Upload failed"
            case is URLError:
                errorMessage = "Network error"
            default:
                errorMessage = error.localizedDescription
            }
            
            storageManager.updateStatus(
                id: analysis.id,
                status: .failed,
                error: errorMessage
            )
        }
        
        // Remove from queue
        processingQueue.removeAll { $0 == analysis.id }
        currentProcessingId = nil
        
        // Small delay between uploads to avoid overwhelming the server
        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
    }
    
    private func uploadAndAnalyzeVideo(url: URL, analysisId: String) async -> AnalysisResult? {
        // Create a custom upload task that we can track and cancel
        return await withTaskCancellationHandler {
            await apiClient.uploadAndAnalyzeVideo(url: url)
        } onCancel: {
            // This will be called if the task is cancelled
            print("📤 VideoProcessing: Upload cancelled for \(analysisId)")
        }
    }
    
    private func sendCompletionNotification(for analysis: StoredAnalysis) async {
        // TODO: Implement push notification
        print("📤 VideoProcessing: Would send notification for completed analysis \(analysis.id)")
    }
}

// MARK: - Processing Errors
enum ProcessingError: LocalizedError {
    case serverUnreachable
    case uploadFailed
    case analysisTimeout
    
    var errorDescription: String? {
        switch self {
        case .serverUnreachable:
            return "Cannot reach the server. Please check your connection."
        case .uploadFailed:
            return "Failed to upload video. Please try again."
        case .analysisTimeout:
            return "Analysis is taking longer than expected."
        }
    }
}