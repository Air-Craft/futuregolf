import XCTest
@testable import FutureGolf

final class TestConfigurationTests: XCTestCase {
    
    func testTestConfigurationInitialization() {
        let config = TestConfiguration.shared
        
        // Test that configuration initializes properly
        XCTAssertNotNil(config)
        XCTAssertNotNil(config.analysisMode)
        XCTAssertNotNil(config.connectivityState)
    }
    
    func testMockAnalysisResultCreation() {
        let config = TestConfiguration.shared
        let mockResult = config.createMockAnalysisResult()
        
        // Verify mock result has expected data
        XCTAssertEqual(mockResult.id, "test-analysis-001")
        XCTAssertEqual(mockResult.status, "completed")
        XCTAssertEqual(mockResult.swingPhases.count, 5)
        XCTAssertEqual(mockResult.swingSpeed, 95)
        XCTAssertEqual(mockResult.balance, 88)
        
        // Verify swing phases
        let phaseNames = mockResult.swingPhases.map { $0.name }
        XCTAssertTrue(phaseNames.contains("Setup"))
        XCTAssertTrue(phaseNames.contains("Backswing"))
        XCTAssertTrue(phaseNames.contains("Impact"))
        XCTAssertTrue(phaseNames.contains("Follow Through"))
        
        // Verify coaching content
        XCTAssertFalse(mockResult.overallAnalysis.isEmpty)
        XCTAssertFalse(mockResult.coachingScript.isEmpty)
        XCTAssertFalse(mockResult.keyPoints.isEmpty)
    }
    
    @MainActor
    func testSwingAnalysisViewModelTestMode() async {
        // Create a view model
        let viewModel = SwingAnalysisViewModel()
        
        // Get test video URL
        let testBundle = Bundle(for: type(of: self))
        guard let testVideoURL = testBundle.url(forResource: "test_video", withExtension: "mov") else {
            XCTFail("Test video not found in bundle")
            return
        }
        
        // Start analysis - should handle normally since we're not in UI testing mode
        viewModel.startNewAnalysis(videoURL: testVideoURL)
        
        // Wait a moment for processing to start
        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        // Verify that normal processing started (not test mode)
        // In normal mode, should either be loading or have connectivity issues
        XCTAssertTrue(viewModel.isLoading || viewModel.isOffline || viewModel.showError)
    }
}