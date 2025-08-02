import Foundation
import UIKit
import AVFoundation
import Combine

@MainActor
class ThumbnailService: ObservableObject {
    @Published var thumbnail: UIImage?
    @Published var isLoading = false
    @Published var loadingProgress: Double = 0.0
    @Published var errorMessage: String?

    private var storageManager: AnalysisStorageManager?

    init(dependencies: AppDependencies?) {
        self.storageManager = dependencies?.analysisStorage
    }

    func generateThumbnail(for analysisId: String, from videoURL: URL) async {
        print("🎬 THUMBNAIL: Starting generation for: \(videoURL.lastPathComponent)")
        
        isLoading = true
        loadingProgress = 0.0
        errorMessage = nil
        
        guard await validateVideoFile(url: videoURL) else {
            print("🎬 THUMBNAIL: ❌ Video file validation failed")
            setThumbnailGenerationFailed(reason: "Video file not accessible")
            return
        }
        
        loadingProgress = 0.3
        
        let maxRetries = 3
        for attempt in 1...maxRetries {
            print("🎬 THUMBNAIL: Attempt \(attempt)/\(maxRetries)")
            loadingProgress = 0.3 + (Double(attempt) / Double(maxRetries)) * 0.6
            
            if let generatedThumbnail = await attemptThumbnailGeneration(from: videoURL, attempt: attempt) {
                self.thumbnail = generatedThumbnail
                self.isLoading = false
                self.loadingProgress = 1.0
                self.errorMessage = nil
                print("🎬 THUMBNAIL: ✅ Success on attempt \(attempt)")
                
                storageManager?.updateThumbnail(id: analysisId, thumbnail: generatedThumbnail)
                return
            }
            
            if attempt < maxRetries {
                let delay = UInt64(pow(2.0, Double(attempt)) * 500_000_000)
                print("🎬 THUMBNAIL: Waiting \(delay/1_000_000_000)s before retry...")
                try? await Task.sleep(nanoseconds: delay)
            }
        }
        
        print("🎬 THUMBNAIL: ❌ All attempts failed - no thumbnail available")
        setThumbnailGenerationFailed(reason: "Thumbnail generation failed after \(maxRetries) attempts")
    }

    private func validateVideoFile(url: URL) async -> Bool {
        guard FileManager.default.fileExists(atPath: url.path) else { return false }
        guard let attributes = try? FileManager.default.attributesOfItem(atPath: url.path),
              let fileSize = attributes[.size] as? Int64,
              fileSize > 0 else { return false }
        guard FileManager.default.isReadableFile(atPath: url.path) else { return false }
        
        let asset = AVURLAsset(url: url)
        guard let tracks = try? await asset.load(.tracks),
              !tracks.filter({ $0.mediaType == .video }).isEmpty else { return false }
        
        return true
    }

    private func attemptThumbnailGeneration(from url: URL, attempt: Int) async -> UIImage? {
        let asset = AVURLAsset(url: url)
        var timePositions: [Double] = [0.0]
        
        if let duration = try? await asset.load(.duration) {
            let durationSeconds = CMTimeGetSeconds(duration)
            if durationSeconds > 0 {
                switch attempt {
                case 1: timePositions = [durationSeconds / 2.0]
                case 2: timePositions = [durationSeconds / 4.0, durationSeconds * 3.0 / 4.0]
                default: timePositions = [0.0, durationSeconds / 8.0, durationSeconds / 4.0]
                }
            }
        }
        
        for time in timePositions {
            if let thumbnail = await generateThumbnailAsync(from: url, at: time) {
                return thumbnail
            }
        }
        
        return nil
    }

    func generateThumbnailAsync(from url: URL, at time: Double) async -> UIImage? {
        await withCheckedContinuation { continuation in
            Task.detached(priority: .background) {
                let asset = AVURLAsset(url: url)
                let imageGenerator = AVAssetImageGenerator(asset: asset)
                imageGenerator.appliesPreferredTrackTransform = true
                imageGenerator.maximumSize = CGSize(width: 400, height: 300)
                let cmTime = CMTime(seconds: time, preferredTimescale: 1)
                
                do {
                    let cgImage = try imageGenerator.copyCGImage(at: cmTime, actualTime: nil)
                    continuation.resume(returning: UIImage(cgImage: cgImage))
                } catch {
                    continuation.resume(returning: nil)
                }
            }
        }
    }

    private func setThumbnailGenerationFailed(reason: String) {
        isLoading = false
        loadingProgress = 0.0
        errorMessage = reason
    }
}
