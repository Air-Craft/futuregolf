import Foundation
import SwiftUI
import Combine

// MARK: - Analysis Status
enum AnalysisStatus: String, Codable {
    case pending          // Video recorded, waiting for upload
    case uploading        // Currently uploading
    case analyzing        // Server processing
    case completed        // Fully processed
    case failed           // Upload/processing failed
}

// MARK: - Stored Analysis Model
struct StoredAnalysis: Codable, Identifiable {
    let id: String
    let videoURL: URL
    let recordedAt: Date
    var status: AnalysisStatus
    var analysisResult: AnalysisResult?
    var lastError: String?
    var uploadProgress: Double = 0.0
    var lastUpdated: Date
    var thumbnailData: Data? // Store thumbnail as data
    
    init(videoURL: URL, status: AnalysisStatus = .pending) {
        self.id = UUID().uuidString
        self.videoURL = videoURL
        self.recordedAt = Date()
        self.status = status
        self.lastUpdated = Date()
    }
}

// MARK: - Analysis Storage Manager
@MainActor
class AnalysisStorageManager: ObservableObject {
    @Published var storedAnalyses: [StoredAnalysis] = []
    
    private let documentsDirectory: URL
    private let storageFileName = "stored_analyses.json"
    
    init() {
        documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        loadAnalyses()
    }
    
    // MARK: - Public Methods
    
    /// Save a new analysis record
    func saveAnalysis(videoURL: URL, status: AnalysisStatus = .pending) -> String {
        let analysis = StoredAnalysis(videoURL: videoURL, status: status)
        storedAnalyses.append(analysis)
        persistAnalyses()
        return analysis.id
    }
    
    /// Update the status of an analysis
    func updateStatus(id: String, status: AnalysisStatus, error: String? = nil) {
        guard let index = storedAnalyses.firstIndex(where: { $0.id == id }) else { return }
        
        storedAnalyses[index].status = status
        storedAnalyses[index].lastError = error
        storedAnalyses[index].lastUpdated = Date()
        persistAnalyses()
    }
    
    /// Update analysis with results
    func updateAnalysisResult(id: String, result: AnalysisResult) {
        guard let index = storedAnalyses.firstIndex(where: { $0.id == id }) else { return }
        
        storedAnalyses[index].analysisResult = result
        storedAnalyses[index].status = .completed
        storedAnalyses[index].lastUpdated = Date()
        persistAnalyses()
    }
    
    /// Update upload progress
    func updateUploadProgress(id: String, progress: Double) {
        guard let index = storedAnalyses.firstIndex(where: { $0.id == id }) else { return }
        
        storedAnalyses[index].uploadProgress = progress
        storedAnalyses[index].lastUpdated = Date()
        // Don't persist for every progress update to avoid excessive disk I/O
        if progress >= 1.0 {
            persistAnalyses()
        }
    }
    
    /// Update thumbnail
    func updateThumbnail(id: String, thumbnail: UIImage) {
        guard let index = storedAnalyses.firstIndex(where: { $0.id == id }) else { return }
        
        // Convert to JPEG data with compression
        if let thumbnailData = thumbnail.jpegData(compressionQuality: 0.7) {
            storedAnalyses[index].thumbnailData = thumbnailData
            storedAnalyses[index].lastUpdated = Date()
            persistAnalyses()
        }
    }
    
    /// Get thumbnail for analysis
    func getThumbnail(id: String) -> UIImage? {
        guard let analysis = getAnalysis(id: id),
              let thumbnailData = analysis.thumbnailData else { return nil }
        return UIImage(data: thumbnailData)
    }
    
    /// Get all analyses that need processing
    func getPendingAnalyses() -> [StoredAnalysis] {
        return storedAnalyses.filter { 
            $0.status == .pending || $0.status == .failed
        }.sorted { $0.recordedAt < $1.recordedAt } // Process oldest first
    }
    
    /// Get all analyses currently being processed
    func getActiveAnalyses() -> [StoredAnalysis] {
        return storedAnalyses.filter {
            $0.status == .uploading || $0.status == .analyzing
        }
    }
    
    /// Get a specific analysis
    func getAnalysis(id: String) -> StoredAnalysis? {
        return storedAnalyses.first { $0.id == id }
    }
    
    /// Delete an analysis
    func deleteAnalysis(id: String) {
        storedAnalyses.removeAll { $0.id == id }
        persistAnalyses()
        
        // Also delete the video file if needed
        if let analysis = getAnalysis(id: id) {
            try? FileManager.default.removeItem(at: analysis.videoURL)
        }
    }
    
    /// Clean up old completed analyses (optional housekeeping)
    func cleanupOldAnalyses(daysToKeep: Int = 30) {
        let cutoffDate = Calendar.current.date(byAdding: .day, value: -daysToKeep, to: Date())!
        
        let analysesToDelete = storedAnalyses.filter {
            $0.status == .completed && $0.recordedAt < cutoffDate
        }
        
        for analysis in analysesToDelete {
            deleteAnalysis(id: analysis.id)
        }
    }
    
    // MARK: - Private Methods
    
    private func loadAnalyses() {
        let fileURL = documentsDirectory.appendingPathComponent(storageFileName)
        
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            print("No stored analyses found")
            return
        }
        
        do {
            let data = try Data(contentsOf: fileURL)
            storedAnalyses = try JSONDecoder().decode([StoredAnalysis].self, from: data)
            print("Loaded \(storedAnalyses.count) stored analyses")
        } catch {
            print("Error loading stored analyses: \(error)")
        }
    }
    
    private func persistAnalyses() {
        let fileURL = documentsDirectory.appendingPathComponent(storageFileName)
        
        do {
            let data = try JSONEncoder().encode(storedAnalyses)
            try data.write(to: fileURL)
        } catch {
            print("Error persisting analyses: \(error)")
        }
    }
}

