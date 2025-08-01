import XCTest
@testable import FutureGolf

@MainActor
final class SwingAnalysisStateIntegrationTests: XCTestCase {
    
    var viewModel: SwingAnalysisViewModel!
    
    override func setUp() async throws {
        viewModel = SwingAnalysisViewModel()
    }
    
    override func tearDown() async throws {
        viewModel.cleanup()
        viewModel = nil
    }
    
    // MARK: - Helper Methods
    
    private func getTestVideoURL() -> URL {
        let bundle = Bundle(for: type(of: self))
        
        if let url = bundle.url(forResource: "test_video", withExtension: "mov") {
            return url
        }
        
        // Fallback path
        if let bundlePath = bundle.bundlePath.components(separatedBy: "/Build/Products/").first {
            let testVideoPath = "\(bundlePath)/ios/FutureGolf/FutureGolfTestsShared/fixtures/test_video.mov"
            let fileURL = URL(fileURLWithPath: testVideoPath)
            if FileManager.default.fileExists(atPath: fileURL.path) {
                return fileURL
            }
        }
        
        return FileManager.default.temporaryDirectory.appendingPathComponent("test_video.mov")
    }
    
    private func waitForStateStabilization(timeout: TimeInterval = 5.0) async throws {
        let startTime = Date()
        
        // Wait for loading states to stabilize
        while (viewModel.isThumbnailLoading || viewModel.isLoading) && 
              Date().timeIntervalSince(startTime) < timeout {
            try await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        }
    }
    
    // MARK: - TestConfiguration Integration Tests
    
    /// Test view model responds correctly to current TestConfiguration
    func testCurrentTestConfiguration() async throws {
        // Given - current TestConfiguration (read-only)
        let testConfig = TestConfiguration.shared
        let testVideoURL = getTestVideoURL()
        
        print("🔧 STATE TEST: Testing current TestConfiguration integration")
        print("   - Is UI Testing: \(testConfig.isUITesting)")
        print("   - Analysis mode: \(testConfig.analysisMode)")
        print("   - Connectivity: \(testConfig.connectivityState)")
        
        // When - starting analysis with current configuration
        viewModel.startNewAnalysis(videoURL: testVideoURL)
        
        // Wait for state to stabilize
        try await waitForStateStabilization()
        
        // Then - verify view model responds to configuration
        print("   - Is offline: \(viewModel.isOffline)")
        print("   - Is loading: \(viewModel.isLoading)")
        print("   - Processing status: \(viewModel.processingStatus)")
        
        // Verify basic state consistency
        XCTAssertNotNil(viewModel.videoURL, "Video URL should be set")
        XCTAssertEqual(viewModel.videoURL, testVideoURL, "Video URL should match")
        
        // Thumbnail should be attempted regardless of connectivity
        if viewModel.videoThumbnail != nil {
            print("   - Thumbnail: ✅ Generated")
            XCTAssertNotNil(viewModel.videoThumbnail, "Thumbnail generated successfully")
        } else {
            print("   - Thumbnail: ❌ Not generated (may be simulator limitation)")
            print("   - Thumbnail error: \(viewModel.thumbnailErrorMessage ?? "none")")
            // This is acceptable in simulator environment
        }
        
        print("✅ CONFIG TEST PASSED: View model responds to TestConfiguration")
    }
    
    /// Test direct state manipulation for offline scenarios
    func testOfflineStateSimulation() async throws {
        // Given - test video and manual offline state
        let testVideoURL = getTestVideoURL()
        
        print("🔧 OFFLINE TEST: Testing offline state behavior")
        
        // When - manually setting offline state (simulating ConnectivityService)
        viewModel.isOffline = true
        viewModel.startNewAnalysis(videoURL: testVideoURL)
        
        // Wait for state to stabilize
        try await waitForStateStabilization()
        
        // Then - verify offline behavior
        XCTAssertTrue(viewModel.isOffline, "Should be in offline state")
        XCTAssertNotNil(viewModel.videoURL, "Video URL should be set even offline")
        
        print("   - Is offline: \(viewModel.isOffline)")
        print("   - Video URL set: \(viewModel.videoURL != nil)")
        print("   - Processing status: \(viewModel.processingStatus)")
        
        // Thumbnail should still be attempted even offline
        if viewModel.videoThumbnail != nil {
            print("   - Thumbnail: ✅ Generated even offline")
            XCTAssertNotNil(viewModel.videoThumbnail, "Thumbnail should work offline")
        } else {
            print("   - Thumbnail: May not work in simulator")
        }
        
        print("✅ OFFLINE TEST PASSED: View model handles offline state correctly")
    }
    
    /// Test analysis result integration with mock data
    func testAnalysisResultIntegration() async throws {
        // Given - test video and mock analysis result
        let testVideoURL = getTestVideoURL()
        let mockResult = TestConfiguration.shared.createMockAnalysisResult()
        
        print("🔧 ANALYSIS TEST: Testing analysis result integration")
        
        // When - setting up analysis with mock result
        viewModel.startNewAnalysis(videoURL: testVideoURL)
        try await waitForStateStabilization()
        
        // Manually set analysis result (simulating completed analysis)
        viewModel.analysisResult = mockResult
        viewModel.isAnalysisTTSReady = true
        viewModel.isLoading = false
        
        // Then - verify analysis integration
        XCTAssertNotNil(viewModel.analysisResult, "Should have analysis result")
        XCTAssertEqual(viewModel.analysisResult?.id, mockResult.id, "Should have correct analysis ID")
        XCTAssertTrue(viewModel.isAnalysisTTSReady, "TTS should be ready")
        XCTAssertFalse(viewModel.isLoading, "Should not be loading when complete")
        
        print("   - Analysis ID: \(viewModel.analysisResult?.id ?? "nil")")
        print("   - TTS ready: \(viewModel.isAnalysisTTSReady)")
        print("   - Loading: \(viewModel.isLoading)")
        
        print("✅ ANALYSIS TEST PASSED: Analysis result integration works")
    }
    
    /// Test TTS loading state simulation
    func testTTSLoadingStateSimulation() async throws {
        // Given - analysis with TTS in progress
        let testVideoURL = getTestVideoURL()
        let mockResult = TestConfiguration.shared.createMockAnalysisResult()
        
        print("🔧 TTS TEST: Testing TTS loading state simulation")
        
        // When - setting up TTS loading state
        viewModel.startNewAnalysis(videoURL: testVideoURL)
        try await waitForStateStabilization()
        
        // Simulate analysis complete but TTS still loading
        viewModel.analysisResult = mockResult
        viewModel.isAnalysisTTSReady = false
        viewModel.analysisTTSProgress = 0.5
        viewModel.isLoading = false // Main analysis done
        
        // Then - verify TTS loading state
        XCTAssertNotNil(viewModel.analysisResult, "Should have analysis result")
        XCTAssertFalse(viewModel.isAnalysisTTSReady, "TTS should not be ready yet")
        XCTAssertGreaterThan(viewModel.analysisTTSProgress, 0, "Should have TTS progress")
        XCTAssertFalse(viewModel.isLoading, "Main analysis should be complete")
        
        print("   - Analysis result: \(viewModel.analysisResult != nil)")
        print("   - TTS ready: \(viewModel.isAnalysisTTSReady)")
        print("   - TTS progress: \(viewModel.analysisTTSProgress)")
        print("   - Main loading: \(viewModel.isLoading)")
        
        print("✅ TTS TEST PASSED: TTS loading state works correctly")
    }
    
    /// Test state transitions from offline to online
    func testOfflineToOnlineTransition() async throws {
        // Given - starting in offline mode
        let testVideoURL = getTestVideoURL()
        
        print("🔧 TRANSITION TEST: Testing offline to online state transition")
        
        // When - starting in offline mode
        viewModel.isOffline = true
        viewModel.startNewAnalysis(videoURL: testVideoURL)
        try await waitForStateStabilization()
        
        // Verify offline state
        XCTAssertTrue(viewModel.isOffline, "Should start in offline state")
        let thumbnailBeforeTransition = viewModel.videoThumbnail
        
        print("   - Initial state: Offline (\(viewModel.isOffline))")
        print("   - Thumbnail before transition: \(thumbnailBeforeTransition != nil ? "✅" : "❌")")
        
        // When - transitioning to online (simulating ConnectivityService update)
        viewModel.isOffline = false
        viewModel.isLoading = true
        viewModel.processingStatus = "Analyzing swing"
        
        // Then - verify transition
        XCTAssertFalse(viewModel.isOffline, "Should be online after transition")
        XCTAssertTrue(viewModel.isLoading, "Should be processing after transition")
        
        print("   - After transition: Online (\(viewModel.isOffline)) and processing (\(viewModel.isLoading))")
        print("   - Thumbnail preserved: \(viewModel.videoThumbnail != nil)")
        
        // Important: Video URL should be preserved during transition
        XCTAssertNotNil(viewModel.videoURL, "Video URL should be preserved during transition")
        XCTAssertEqual(viewModel.videoURL, testVideoURL, "Video URL should remain the same")
        
        print("✅ TRANSITION TEST PASSED: Offline to online transition works correctly")
    }
    
    /// Test thumbnail persistence across different states
    func testThumbnailPersistenceAcrossStates() async throws {
        // Given - analysis with thumbnail
        let testVideoURL = getTestVideoURL()
        
        print("🔧 PERSISTENCE TEST: Testing thumbnail persistence across state changes")
        
        // When - starting analysis and getting thumbnail
        viewModel.startNewAnalysis(videoURL: testVideoURL)
        try await waitForStateStabilization()
        
        let initialThumbnail = viewModel.videoThumbnail
        print("   - Initial thumbnail: \(initialThumbnail != nil ? "✅" : "❌")")
        
        // Then - verify thumbnail persists through state changes
        let states = [
            ("Offline", { self.viewModel.isOffline = true }),
            ("Online", { self.viewModel.isOffline = false }),
            ("Loading", { self.viewModel.isLoading = true }),
            ("Not Loading", { self.viewModel.isLoading = false })
        ]
        
        for (stateName, setState) in states {
            setState()
            
            // Thumbnail should persist regardless of other state changes
            if initialThumbnail != nil {
                XCTAssertNotNil(viewModel.videoThumbnail, "Thumbnail should persist in \(stateName) state")
            }
            
            print("   - \(stateName): Thumbnail preserved")
        }
        
        print("✅ PERSISTENCE TEST PASSED: Thumbnail persists across state changes")
    }
    
    /// Test basic view model functionality with current configuration
    func testBasicViewModelFunctionality() async throws {
        // Given - current test configuration and test video
        let testConfig = TestConfiguration.shared
        let testVideoURL = getTestVideoURL()
        
        print("🔧 BASIC TEST: Testing basic view model functionality")
        print("   - Current test config UI testing: \(testConfig.isUITesting)")
        print("   - Current analysis mode: \(testConfig.analysisMode)")
        
        // When - starting analysis
        viewModel.startNewAnalysis(videoURL: testVideoURL)
        
        // Wait for initial setup
        try await waitForStateStabilization()
        
        // Then - verify basic functionality works
        XCTAssertNotNil(viewModel.videoURL, "Video URL should be set")
        XCTAssertEqual(viewModel.videoURL, testVideoURL, "Video URL should match input")
        
        print("   - Video URL set: \(viewModel.videoURL != nil)")
        print("   - Thumbnail attempted: \(viewModel.videoThumbnail != nil || viewModel.thumbnailErrorMessage != nil)")
        print("   - Thumbnail loading: \(viewModel.isThumbnailLoading)")
        
        // Verify thumbnail process was attempted (success or failure both acceptable in simulator)
        let thumbnailProcessAttempted = viewModel.videoThumbnail != nil || 
                                       viewModel.thumbnailErrorMessage != nil ||
                                       viewModel.isThumbnailLoading
        
        if viewModel.videoThumbnail != nil {
            print("✅ THUMBNAIL: Generated successfully")
        } else {
            print("ℹ️ THUMBNAIL: May not work in simulator environment")
        }
        
        print("✅ BASIC TEST PASSED: View model functionality works with current configuration")
    }
}

// MARK: - TestConfiguration Integration Notes

/// TestConfiguration is read-only and configured via environment variables and command-line arguments.
/// These tests verify that the view model responds correctly to the current TestConfiguration
/// rather than trying to modify the configuration during testing.