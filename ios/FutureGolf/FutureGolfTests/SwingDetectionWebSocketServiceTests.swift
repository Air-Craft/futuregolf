import XCTest
import AVFoundation
import Combine
@testable import FutureGolf

@MainActor
final class SwingDetectionWebSocketServiceTests: XCTestCase {
    
    var service: SwingDetectionWebSocketService!
    var cancellables = Set<AnyCancellable>()
    
    override func setUp() {
        super.setUp()
        service = SwingDetectionWebSocketService()
    }
    
    override func tearDown() {
        service.disconnect()
        service = nil
        cancellables.removeAll()
        super.tearDown()
    }
    
    func testSwingDetectionWithTestVideo() async throws {
        // Get test video URL
        let videoURL = try getTestVideoURL()
        
        // Extract frames from video
        let frames = try await extractFramesFromVideo(videoURL, intervalSeconds: 0.2)
        XCTAssertFalse(frames.isEmpty, "Should extract frames from video")
        print("📹 Extracted \(frames.count) frames from test video")
        
        // Set up expectations
        let connectionExpectation = XCTestExpectation(description: "WebSocket connects")
        let swingExpectations = [
            XCTestExpectation(description: "First swing detected"),
            XCTestExpectation(description: "Second swing detected"),
            XCTestExpectation(description: "Third swing detected")
        ]
        var detectedSwings = 0
        
        // Monitor connection state
        service.$isConnected
            .dropFirst() // Skip initial false value
            .filter { $0 } // Only when connected
            .first()
            .sink { _ in
                connectionExpectation.fulfill()
            }
            .store(in: &cancellables)
        
        // Set up swing detection callback
        service.onSwingDetected = { confidence in
            print("🏌️ Swing detected with confidence: \(confidence)")
            if confidence >= Config.swingDetectConfidenceThreshold {
                detectedSwings += 1
            }
            if detectedSwings <= swingExpectations.count && detectedSwings > 0 {
                swingExpectations[detectedSwings - 1].fulfill()
            }
        }
        
        // Connect to WebSocket
        service.connect()
        
        // Skip test if server is not available
//        guard await isServerAvailable() else {
//            XCTAssert(false, "WebSocket should not be connected")
//            throw XCTSkip("Server not available for WebSocket testing")
//        }
        
        // Wait for connection
        await fulfillment(of: [connectionExpectation], timeout: 5.0)
        XCTAssertTrue(service.isConnected, "WebSocket should be connected")
        
        // Begin detection
        service.beginDetection()
        
        // Send frames simulating real-time capture
        for (index, frame) in frames.enumerated() {
            do {
                try await service.sendFrame(frame.image)
                print("📷 Sent frame \(index + 1)/\(frames.count)")
                
                // Wait to simulate real-time (200ms between frames)
                try await Task.sleep(nanoseconds: 200_000_000) // 200ms
                
            } catch {
                print("❌ Failed to send frame \(index + 1): \(error)")
            }
        }
        
        // Wait for all 3 swings to be detected (with generous timeout)
        await fulfillment(of: swingExpectations, timeout: 60.0, enforceOrder: true)
        
        print("☑️ At least 3 swings detected. Total swings: \(detectedSwings)")
        
        // End detection
        service.endDetection()
        
        // Verify final state
        XCTAssertGreaterThanOrEqual(detectedSwings, 3, "Should detect at least 3 swings")
        print("✅ Test passed with \(detectedSwings) swings detected")
    }
    
    // MARK: - Helper Methods
    
    private func isServerAvailable() async -> Bool {
        let url = URL(string: "\(Config.apiBaseURL)/health")!
        
        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            if let httpResponse = response as? HTTPURLResponse {
                return httpResponse.statusCode == 200
            }
        } catch {
            print("⚠️ Server health check failed: \(error)")
        }
        
        return false
    }
    
    private func getTestVideoURL() throws -> URL {
        // Try to find test video in test bundle
        if let url = Bundle(for: type(of: self)).url(forResource: "test_video", withExtension: "mov") {
            return url
        }
        
        // Try shared fixtures directory
        let sharedFixturesPath = Bundle.main.bundlePath
            .replacingOccurrences(of: "FutureGolf.app", with: "FutureGolfTestsShared/fixtures/test_video.mov")
        let sharedURL = URL(fileURLWithPath: sharedFixturesPath)
        
        if FileManager.default.fileExists(atPath: sharedURL.path) {
            return sharedURL
        }
        
        // Try relative path from project
        let projectPath = #file
            .replacingOccurrences(of: "ios/FutureGolf/FutureGolfTests/SwingDetectionWebSocketServiceTests.swift", with: "")
        let fixturesURL = URL(fileURLWithPath: projectPath + "ios/FutureGolf/FutureGolfTestsShared/fixtures/test_video.mov")
        
        if FileManager.default.fileExists(atPath: fixturesURL.path) {
            return fixturesURL
        }
        
        throw XCTSkip("Test video not found in any expected location")
    }
    
    private func extractFramesFromVideo(_ url: URL, intervalSeconds: Double) async throws -> [(image: UIImage, timestamp: TimeInterval)] {
        let asset = AVAsset(url: url)
        
        // Check if asset is readable
        guard try await asset.load(.isReadable) else {
            throw NSError(domain: "SwingDetectionTests", code: 1, userInfo: [NSLocalizedDescriptionKey: "Video asset is not readable"])
        }
        
        let duration = try await asset.load(.duration)
        let durationSeconds = CMTimeGetSeconds(duration)
        
        let imageGenerator = AVAssetImageGenerator(asset: asset)
        imageGenerator.appliesPreferredTrackTransform = true
        imageGenerator.requestedTimeToleranceBefore = .zero
        imageGenerator.requestedTimeToleranceAfter = .zero
        
        var frames: [(image: UIImage, timestamp: TimeInterval)] = []
        var currentTime: TimeInterval = 0
        
        while currentTime < durationSeconds {
            let cmTime = CMTime(seconds: currentTime, preferredTimescale: 600)
            
            do {
                let cgImage = try imageGenerator.copyCGImage(at: cmTime, actualTime: nil)
                let uiImage = UIImage(cgImage: cgImage)
                frames.append((image: uiImage, timestamp: currentTime))
            } catch {
                print("⚠️ Failed to extract frame at \(currentTime)s: \(error)")
            }
            
            currentTime += intervalSeconds
        }
        
        return frames
    }
}
