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
    
}

// MARK: - Test Helpers
// Extension moved to SwingAnalysisViewMockTests.swift to avoid duplication
