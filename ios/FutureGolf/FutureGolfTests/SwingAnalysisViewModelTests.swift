import XCTest
@testable import FutureGolf
import Combine

@MainActor
final class SwingAnalysisViewModelTests: XCTestCase {
    var viewModel: SwingAnalysisViewModel!
    var cancellables: Set<AnyCancellable>!
    
    override func setUp() {
        super.setUp()
        viewModel = SwingAnalysisViewModel()
        cancellables = []
    }
    
    override func tearDown() {
        viewModel = nil
        cancellables = nil
        super.tearDown()
    }
    
    // MARK: - Initialization Tests
    
    func testInitialState() {
        XCTAssertTrue(viewModel.isLoading)
        XCTAssertEqual(viewModel.processingProgress, 0.0)
        XCTAssertEqual(viewModel.processingStatus, "Uploading video")
        XCTAssertNil(viewModel.analysisResult)
        XCTAssertTrue(viewModel.keyMoments.isEmpty)
    }
    
    // MARK: - New Analysis Tests
    
    func testStartNewAnalysis() async {
        // Create test video URL
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        
        // Start analysis
        viewModel.startNewAnalysis(videoURL: testURL)
        
        // Verify initial state
        XCTAssertTrue(viewModel.isLoading)
        XCTAssertEqual(viewModel.processingStatus, "Uploading video")
        
        // Wait a bit for processing simulation to start
        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        // Verify progress has started
        XCTAssertGreaterThan(viewModel.processingProgress, 0.0)
    }
    
    func testProcessingStatusUpdates() async {
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        viewModel.startNewAnalysis(videoURL: testURL)
        
        // Wait for status to change to "Analyzing"
        let expectation = XCTestExpectation(description: "Status changes to Analyzing")
        
        // Check status periodically since it's not @Published
        Task {
            for _ in 0..<50 { // Check 50 times
                if viewModel.processingStatus == "Analyzing" {
                    expectation.fulfill()
                    break
                }
                try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
            }
        }
        
        await fulfillment(of: [expectation], timeout: 5.0)
        
        XCTAssertEqual(viewModel.processingStatus, "Analyzing")
    }
    
    // MARK: - Existing Analysis Tests
    
    func testLoadExistingAnalysisSuccess() async {
        let testId = "test-analysis-123"
        
        viewModel.loadExistingAnalysis(id: testId)
        
        // Wait for loading to complete
        try? await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
        
        // Verify analysis was loaded
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNotNil(viewModel.analysisResult)
        XCTAssertEqual(viewModel.analysisResult?.id, testId)
    }
    
    // MARK: - Display Data Tests
    
    func testUpdateDisplayData() {
        let mockResult = createMockAnalysisResult()
        
        viewModel.updateDisplayData(from: mockResult)
        
        XCTAssertEqual(viewModel.overallScore, "88")
        XCTAssertEqual(viewModel.avgHeadSpeed, "95 mph")
        XCTAssertEqual(viewModel.topCompliment, "Great tempo")
        XCTAssertEqual(viewModel.topCritique, "Solid impact position")
        XCTAssertEqual(viewModel.summaryText, mockResult.overallAnalysis)
    }
    
    func testGenerateKeyMoments() {
        let mockResult = createMockAnalysisResult()
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        
        viewModel.videoURL = testURL
        viewModel.generateKeyMoments(from: mockResult)
        
        XCTAssertEqual(viewModel.keyMoments.count, mockResult.swingPhases.count)
        
        for (index, moment) in viewModel.keyMoments.enumerated() {
            XCTAssertEqual(moment.phaseName, mockResult.swingPhases[index].name)
            XCTAssertEqual(moment.timestamp, mockResult.swingPhases[index].timestamp)
            XCTAssertEqual(moment.feedback, mockResult.swingPhases[index].feedback)
        }
    }
    
    // MARK: - Error Handling Tests
    
    func testErrorHandling() async {
        // Simulate error during upload
        viewModel.showError = true
        viewModel.errorMessage = "Test error"
        
        XCTAssertTrue(viewModel.showError)
        XCTAssertEqual(viewModel.errorMessage, "Test error")
    }
    
    // MARK: - Thumbnail Generation Tests
    
    func testThumbnailGeneration() {
        let testURL = Bundle.main.url(forResource: "test_video", withExtension: "mp4")
        
        guard let url = testURL else {
            XCTFail("Test video not found")
            return
        }
        
        let thumbnail = viewModel.generateThumbnail(from: url, at: 0)
        
        XCTAssertNotNil(thumbnail)
    }
    
    // MARK: - Storage Manager Tests
    
    func testStorageManagerSaveAndLoad() async {
        let storageManager = AnalysisStorageManager()
        let mockResult = createMockAnalysisResult()
        let testURL = URL(fileURLWithPath: "/tmp/test_video.mp4")
        
        // Save analysis
        await storageManager.saveAnalysis(mockResult, videoURL: testURL)
        
        // Load analysis
        let loadedResult = await storageManager.loadAnalysis(id: mockResult.id)
        
        XCTAssertNotNil(loadedResult)
        XCTAssertEqual(loadedResult?.id, mockResult.id)
        XCTAssertEqual(loadedResult?.swingSpeed, mockResult.swingSpeed)
    }
    
    // MARK: - Helper Methods
    
    private func createMockAnalysisResult() -> AnalysisResult {
        return AnalysisResult(
            id: "test-123",
            status: "completed",
            swingPhases: [
                SwingPhase(name: "Setup", timestamp: 0.0, description: "Initial stance", feedback: "Good posture"),
                SwingPhase(name: "Backswing", timestamp: 1.5, description: "Club to top", feedback: "Full shoulder turn"),
                SwingPhase(name: "Impact", timestamp: 3.0, description: "Ball contact", feedback: "Solid contact")
            ],
            keyPoints: ["Great tempo", "Solid impact position", "Good balance"],
            overallAnalysis: "Your swing shows good fundamentals.",
            coachingScript: "Keep practicing",
            swingSpeed: 95,
            tempo: "3:1",
            balance: 88
        )
    }
}

// MARK: - Mock API Client for Testing
class MockAPIClient: APIClient {
    var shouldFail = false
    var mockDelay: TimeInterval = 1.0
    
    override func uploadAndAnalyzeVideo(url: URL) async -> AnalysisResult? {
        // Simulate network delay
        try? await Task.sleep(nanoseconds: UInt64(mockDelay * 1_000_000_000))
        
        if shouldFail {
            return nil
        }
        
        return AnalysisResult(
            id: UUID().uuidString,
            status: "completed",
            swingPhases: [
                SwingPhase(name: "Setup", timestamp: 0.0, description: "Setup", feedback: "Good setup")
            ],
            keyPoints: ["Test point"],
            overallAnalysis: "Test analysis",
            coachingScript: "Test script",
            swingSpeed: 90,
            tempo: "3:1",
            balance: 85
        )
    }
}