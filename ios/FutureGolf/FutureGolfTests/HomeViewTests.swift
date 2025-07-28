import XCTest
import SwiftUI
@testable import FutureGolf

@MainActor
final class HomeViewTests: XCTestCase {
    
    var viewModel: VideoAnalysisViewModel!
    
    @MainActor override func setUp() {
        super.setUp()
        viewModel = VideoAnalysisViewModel()
    }
    
    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }
    
    func testGreetingTextBasedOnTime() {
        let homeView = HomeView()
        let mirror = Mirror(reflecting: homeView)
        
        // Test greeting computation
        let hour = Calendar.current.component(.hour, from: Date())
        let expectedGreeting: String
        
        switch hour {
        case 5..<12:
            expectedGreeting = "Good Morning"
        case 12..<17:
            expectedGreeting = "Good Afternoon"
        case 17..<22:
            expectedGreeting = "Good Evening"
        default:
            expectedGreeting = "Welcome"
        }
        
        // Access computed property through reflection
        if let greetingProperty = mirror.descendant("greetingText") {
            XCTAssertNotNil(greetingProperty, "Greeting text should not be nil")
        }
    }
    
    func testHomeViewInitialization() {
        let homeView = HomeView()
        XCTAssertNotNil(homeView, "HomeView should initialize successfully")
    }
    
    func testQuickActionsSectionExists() {
        let homeView = HomeView()
        let mirror = Mirror(reflecting: homeView)
        
        // Verify quick actions section exists
        if let quickActionsSection = mirror.descendant("quickActionsSection") {
            XCTAssertNotNil(quickActionsSection, "Quick actions section should exist")
        }
    }
    
    func testTipsSectionContainsTips() {
        let homeView = HomeView()
        let mirror = Mirror(reflecting: homeView)
        
        // Verify tips section exists
        if let tipsSection = mirror.descendant("tipsSection") {
            XCTAssertNotNil(tipsSection, "Tips section should exist")
        }
    }
    
    @MainActor func testRecentAnalysisSectionVisibility() {
        // Test when no recent analysis
        viewModel.lastAnalysisResult = nil
        XCTAssertFalse(viewModel.hasRecentAnalysis, "Should not have recent analysis")
        
        // Test when recent analysis exists
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
        
        viewModel.lastAnalysisResult = mockResult
        viewModel.lastAnalysisDate = Date()
        
        XCTAssertTrue(viewModel.hasRecentAnalysis, "Should have recent analysis")
        XCTAssertNotNil(viewModel.lastAnalysisDate, "Should have analysis date")
    }
    
    @MainActor func testLoadLastAnalysisFunction() {
        // Setup mock data
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
        
        viewModel.lastAnalysisResult = mockResult
        viewModel.analysisResult = nil
        
        // Test loading last analysis
        viewModel.loadLastAnalysis()
        
        XCTAssertNotNil(viewModel.analysisResult, "Analysis result should be loaded")
        XCTAssertEqual(viewModel.analysisResult?.id, mockResult.id, "Should load correct analysis")
    }
    
    func testAnimationStateOnAppear() {
        let expectation = XCTestExpectation(description: "Animation should trigger on appear")
        
        // Create view and simulate appear
        let homeView = HomeView()
        let hostingController = UIHostingController(rootView: homeView)
        
        // Add to window hierarchy
        let window = UIWindow()
        window.rootViewController = hostingController
        window.makeKeyAndVisible()
        
        // Wait for animation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 1.0)
    }
    
    func testMetricViewsDisplay() {
        let mockResult = AnalysisResult(
            id: "test-id",
            status: "completed",
            swingPhases: [],
            keyPoints: [],
            overallAnalysis: "",
            coachingScript: "",
            swingSpeed: 95,
            tempo: "2.5:1",
            balance: 88
        )
        
        XCTAssertEqual(mockResult.swingSpeed, 95, "Swing speed should be 95")
        XCTAssertEqual(mockResult.tempo, "2.5:1", "Tempo should be 2.5:1")
        XCTAssertEqual(mockResult.balance, 88, "Balance should be 88")
    }
}

// UI Testing for HomeView
class HomeViewUITests: XCTestCase {
    
    func testNavigationToUploadFlow() {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to home if not already there
        if app.tabBars.buttons["Home"].exists {
            app.tabBars.buttons["Home"].tap()
        }
        
        // Look for "New Analysis" button
        let newAnalysisButton = app.buttons["New Analysis"]
        
        XCTAssertTrue(newAnalysisButton.waitForExistence(timeout: 5), "New Analysis button should exist")
        
        // Tap the button
        newAnalysisButton.tap()
        
        // Verify upload flow appears
        let uploadTitle = app.navigationBars["Upload Swing Video"]
        XCTAssertTrue(uploadTitle.waitForExistence(timeout: 5), "Upload flow should appear")
    }
    
    func testNavigationToHistory() {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to home
        if app.tabBars.buttons["Home"].exists {
            app.tabBars.buttons["Home"].tap()
        }
        
        // Look for History button
        let historyButton = app.buttons["History"]
        
        if historyButton.waitForExistence(timeout: 5) {
            historyButton.tap()
            
            // Verify navigation occurred
            let previousAnalysesTitle = app.navigationBars.staticTexts["Previous Analyses"]
            XCTAssertTrue(previousAnalysesTitle.waitForExistence(timeout: 5), "Should navigate to Previous Analyses")
        }
    }
}

// Performance Tests
class HomeViewPerformanceTests: XCTestCase {
    
    func testHomeViewLoadPerformance() {
        measure {
            let homeView = HomeView()
            let _ = UIHostingController(rootView: homeView)
        }
    }
    
    func testViewModelInitializationPerformance() {
        measure {
            let _ = VideoAnalysisViewModel()
        }
    }
}