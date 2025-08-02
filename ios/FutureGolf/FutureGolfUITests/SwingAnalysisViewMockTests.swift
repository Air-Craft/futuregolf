import XCTest

final class SwingAnalysisViewMockTests: XCTestCase {
    
    var app: XCUIApplication!
    
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        
        // Set launch arguments for testing
        app.launchArguments = [
            "--uitesting",
            "--swingAnalysisTest",
            "--mockConnectivity"
        ]
    }
    
    override func tearDownWithError() throws {
        app = nil
    }
    
    // MARK: - Connectivity State Tests
    
    func testOfflineStateBusyIndicator() throws {
        app.launchEnvironment["CONNECTIVITY_STATE"] = "offline"
        app.launch()
        
        // Verify busy indicator exists
        let busyIndicator = app.activityIndicators.firstMatch
        XCTAssertTrue(busyIndicator.waitForExistence(timeout: 2))
        
        // Verify it's over the thumbnail
        let thumbnail = app.images.matching(NSPredicate(format: "identifier CONTAINS 'thumbnail'")).firstMatch
        XCTAssertTrue(thumbnail.frame.contains(busyIndicator.frame.center), 
                     "Busy indicator should be centered over thumbnail")
        
        // Verify progress text
        XCTAssertTrue(app.staticTexts["Waiting for connectivity..."].exists)
        
        // Verify expandable section exists
        let expandableSection = app.buttons["Analysis Details"].firstMatch
        XCTAssertTrue(expandableSection.exists)
    }
    
    func testConnectivityRestoredFlow() throws {
        app.launchEnvironment["CONNECTIVITY_STATE"] = "offline"
        app.launchEnvironment["SIMULATE_CONNECTION_RESTORE"] = "true"
        app.launch()
        
        // Initially offline
        XCTAssertTrue(app.activityIndicators.firstMatch.exists)
        XCTAssertTrue(app.staticTexts["Waiting for connectivity..."].exists)
        
        // Simulate connection restored after 2 seconds
        Thread.sleep(forTimeInterval: 2.5)
        
        // Verify UI updates
        XCTAssertTrue(app.staticTexts["Processing swing data..."].waitForExistence(timeout: 3))
        
        // Verify toast appears
        let successToast = app.staticTexts["Connected"]
        XCTAssertTrue(successToast.waitForExistence(timeout: 1))
    }
    
    // MARK: - TTS Cache State Tests
    
    func testTTSCachingInProgress() throws {
        app.launchEnvironment["ANALYSIS_MODE"] = "tts_caching"
        app.launch()
        
        // Verify busy indicator remains
        let busyIndicator = app.activityIndicators.firstMatch
        XCTAssertTrue(busyIndicator.waitForExistence(timeout: 2))
        
        // Verify status text
        XCTAssertTrue(app.staticTexts["Preparing coaching audio..."].exists)
        
        // Verify play button is NOT visible
        let playButton = app.buttons.matching(NSPredicate(format: "label CONTAINS 'play'")).firstMatch
        XCTAssertFalse(playButton.exists)
    }
    
    func testTTSCacheComplete() throws {
        app.launchEnvironment["ANALYSIS_MODE"] = "tts_complete"
        app.launch()
        
        // Verify play button appears
        let playButton = app.buttons.matching(NSPredicate(format: "label CONTAINS 'play'")).firstMatch
        XCTAssertTrue(playButton.waitForExistence(timeout: 3))
        
        // Verify busy indicator is gone
        let busyIndicator = app.activityIndicators.firstMatch
        XCTAssertFalse(busyIndicator.exists)
        
        // Verify play button is centered on thumbnail
        let thumbnail = app.images.matching(NSPredicate(format: "identifier CONTAINS 'thumbnail'")).firstMatch
        XCTAssertTrue(thumbnail.frame.contains(playButton.frame.center))
    }
    
    func testPlayButtonNavigatesToCoaching() throws {
        app.launchEnvironment["ANALYSIS_MODE"] = "tts_complete"
        app.launch()
        
        // Tap play button
        let playButton = app.buttons.matching(NSPredicate(format: "label CONTAINS 'play'")).firstMatch
        XCTAssertTrue(playButton.waitForExistence(timeout: 3))
        playButton.tap()
        
        // Verify navigation to video coaching view
        XCTAssertTrue(app.otherElements["VideoPlayer"].waitForExistence(timeout: 2))
        XCTAssertTrue(app.buttons["Done"].exists)
    }
    
    // MARK: - Expandable Section Tests
    
    func testExpandableSectionInOfflineState() throws {
        app.launchEnvironment["CONNECTIVITY_STATE"] = "offline"
        app.launch()
        
        // Find expandable section
        let expandableSection = app.buttons["Analysis Details"].firstMatch
        XCTAssertTrue(expandableSection.exists)
        
        // Verify initial state shows offline message
        XCTAssertTrue(app.staticTexts["Waiting for connection..."].exists)
        
        // Tap to expand
        expandableSection.tap()
        
        // Verify expanded content
        XCTAssertTrue(app.staticTexts["Your swing will be analyzed when connection is restored."].waitForExistence(timeout: 1))
        
        // Verify placeholder cards
        let placeholderCards = ["Key Points", "Technique Analysis", "Recommendations"]
        for card in placeholderCards {
            XCTAssertTrue(app.staticTexts[card].exists)
            XCTAssertTrue(app.staticTexts["Waiting for connection..."].allMatches.count > 1)
        }
        
        // Verify chevron rotation
        let chevron = app.images["chevron.down.circle.fill"]
        XCTAssertTrue(chevron.exists)
    }
    
    func testExpandableSectionInProcessingState() throws {
        app.launchEnvironment["ANALYSIS_MODE"] = "processing"
        app.launch()
        
        let expandableSection = app.buttons["Analysis Details"].firstMatch
        expandableSection.tap()
        
        // Verify processing messages
        XCTAssertTrue(app.staticTexts["Analyzing your swing technique..."].waitForExistence(timeout: 1))
        
        // Verify placeholder cards show processing state
        XCTAssertTrue(app.staticTexts["Processing..."].exists)
    }
    
    func testExpandableSectionContent() throws {
        app.launchEnvironment["ANALYSIS_MODE"] = "tts_caching"
        app.launch()
        
        let expandableSection = app.buttons["Analysis Details"].firstMatch
        
        // Test expand
        expandableSection.tap()
        
        // Verify content appears with animation
        let expandedContent = app.staticTexts["Preparing audio for your personalized coaching session..."]
        XCTAssertTrue(expandedContent.waitForExistence(timeout: 1))
        
        // Test collapse
        expandableSection.tap()
        
        // Verify content disappears
        XCTAssertTrue(expandedContent.waitForNonExistence(timeout: 1))
    }
    
    // MARK: - Layout and Size Tests
    
    func testThumbnailHeightCalculation() throws {
        app.launch()
        
        let thumbnail = app.images.matching(NSPredicate(format: "identifier CONTAINS 'thumbnail'")).firstMatch
        XCTAssertTrue(thumbnail.waitForExistence(timeout: 3))
        
        // Test on current device
        let frame = thumbnail.frame
        let screenWidth = app.frame.width
        let padding: CGFloat = 32
        let calculatedHeight = (screenWidth - padding) * 9 / 16
        
        if UIDevice.current.userInterfaceIdiom == .pad {
            XCTAssertLessThanOrEqual(frame.height, 400, "iPad thumbnail height should not exceed 400pt")
        } else {
            XCTAssertLessThanOrEqual(frame.height, 250, "iPhone thumbnail height should not exceed 250pt")
        }
    }
    
    func testUIElementPositioning() throws {
        app.launchEnvironment["ANALYSIS_MODE"] = "completed"
        app.launch()
        
        // Get main elements
        let thumbnail = app.images.matching(NSPredicate(format: "identifier CONTAINS 'thumbnail'")).firstMatch
        let progressBar = app.progressIndicators.firstMatch
        let expandableSection = app.buttons["Analysis Details"].firstMatch
        
        // Verify vertical ordering
        XCTAssertLessThan(thumbnail.frame.maxY, progressBar.frame.minY, 
                         "Thumbnail should be above progress bar")
        XCTAssertLessThan(progressBar.frame.maxY, expandableSection.frame.minY, 
                         "Progress bar should be above expandable section")
        
        // Verify spacing
        let spacing1 = progressBar.frame.minY - thumbnail.frame.maxY
        let spacing2 = expandableSection.frame.minY - progressBar.frame.maxY
        
        XCTAssertGreaterThan(spacing1, 20, "Should have adequate spacing between elements")
        XCTAssertGreaterThan(spacing2, 20, "Should have adequate spacing between elements")
    }
    
    // MARK: - Accessibility Tests
    
    func testAccessibilityIdentifiers() throws {
        app.launchEnvironment["ANALYSIS_MODE"] = "completed"
        app.launch()
        
        // Verify key elements have accessibility identifiers
        XCTAssertTrue(app.buttons.matching(identifier: "VideoThumbnail").firstMatch.exists)
        
        // Verify accessibility labels
        let playButton = app.buttons.matching(NSPredicate(format: "label CONTAINS 'Play swing analysis video'")).firstMatch
        if playButton.exists {
            XCTAssertNotNil(playButton.value(forKey: "accessibilityHint"))
        }
    }
    
    func testScrollPerformance() throws {
        app.launchEnvironment["ANALYSIS_MODE"] = "completed"
        app.launch()
        
        // Measure scroll performance
        let metrics = XCTOSSignpostMetric.scrollDraggingMetric
        let options = XCTMeasureOptions()
        options.iterationCount = 3
        
        measure(metrics: [metrics], options: options) {
            // Scroll down
            app.swipeUp()
            
            // Scroll up
            app.swipeDown()
        }
    }
}

// MARK: - Helper Extensions

extension CGRect {
    var center: CGPoint {
        return CGPoint(x: midX, y: midY)
    }
}

extension XCUIElement {
    func waitForNonExistence(timeout: TimeInterval) -> Bool {
        let doesNotExistPredicate = NSPredicate(format: "exists == false")
        let expectation = XCTNSPredicateExpectation(predicate: doesNotExistPredicate, object: self)
        return XCTWaiter().wait(for: [expectation], timeout: timeout) == .completed
    }
    
    var allMatches: [XCUIElement] {
        let query = XCUIApplication().descendants(matching: .any).matching(NSPredicate(format: "label == %@", self.label))
        return (0..<query.count).map { query.element(boundBy: $0) }
    }
}
