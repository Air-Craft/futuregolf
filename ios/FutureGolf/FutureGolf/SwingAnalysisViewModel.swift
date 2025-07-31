import SwiftUI
import AVFoundation
import Combine

@MainActor
@Observable
class SwingAnalysisViewModel: ObservableObject {
    // Processing State
    var isLoading = true
    var processingProgress: Double = 0.0
    var processingStatus = "Uploading video"
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
    
    private let apiClient = APIClient()
    private var progressTimer: Timer?
    var videoURL: URL?
    private let storageManager = AnalysisStorageManager()
    
    func startNewAnalysis(videoURL: URL) {
        self.videoURL = videoURL
        generateThumbnail(from: videoURL)
        startProcessingSimulation()
        
        Task {
            await uploadAndAnalyzeVideo(url: videoURL)
        }
    }
    
    func loadExistingAnalysis(id: String) {
        // Load from local storage
        Task {
            if let analysis = await storageManager.loadAnalysis(id: id) {
                self.analysisResult = analysis
                updateDisplayData(from: analysis)
                self.isLoading = false
                
                // Load video thumbnail if available
                if let url = self.videoURL {
                    generateThumbnail(from: url)
                }
            } else {
                // Fallback to API
                await fetchAnalysisFromServer(id: id)
            }
        }
    }
    
    private func startProcessingSimulation() {
        processingProgress = 0.0
        
        progressTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            
            if self.processingProgress < 0.3 {
                self.processingProgress += 0.01
                self.processingStatus = "Uploading video"
                self.processingDetail = "Uploading \(Int(self.processingProgress * 100 / 0.3))%"
            } else if self.processingProgress < 0.9 {
                self.processingProgress += 0.005
                self.processingStatus = "Analyzing"
                self.processingDetail = "Processing swing data..."
            } else if self.processingProgress < 0.98 {
                self.processingProgress += 0.002
                self.processingStatus = "Downloading"
                self.processingDetail = "Receiving analysis results..."
            }
        }
    }
    
    private func uploadAndAnalyzeVideo(url: URL) async {
        do {
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
            
            // Save to local storage
            await storageManager.saveAnalysis(result, videoURL: url)
            
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
        
        keyMoments = result.swingPhases.map { phase in
            let thumbnail = generateThumbnail(from: url, at: phase.timestamp)
            return KeyMoment(
                phaseName: phase.name,
                timestamp: phase.timestamp,
                thumbnail: thumbnail,
                feedback: phase.feedback
            )
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
    
    private func playCompletionSound() {
        // Play a system sound
        AudioServicesPlaySystemSound(1001) // Simple completion sound
    }
}

// MARK: - Storage Manager
actor AnalysisStorageManager {
    private let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
    private let analysisDirectory: URL
    
    init() {
        analysisDirectory = documentsDirectory.appendingPathComponent("SwingAnalyses")
        try? FileManager.default.createDirectory(at: analysisDirectory, withIntermediateDirectories: true)
    }
    
    func saveAnalysis(_ analysis: AnalysisResult, videoURL: URL) async {
        // Save analysis JSON
        let analysisFile = analysisDirectory.appendingPathComponent("\(analysis.id).json")
        
        do {
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            let data = try encoder.encode(analysis)
            try data.write(to: analysisFile)
            
            // Copy video to local storage
            let videoFile = analysisDirectory.appendingPathComponent("\(analysis.id).mp4")
            try FileManager.default.copyItem(at: videoURL, to: videoFile)
            
        } catch {
            print("Error saving analysis: \(error)")
        }
    }
    
    func loadAnalysis(id: String) async -> AnalysisResult? {
        let analysisFile = analysisDirectory.appendingPathComponent("\(id).json")
        
        do {
            let data = try Data(contentsOf: analysisFile)
            let decoder = JSONDecoder()
            return try decoder.decode(AnalysisResult.self, from: data)
        } catch {
            print("Error loading analysis: \(error)")
            return nil
        }
    }
    
    func getVideoURL(for analysisId: String) -> URL? {
        let videoFile = analysisDirectory.appendingPathComponent("\(analysisId).mp4")
        return FileManager.default.fileExists(atPath: videoFile.path) ? videoFile : nil
    }
}

