import XCTest

final class SwingAnalysisViewUITests: XCTestCase {
    var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        
        // Configure app for UI testing with mock data
        app.launchArguments = [
            "--uitesting",
            "--swingAnalysisTest",
            "--mockConnectivity"
        ]
        
        // Don't launch yet - let individual tests configure launch environment
    }
    
    override func tearDownWithError() throws {
        app = nil
    }
    
    // MARK: - Mock Data Tests
    
    func testMockAnalysisDataPresentation() throws {
        // Configure for completed analysis with mock data
        app.launchEnvironment["ANALYSIS_MODE"] = "completed"
        app.launchEnvironment["CONNECTIVITY_STATE"] = "online"
        app.launch()
        
        // Verify mock analysis data is displayed
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'test-analysis'")).firstMatch.waitForExistence(timeout: 3))
        
        // Verify swing phases from mock data
        XCTAssertTrue(app.staticTexts["Setup"].exists || app.staticTexts["Backswing"].exists)
        XCTAssertTrue(app.staticTexts["Impact"].exists || app.staticTexts["Follow Through"].exists)
        
        // Verify mock coaching feedback
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Good posture'")).firstMatch.exists ||
                     app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'fundamentals'")).firstMatch.exists)
        
        // Verify mock statistics
        XCTAssertTrue(app.staticTexts["95"].exists || // Swing speed
                     app.staticTexts["88"].exists)   // Balance score
    }
    
    // MARK: - Processing Mode Tests
    
    func testProcessingViewDisplaysCorrectly() throws {
        // Navigate to SwingAnalysisView in processing mode
        navigateToSwingAnalysisView(isProcessing: true)
        
        // Verify processing UI elements
        XCTAssertTrue(app.staticTexts["Processing Swing"].exists || 
                     app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Processing'")).firstMatch.exists)
        XCTAssertTrue(app.progressIndicators.firstMatch.exists)
        XCTAssertTrue(app.staticTexts["Uploading video"].exists || 
                     app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'Uploading'")).firstMatch.exists)
        
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
    
    // MARK: - Connectivity Tests
    
    func testOfflineAnalysisDisplay() throws {
        // Configure for offline analysis
        app.launchEnvironment["ANALYSIS_MODE"] = "offline"
        app.launchEnvironment["CONNECTIVITY_STATE"] = "offline"
        app.launch()
        
        // Verify offline messaging
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'offline'")).firstMatch.waitForExistence(timeout: 3))
        
        // Verify video thumbnail still shows
        let videoThumbnail = app.buttons.matching(identifier: "VideoThumbnail").firstMatch
        XCTAssertTrue(videoThumbnail.waitForExistence(timeout: 3))
    }
    
    func testConnectivityRestore() throws {
        // Configure to simulate connection restore
        app.launchEnvironment["ANALYSIS_MODE"] = "processing"
        app.launchEnvironment["CONNECTIVITY_STATE"] = "offline"
        app.launchEnvironment["SIMULATE_CONNECTION_RESTORE"] = "true"
        app.launch()
        
        // Initially should show offline state
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'connectivity'")).firstMatch.waitForExistence(timeout: 3))
        
        // Wait for connection restore (2 seconds as configured in MockConnectivityService)
        let connectedMessage = app.staticTexts["Connected"]
        XCTAssertTrue(connectedMessage.waitForExistence(timeout: 5))
    }
    
    // MARK: - Navigation Tests
    
    func testNavigationBarItems() throws {
        navigateToSwingAnalysisView(isProcessing: false)
        
        // Verify navigation title or main content (may vary based on implementation)
        let hasNavBar = app.navigationBars["Swing Analysis"].exists
        let hasMainContent = app.staticTexts["Analysis Summary"].exists || app.staticTexts["Overall Score"].exists
        XCTAssertTrue(hasNavBar || hasMainContent, "Should have navigation or main analysis content")
        
        // Test share functionality if share button exists
        let shareButton = app.buttons["square.and.arrow.up"]
        if shareButton.exists {
            shareButton.tap()
            // Look for either ActivityListView or any share sheet
            let shareSheetAppeared = app.otherElements["ActivityListView"].waitForExistence(timeout: 2) || 
                                   app.sheets.firstMatch.waitForExistence(timeout: 2)
            XCTAssertTrue(shareSheetAppeared, "Share sheet should appear")
        }
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
        // Configure analysis mode via launch environment
        if isProcessing {
            app.launchEnvironment["ANALYSIS_MODE"] = "processing"
            app.launchEnvironment["CONNECTIVITY_STATE"] = "online"
        } else {
            app.launchEnvironment["ANALYSIS_MODE"] = "completed"
            app.launchEnvironment["CONNECTIVITY_STATE"] = "online"
        }
        
        // Launch app with test configuration
        app.launch()
        
        // Wait for the swing analysis view to appear
        let swingAnalysisView = app.otherElements["SwingAnalysisView"]
        if !swingAnalysisView.waitForExistence(timeout: 5) {
            // Fallback: Look for main content elements that should be present
            let processingText = app.staticTexts["Processing Swing"]
            let completedContent = app.staticTexts["Analysis Summary"]
            XCTAssertTrue(processingText.exists || completedContent.exists, 
                         "Should show either processing or completed swing analysis content")
        }
    }
}

// MARK: - Test Helpers
// Extension moved to SwingAnalysisViewMockTests.swift to avoid duplication