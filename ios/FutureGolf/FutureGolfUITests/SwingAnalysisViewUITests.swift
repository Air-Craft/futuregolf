import XCTest

final class SwingAnalysisViewUITests: XCTestCase {
    var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }
    
    override func tearDownWithError() throws {
        app = nil
    }
    
    // MARK: - Processing Mode Tests
    
    func testProcessingViewDisplaysCorrectly() throws {
        // Navigate to SwingAnalysisView in processing mode
        navigateToSwingAnalysisView(isProcessing: true)
        
        // Verify processing UI elements
        XCTAssertTrue(app.staticTexts["Processing Swing"].exists)
        XCTAssertTrue(app.progressIndicators.firstMatch.exists)
        XCTAssertTrue(app.staticTexts["Uploading video"].exists)
        
        // Verify progress bar exists
        let progressView = app.progressIndicators.firstMatch
        XCTAssertTrue(progressView.exists)
    }
    
    func testProcessingStatusUpdates() throws {
        navigateToSwingAnalysisView(isProcessing: true)
        
        // Check initial status
        XCTAssertTrue(app.staticTexts["Uploading video"].exists)
        
        // Wait for status change (simulated)
        let analyzingPredicate = NSPredicate(format: "label CONTAINS 'Analyzing'")
        let analyzingText = app.staticTexts.matching(analyzingPredicate)
        XCTAssertTrue(analyzingText.element.waitForExistence(timeout: 5))
    }
    
    // MARK: - Analysis Content Tests
    
    func testVideoThumbnailSection() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Verify video thumbnail exists
        let videoThumbnail = app.buttons.matching(identifier: "VideoThumbnail").firstMatch
        XCTAssertTrue(videoThumbnail.waitForExistence(timeout: 3))
        
        // Verify play button overlay
        let playButton = app.images["play.circle.fill"]
        XCTAssertTrue(playButton.exists)
        
        // Test tap action
        videoThumbnail.tap()
        
        // Verify video player appears
        XCTAssertTrue(app.otherElements["VideoPlayer"].waitForExistence(timeout: 2))
    }
    
    func testOverviewSection() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Verify stats display
        XCTAssertTrue(app.staticTexts["Overall Score"].exists)
        XCTAssertTrue(app.staticTexts["Avg Head Speed"].exists)
        
        // Verify score values
        let scoreValue = app.staticTexts.matching(NSPredicate(format: "label MATCHES '[0-9]+'")).firstMatch
        XCTAssertTrue(scoreValue.exists)
        
        // Verify feedback items
        XCTAssertTrue(app.images["checkmark.circle.fill"].exists)
        XCTAssertTrue(app.images["exclamationmark.triangle.fill"].exists)
    }
    
    func testAnalysisSection() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Verify section title
        XCTAssertTrue(app.staticTexts["Key Moments"].exists)
        
        // Verify horizontal scroll view
        let scrollView = app.scrollViews.firstMatch
        XCTAssertTrue(scrollView.exists)
        
        // Verify key moment cards exist
        let keyMomentCards = app.otherElements.matching(identifier: "KeyMomentCard")
        XCTAssertGreaterThan(keyMomentCards.count, 0)
        
        // Test scrolling
        scrollView.swipeLeft()
        
        // Verify phase names
        let phaseNames = ["Setup", "Backswing", "Downswing", "Impact", "Follow Through"]
        for phase in phaseNames {
            let phaseText = app.staticTexts[phase]
            if phaseText.exists {
                XCTAssertTrue(phaseText.isHittable)
            }
        }
    }
    
    func testSummarySection() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Scroll to bottom
        app.swipeUp()
        
        // Verify summary section
        XCTAssertTrue(app.staticTexts["Analysis Summary"].waitForExistence(timeout: 2))
        
        // Verify summary text exists and has content
        let summaryText = app.staticTexts.matching(NSPredicate(format: "label.length > 50")).firstMatch
        XCTAssertTrue(summaryText.exists)
    }
    
    // MARK: - Navigation Tests
    
    func testNavigationBarItems() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Verify navigation title
        XCTAssertTrue(app.navigationBars["Swing Analysis"].exists)
        
        // Verify share button
        let shareButton = app.buttons["square.and.arrow.up"]
        XCTAssertTrue(shareButton.exists)
        
        // Test share button tap
        shareButton.tap()
        
        // Verify share sheet appears
        XCTAssertTrue(app.otherElements["ActivityListView"].waitForExistence(timeout: 2))
    }
    
    func testBackNavigation() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Find and tap back button
        let backButton = app.navigationBars.buttons.firstMatch
        XCTAssertTrue(backButton.exists)
        
        backButton.tap()
        
        // Verify we're back at home
        XCTAssertTrue(app.staticTexts["Golf Swing"].waitForExistence(timeout: 2))
    }
    
    // MARK: - Interaction Tests
    
    func testCollapsedSectionExpansion() throws {
        navigateToSwingAnalysisView(isProcessing: true)
        
        // Find collapsed section
        let collapsedSection = app.otherElements.matching(identifier: "CollapsedAnalysisSection").firstMatch
        XCTAssertTrue(collapsedSection.waitForExistence(timeout: 2))
        
        // Tap to expand
        collapsedSection.tap()
        
        // Verify chevron rotates
        let chevron = app.images["chevron.down.circle.fill"]
        XCTAssertTrue(chevron.exists)
    }
    
    func testVideoPlayerNavigation() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Tap video thumbnail
        let videoThumbnail = app.buttons.matching(identifier: "VideoThumbnail").firstMatch
        videoThumbnail.tap()
        
        // Verify video player controls
        XCTAssertTrue(app.buttons["play.fill"].waitForExistence(timeout: 2))
        XCTAssertTrue(app.sliders.firstMatch.exists)
        
        // Test done button
        let doneButton = app.buttons["Done"]
        XCTAssertTrue(doneButton.exists)
        doneButton.tap()
        
        // Verify we're back at analysis view
        XCTAssertTrue(app.staticTexts["Key Moments"].waitForExistence(timeout: 2))
    }
    
    // MARK: - Accessibility Tests
    
    func testAccessibilityLabels() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Test video thumbnail accessibility
        let videoThumbnail = app.buttons.matching(identifier: "VideoThumbnail").firstMatch
        XCTAssertNotNil(videoThumbnail.label)
        
        // Test stat items accessibility
        let overallScore = app.staticTexts["Overall Score"]
        XCTAssertTrue(overallScore.isAccessibilityElement)
        
        // Test key moment cards
        let keyMomentCard = app.otherElements.matching(identifier: "KeyMomentCard").firstMatch
        XCTAssertTrue(keyMomentCard.isAccessibilityElement)
    }
    
    // MARK: - Helper Methods
    
    private func navigateToSwingAnalysisView(isProcessing: Bool) {
        // This would navigate through your app to reach SwingAnalysisView
        // For testing, you might need to set up a test harness or use launch arguments
        
        // Example: Navigate from home to recording to analysis
        // This would be replaced with proper test setup in a real app
        // For now, we'll assume the view is launched directly via test configuration
        
        // Simulate recording completion if needed
        if !isProcessing {
            // Wait for processing to complete (in test mode)
            Thread.sleep(forTimeInterval: 2)
        }
    }
}

// MARK: - Test Helpers
extension XCUIElement {
    func waitForNonExistence(timeout: TimeInterval) -> Bool {
        let doesNotExistPredicate = NSPredicate(format: "exists == false")
        let expectation = XCTNSPredicateExpectation(predicate: doesNotExistPredicate, object: self)
        return XCTWaiter().wait(for: [expectation], timeout: timeout) == .completed
    }
}