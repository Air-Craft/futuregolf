import SwiftUI
import PhotosUI
import AVFoundation

enum UploadError: LocalizedError {
    case networkUnavailable
    case serverError(String)
    case timeout
    case invalidVideo
    case fileTooLarge
    case unauthorized
    
    var errorDescription: String? {
        switch self {
        case .networkUnavailable:
            return "No internet connection. Please check your network settings."
        case .serverError(let message):
            return "Server error: \(message)"
        case .timeout:
            return "The upload timed out. Please try again with a stable connection."
        case .invalidVideo:
            return "Invalid video format. Please upload an MP4 or MOV file."
        case .fileTooLarge:
            return "Video file is too large. Maximum size is 100MB."
        case .unauthorized:
            return "Authentication required. Please sign in and try again."
        }
    }
    
    var recoveryAction: String {
        switch self {
        case .networkUnavailable:
            return "Check Connection"
        case .serverError, .timeout:
            return "Retry Upload"
        case .invalidVideo, .fileTooLarge:
            return "Choose Different Video"
        case .unauthorized:
            return "Sign In"
        }
    }
}

@MainActor
@Observable
class VideoAnalysisViewModel {
    var selectedItem: PhotosPickerItem?
    var selectedVideoURL: URL?
    var isUploading = false
    var analysisResult: AnalysisResult?
    var showError = false
    var errorMessage = ""
    var currentError: UploadError?
    var uploadProgress: Double = 0.0
    var uploadStatus: String = ""
    
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
        uploadProgress = 0.0
        uploadStatus = "Preparing video..."
        currentError = nil
        
        do {
            // Check file size
            let fileSize = try FileManager.default.attributesOfItem(atPath: videoURL.path)[.size] as? Int64 ?? 0
            let maxSize: Int64 = 100 * 1024 * 1024 // 100MB
            
            if fileSize > maxSize {
                throw UploadError.fileTooLarge
            }
            
            // Check video format
            let asset = AVAsset(url: videoURL)
            guard asset.isPlayable else {
                throw UploadError.invalidVideo
            }
            
            uploadStatus = "Uploading video..."
            uploadProgress = 0.2
            
            let result = await apiClient.uploadAndAnalyzeVideo(url: videoURL)
            
            uploadProgress = 1.0
            uploadStatus = "Analysis complete!"
            analysisResult = result
            
            // Save for recent analysis
            lastAnalysisResult = result
            lastAnalysisDate = Date()
            
        } catch let error as UploadError {
            currentError = error
            showError = true
            errorMessage = error.localizedDescription
        } catch {
            // Map generic errors to our error types
            if (error as NSError).code == NSURLErrorNotConnectedToInternet {
                currentError = .networkUnavailable
            } else if (error as NSError).code == NSURLErrorTimedOut {
                currentError = .timeout
            } else {
                currentError = .serverError(error.localizedDescription)
            }
            
            showError = true
            errorMessage = currentError?.localizedDescription ?? "Unknown error occurred"
        }
        
        isUploading = false
    }
    
    func retryUpload() async {
        await uploadVideo()
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