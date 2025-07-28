import SwiftUI
import PhotosUI
import AVFoundation

@MainActor
@Observable
class VideoAnalysisViewModel {
    var selectedItem: PhotosPickerItem?
    var selectedVideoURL: URL?
    var isUploading = false
    var analysisResult: AnalysisResult?
    var showError = false
    var errorMessage = ""
    
    // Properties for HomeView
    var hasRecentAnalysis: Bool {
        lastAnalysisResult != nil
    }
    var lastAnalysisDate: Date?
    var lastAnalysisResult: AnalysisResult?
    
    private let apiClient = APIClient()
    
    func loadVideo(from item: PhotosPickerItem?) async {
        guard let item = item else { return }
        
        do {
            if let movie = try await item.loadTransferable(type: Movie.self) {
                selectedVideoURL = movie.url
            }
        } catch {
            showError = true
            errorMessage = "Failed to load video: \(error.localizedDescription)"
        }
    }
    
    func uploadVideo() async {
        guard let videoURL = selectedVideoURL else { return }
        
        isUploading = true
        
        do {
            let result = await apiClient.uploadAndAnalyzeVideo(url: videoURL)
            analysisResult = result
        } catch {
            showError = true
            errorMessage = "Upload failed: \(error.localizedDescription)"
        }
        
        isUploading = false
    }
    
    func loadLastAnalysis() {
        // In a real app, this would load from persistent storage
        analysisResult = lastAnalysisResult
    }
}

struct Movie: Transferable {
    let url: URL
    
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(contentType: .movie) { movie in
            SentTransferredFile(movie.url)
        } importing: { received in
            let copy = URL.documentsDirectory.appending(path: "video_\(Date().timeIntervalSince1970).mov")
            try FileManager.default.copyItem(at: received.file, to: copy)
            return Self(url: copy)
        }
    }
}