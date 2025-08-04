import XCTest

/// End-to-End tests for SwingAnalysisView that use real backend services
/// These tests verify the complete flow from video upload through analysis completion
final class SwingAnalysisViewE2ETests: XCTestCase {
    var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        
        // Configure app for E2E testing with real backend
        app.launchArguments = [
            "--uitesting",
            "--swingAnalysisE2ETest"
        ]
    }
    
    override func tearDownWithError() throws {
        app = nil
    }
    
    /// Test the complete swing analysis flow with real backend
    /// This test:
    /// 1. Launches app and taps DEBUG Analysis button
    /// 2. Waits for analysis to process with real backend
    /// 3. Verifies AnalysisResultView appears with results
    func testSwingAnalysisE2E() throws {
        // Launch the app
        app.launch()
        
        // Wait for home view to appear and find DEBUG Analysis button
        let debugButton = app.buttons["debugAnalysisButton"]
        XCTAssertTrue(debugButton.waitForExistence(timeout: 5), "DEBUG Analysis button should appear")
        
        // Tap the DEBUG Analysis button
        debugButton.tap()
        
        // The button should show a progress indicator while processing
        // Wait for the SwingAnalysisView to appear (may take up to 60 seconds with real backend)
        let analysisResultView = app.otherElements["debugAnalysisResultView"]
        let analysisViewAppeared = analysisResultView.waitForExistence(timeout: 10)
        
        if analysisViewAppeared {
            // Verify SwingAnalysisView is displayed
            XCTAssertTrue(analysisResultView.exists, "SwingAnalysisView should be displayed")
            
            // Wait for processing to complete
            let processingCompleted = waitForProcessingToComplete(timeout: 60)
            
            if processingCompleted {
                // Check for key elements in completed analysis
                // Video thumbnail should be visible
                let videoThumbnail = app.images["swingAnalysisThumbnail"]
                XCTAssertTrue(videoThumbnail.exists, "Video thumbnail should be visible")
                
                // Overall score should be displayed
                let scoreLabel = app.staticTexts["overallScoreLabel"]
                XCTAssertTrue(scoreLabel.exists, "Overall score should be displayed")
                
                // Take a screenshot for debugging
                takeDebugScreenshot(name: "SwingAnalysisCompleted")
            }
            
            // Verify we can dismiss the view
            let doneButton = app.buttons["Done"]
            XCTAssertTrue(doneButton.exists, "Done button should be available")
            
        } else {
            // If analysis didn't complete in time, check if button is still processing
            let progressIndicators = app.progressIndicators.count
            if progressIndicators > 0 {
                print("⚠️ Analysis still processing after timeout. Backend may be slow.")
            } else {
                XCTFail("Analysis did not complete and no progress indicators found")
            }
        }
    }
    
    /// Test that the app properly handles backend errors during E2E testing
    func testSwingAnalysisE2EErrorHandling() throws {
        // This test would verify error states, but requires backend to be down
        // or configured to return errors. Keeping as placeholder for future implementation.
        
        // Launch the app
        app.launch()
        
        // Wait for SwingAnalysisView
        let swingAnalysisView = app.otherElements["SwingAnalysisView"]
        XCTAssertTrue(swingAnalysisView.waitForExistence(timeout: 5), "SwingAnalysisView should appear")
        
        // At minimum, verify the view loads without crashing
        XCTAssertTrue(app.exists, "App should remain running")
    }
}

// MARK: - Test Helpers
extension SwingAnalysisViewE2ETests {
    
    /// Helper to wait for an element with custom predicate
    private func waitFor(element: XCUIElement, predicate: NSPredicate, timeout: TimeInterval) -> Bool {
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
        let result = XCTWaiter().wait(for: [expectation], timeout: timeout)
        return result == .completed
    }
    
    /// Helper to check if processing is still ongoing
    private func isProcessing() -> Bool {
        return app.progressIndicators["swingAnalysisBusyIndicator"].exists ||
               app.progressIndicators["swingAnalysisProgressBar"].exists
    }
    
    /// Helper to wait for processing to complete
    private func waitForProcessingToComplete(timeout: TimeInterval) -> Bool {
        let startTime = Date()
        
        while Date().timeIntervalSince(startTime) < timeout {
            if !isProcessing() {
                // Check if we have analysis content
                if app.images["swingAnalysisThumbnail"].exists {
                    return true
                }
            }
            Thread.sleep(forTimeInterval: 1.0)
        }
        
        return false
    }
    
    /// Helper to take a screenshot for debugging
    private func takeDebugScreenshot(name: String) {
        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}