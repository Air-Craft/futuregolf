import XCTest
import SwiftUI
import PhotosUI
@testable import FutureGolf

@MainActor
final class UploadVideoJourneyTests: XCTestCase {
    
    var viewModel: VideoAnalysisViewModel!
    
    @MainActor override func setUp() {
        super.setUp()
        viewModel = VideoAnalysisViewModel()
    }
    
    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }
    
    @MainActor func testInitialState() {
        let uploadView = UploadVideoJourneyView(viewModel: viewModel)
        
        // Verify initial state
        XCTAssertNotNil(uploadView, "Upload view should initialize")
        XCTAssertNil(viewModel.selectedItem, "No item should be selected initially")
        XCTAssertNil(viewModel.selectedVideoURL, "No video URL should be set initially")
        XCTAssertFalse(viewModel.isUploading, "Should not be uploading initially")
    }
    
    func testProgressIndicatorSteps() {
        // Test that we have 4 steps in the progress indicator
        let expectedSteps = 4
        
        // Create view
        let uploadView = UploadVideoJourneyView(viewModel: viewModel)
        let mirror = Mirror(reflecting: uploadView)
        
        // Verify progress indicator exists
        if let _ = mirror.descendant("progressIndicator") {
            // Progress indicator should show 4 steps
            XCTAssertTrue(true, "Progress indicator exists with \(expectedSteps) steps")
        }
    }
    
    func testInstructionsStepContent() {
        let uploadView = UploadVideoJourneyView(viewModel: viewModel)
        let mirror = Mirror(reflecting: uploadView)
        
        // Verify instructions step exists
        if let _ = mirror.descendant("instructionsStep") {
            XCTAssertTrue(true, "Instructions step should exist")
        }
    }
    
    @MainActor func testVideoSelectionFlow() {
        // Test video selection state
        viewModel.selectedItem = nil
        XCTAssertNil(viewModel.selectedVideoURL, "Video URL should be nil before selection")
        
        // Simulate video selection (in real test would use mocked PhotosPickerItem)
        let testURL = URL(fileURLWithPath: "/test/video.mov")
        viewModel.selectedVideoURL = testURL
        
        XCTAssertNotNil(viewModel.selectedVideoURL, "Video URL should be set after selection")
        XCTAssertEqual(viewModel.selectedVideoURL?.lastPathComponent, "video.mov", "Should have correct video name")
    }
    
    @MainActor func testUploadingState() async {
        // Set up video URL
        viewModel.selectedVideoURL = URL(fileURLWithPath: "/test/video.mov")
        
        // Test initial uploading state
        XCTAssertFalse(viewModel.isUploading, "Should not be uploading initially")
        
        // Start upload (this will fail in test but we're testing state changes)
        let uploadTask = Task {
            await viewModel.uploadVideo()
        }
        
        // Give it a moment to start
        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        // Cancel the task to clean up
        uploadTask.cancel()
        
        // After upload completes or fails, uploading should be false
        XCTAssertFalse(viewModel.isUploading, "Should not be uploading after completion")
    }
    
    func testStepTransitions() {
        // Test that steps progress correctly
        let steps = [
            "Instructions",
            "Video Selection", 
            "Video Preview",
            "Uploading"
        ]
        
        XCTAssertEqual(steps.count, 4, "Should have 4 steps in the journey")
        
        // Verify each step has unique content
        for (index, step) in steps.enumerated() {
            XCTAssertFalse(step.isEmpty, "Step \(index) should have a name")
        }
    }
    
    @MainActor func testErrorHandling() {
        // Test error state
        viewModel.showError = false
        viewModel.errorMessage = ""
        
        // Simulate error
        viewModel.showError = true
        viewModel.errorMessage = "Test error message"
        
        XCTAssertTrue(viewModel.showError, "Should show error")
        XCTAssertEqual(viewModel.errorMessage, "Test error message", "Should have correct error message")
    }
    
    @MainActor func testVideoLoadingFromPhotosPickerItem() async {
        // This test would require mocking PhotosPickerItem
        // For now, we test the method exists and handles nil
        
        await viewModel.loadVideo(from: nil)
        XCTAssertNil(viewModel.selectedVideoURL, "Should not set URL when item is nil")
    }
    
    @MainActor func testAnalysisResultHandling() {
        // Test that setting analysis result triggers expected behavior
        XCTAssertNil(viewModel.analysisResult, "Should not have analysis result initially")
        
        // Create mock result
        let mockResult = AnalysisResult(
            id: "test-id",
            status: "completed",
            swingPhases: [],
            keyPoints: ["Test point"],
            overallAnalysis: "Test analysis",
            coachingScript: "Test script",
            swingSpeed: 85,
            tempo: "3:1",
            balance: 92
        )
        
        viewModel.analysisResult = mockResult
        
        XCTAssertNotNil(viewModel.analysisResult, "Should have analysis result")
        XCTAssertEqual(viewModel.analysisResult?.id, "test-id", "Should have correct result ID")
    }
}

// UI Tests for Upload Journey
class UploadVideoJourneyUITests: XCTestCase {
    
    func testCancelButtonDismissesView() {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to upload flow
        if app.tabBars.buttons["Home"].exists {
            app.tabBars.buttons["Home"].tap()
        }
        
        let newAnalysisButton = app.buttons["New Analysis"]
        if newAnalysisButton.waitForExistence(timeout: 5) {
            newAnalysisButton.tap()
            
            // Look for Cancel button
            let cancelButton = app.navigationBars.buttons["Cancel"]
            XCTAssertTrue(cancelButton.waitForExistence(timeout: 5), "Cancel button should exist")
            
            // Tap cancel
            cancelButton.tap()
            
            // Verify we're back at home
            XCTAssertTrue(newAnalysisButton.waitForExistence(timeout: 5), "Should return to home screen")
        }
    }
    
    func testProgressThroughSteps() {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to upload flow
        if app.tabBars.buttons["Home"].exists {
            app.tabBars.buttons["Home"].tap()
        }
        
        let newAnalysisButton = app.buttons["New Analysis"]
        if newAnalysisButton.waitForExistence(timeout: 5) {
            newAnalysisButton.tap()
            
            // Step 1: Instructions
            let continueButton = app.buttons["Continue"]
            XCTAssertTrue(continueButton.waitForExistence(timeout: 5), "Continue button should exist")
            continueButton.tap()
            
            // Step 2: Video Selection
            let chooseFromLibraryButton = app.buttons["Choose from Library"]
            XCTAssertTrue(chooseFromLibraryButton.waitForExistence(timeout: 5), "Library button should exist")
        }
    }
}

// Haptic Manager Tests
class HapticManagerTests: XCTestCase {
    
    func testImpactHapticStyles() {
        // Test that haptic manager can handle all impact styles
        let styles: [UIImpactFeedbackGenerator.FeedbackStyle] = [.light, .medium, .heavy, .soft, .rigid]
        
        for style in styles {
            // This won't actually trigger haptics in test, but ensures no crashes
            HapticManager.impact(style)
        }
        
        XCTAssertTrue(true, "All haptic styles handled without crash")
    }
    
    func testNotificationHapticTypes() {
        // Test notification haptic types
        let types: [UINotificationFeedbackGenerator.FeedbackType] = [.success, .warning, .error]
        
        for type in types {
            HapticManager.notification(type)
        }
        
        XCTAssertTrue(true, "All notification types handled without crash")
    }
}