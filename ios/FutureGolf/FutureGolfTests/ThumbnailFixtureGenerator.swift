import XCTest
import AVFoundation
import UIKit
@testable import FutureGolf

/// Utility class to generate thumbnail fixtures from test videos
/// This is used to create test_video_thumbnail.jpg for consistent testing
final class ThumbnailFixtureGenerator: XCTestCase {
    
    func testGenerateThumbnailFixture() throws {
        // This is a one-time utility test to generate the thumbnail fixture
        // Run this test once to create the fixture, then it can be used in other tests
        
        let testBundle = Bundle(for: type(of: self))
        guard let testVideoURL = testBundle.url(forResource: "test_video", withExtension: "mov") else {
            throw XCTSkip("Test video not found in bundle")
        }
        
        XCTAssertTrue(FileManager.default.fileExists(atPath: testVideoURL.path), 
                     "Test video must exist: \(testVideoURL.path)")
        
        // Generate thumbnail using the same method as the app
        let thumbnail = try generateThumbnailFromVideo(url: testVideoURL, at: 2.0) // Use 2 second mark
        
        // Save to documents directory for later manual copying to fixtures folder
        let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let thumbnailURL = documentsURL.appendingPathComponent("test_video_thumbnail.jpg")
        
        try saveThumbnailToFile(image: thumbnail, url: thumbnailURL)
        
        print("📸 Thumbnail fixture generated successfully!")
        print("📁 Saved to: \(thumbnailURL.path)")
        print("📋 Next steps:")
        print("   1. Copy test_video_thumbnail.jpg to FutureGolfTestsShared/fixtures/")
        print("   2. Add to Xcode project in both test bundles")
        print("   3. Use in tests with loadFixtureThumbnail()")
        
        // Verify the generated thumbnail has valid content
        let analysis = analyzeImageContent(thumbnail)
        print("🔍 Thumbnail analysis:")
        print("   - Size: \(thumbnail.size)")
        print("   - Has variation: \(analysis.hasVariation)")
        print("   - Average gray: \(analysis.averageGrayValue)")
        
        XCTAssertTrue(analysis.hasVariation, "Generated thumbnail should have visual variation (not a solid color)")
        XCTAssertGreaterThan(thumbnail.size.width, 0, "Thumbnail should have valid dimensions")
        XCTAssertGreaterThan(thumbnail.size.height, 0, "Thumbnail should have valid dimensions")
    }
    
    private func generateThumbnailFromVideo(url: URL, at time: Double) throws -> UIImage {
        let asset = AVURLAsset(url: url)
        let imageGenerator = AVAssetImageGenerator(asset: asset)
        imageGenerator.appliesPreferredTrackTransform = true
        imageGenerator.maximumSize = CGSize(width: 400, height: 300)
        
        let cmTime = CMTime(seconds: time, preferredTimescale: 600)
        
        do {
            let cgImage = try imageGenerator.copyCGImage(at: cmTime, actualTime: nil)
            return UIImage(cgImage: cgImage)
        } catch {
            throw NSError(domain: "ThumbnailGeneration", code: 0, 
                         userInfo: [NSLocalizedDescriptionKey: "Failed to generate thumbnail: \(error)"])
        }
    }
    
    private func saveThumbnailToFile(image: UIImage, url: URL) throws {
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            throw NSError(domain: "ThumbnailSave", code: 0,
                         userInfo: [NSLocalizedDescriptionKey: "Failed to convert image to JPEG data"])
        }
        
        try imageData.write(to: url)
    }
    
    private func analyzeImageContent(_ image: UIImage) -> ThumbnailAnalysis {
        guard let cgImage = image.cgImage else {
            return ThumbnailAnalysis(hasVariation: false, averageGrayValue: 0)
        }
        
        let width = cgImage.width
        let height = cgImage.height
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.noneSkipLast.rawValue)
        
        guard let context = CGContext(data: nil, width: width, height: height, 
                                    bitsPerComponent: 8, bytesPerRow: width * 4, 
                                    space: colorSpace, bitmapInfo: bitmapInfo.rawValue) else {
            return ThumbnailAnalysis(hasVariation: false, averageGrayValue: 0)
        }
        
        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
        
        guard let data = context.data else {
            return ThumbnailAnalysis(hasVariation: false, averageGrayValue: 0)
        }
        
        let pixels = data.bindMemory(to: UInt8.self, capacity: width * height * 4)
        
        var grayValues: [Int] = []
        let sampleSize = min(width * height, 1000) // Sample 1000 pixels
        let step = max(1, (width * height) / sampleSize)
        
        for i in stride(from: 0, to: width * height, by: step) {
            let pixelIndex = i * 4
            let red = Int(pixels[pixelIndex])
            let green = Int(pixels[pixelIndex + 1])
            let blue = Int(pixels[pixelIndex + 2])
            
            let grayValue = (red + green + blue) / 3
            grayValues.append(grayValue)
        }
        
        let averageGray = grayValues.reduce(0, +) / grayValues.count
        let meanGray = averageGray
        let variance = grayValues.map { pow(Double($0 - meanGray), 2) }.reduce(0, +) / Double(grayValues.count)
        let hasVariation = sqrt(variance) > 10 // Threshold for meaningful variation
        
        return ThumbnailAnalysis(hasVariation: hasVariation, averageGrayValue: averageGray)
    }
}

private struct ThumbnailAnalysis {
    let hasVariation: Bool
    let averageGrayValue: Int
}