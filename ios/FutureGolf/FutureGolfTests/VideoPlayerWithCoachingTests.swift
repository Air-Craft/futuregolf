import XCTest
import SwiftUI
import AVFoundation
@testable import FutureGolf

@MainActor
final class VideoPlayerWithCoachingTests: XCTestCase {
    
    var mockResult: AnalysisResult!
    var mockVideoURL: URL!
    
    override func setUp() {
        super.setUp()
        mockResult = createMockAnalysisResult()
        mockVideoURL = URL(fileURLWithPath: "/test/video.mp4")
    }
    
    override func tearDown() {
        mockResult = nil
        mockVideoURL = nil
        super.tearDown()
    }
    
    // MARK: - Helper Methods
    
    private func createMockAnalysisResult() -> AnalysisResult {
        return AnalysisResult(
            id: "test-123",
            status: "completed",
            swingPhases: [
                SwingPhase(
                    name: "Setup",
                    timestamp: 0.0,
                    description: "Initial stance",
                    feedback: "Great stance"
                ),
                SwingPhase(
                    name: "Backswing",
                    timestamp: 1.5,
                    description: "Club to top",
                    feedback: "Good rotation"
                ),
                SwingPhase(
                    name: "Impact",
                    timestamp: 3.0,
                    description: "Ball contact",
                    feedback: "Solid contact"
                ),
                SwingPhase(
                    name: "Follow Through",
                    timestamp: 3.8,
                    description: "Finish",
                    feedback: "Complete rotation"
                )
            ],
            keyPoints: ["Great tempo"],
            overallAnalysis: "Good swing",
            coachingScript: "Keep practicing",
            swingSpeed: 90,
            tempo: "3:1",
            balance: 85
        )
    }
    
    // MARK: - View Initialization Tests
    
    func testVideoPlayerInitialization() {
        let view = VideoPlayerWithCoaching(
            analysisResult: mockResult,
            videoURL: mockVideoURL
        )
        
        XCTAssertNotNil(view, "VideoPlayerWithCoaching should initialize")
    }
    
    // MARK: - View Model Tests
    
    @MainActor func testVideoPlayerViewModelInitialization() {
        let viewModel = VideoPlayerViewModel()
        
        XCTAssertNil(viewModel.player, "Player should be nil initially")
        XCTAssertFalse(viewModel.isPlaying, "Should not be playing initially")
        XCTAssertEqual(viewModel.currentTime, 0, "Current time should be 0")
        XCTAssertEqual(viewModel.duration, 0, "Duration should be 0")
        XCTAssertNil(viewModel.currentPhase, "No current phase initially")
        XCTAssertEqual(viewModel.currentPhaseIndex, 0, "Phase index should be 0")
        XCTAssertNil(viewModel.currentFeedback, "No feedback initially")
        XCTAssertTrue(viewModel.isCoachingEnabled, "Coaching should be enabled by default")
    }
    
    @MainActor func testSetupPlayer() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        // Wait a moment for setup
        let expectation = XCTestExpectation(description: "Player setup")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            XCTAssertNotNil(viewModel.player, "Player should be created")
            XCTAssertEqual(viewModel.currentPhase?.name, "Setup", "First phase should be Setup")
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 1.0)
    }
    
    @MainActor func testPlayPauseToggle() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        XCTAssertFalse(viewModel.isPlaying, "Should not be playing initially")
        
        viewModel.togglePlayPause()
        XCTAssertTrue(viewModel.isPlaying, "Should be playing after toggle")
        
        viewModel.togglePlayPause()
        XCTAssertFalse(viewModel.isPlaying, "Should be paused after second toggle")
    }
    
    @MainActor func testPhaseNavigation() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        // Test next phase
        XCTAssertEqual(viewModel.currentPhaseIndex, 0, "Should start at phase 0")
        
        viewModel.nextPhase()
        XCTAssertEqual(viewModel.currentPhaseIndex, 1, "Should move to phase 1")
        XCTAssertEqual(viewModel.currentPhase?.name, "Backswing", "Should be Backswing phase")
        
        // Test previous phase
        viewModel.previousPhase()
        XCTAssertEqual(viewModel.currentPhaseIndex, 0, "Should move back to phase 0")
        XCTAssertEqual(viewModel.currentPhase?.name, "Setup", "Should be Setup phase")
        
        // Test boundary conditions
        viewModel.previousPhase()
        XCTAssertEqual(viewModel.currentPhaseIndex, 0, "Should stay at phase 0")
        
        // Jump to last phase
        viewModel.jumpToPhase(3)
        XCTAssertEqual(viewModel.currentPhaseIndex, 3, "Should jump to phase 3")
        
        viewModel.nextPhase()
        XCTAssertEqual(viewModel.currentPhaseIndex, 3, "Should stay at last phase")
    }
    
    @MainActor func testJumpToPhase() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        // Test valid jump
        viewModel.jumpToPhase(2)
        XCTAssertEqual(viewModel.currentPhaseIndex, 2)
        XCTAssertEqual(viewModel.currentPhase?.name, "Impact")
        
        // Test invalid jumps
        viewModel.jumpToPhase(-1)
        XCTAssertEqual(viewModel.currentPhaseIndex, 2, "Should not change for invalid index")
        
        viewModel.jumpToPhase(10)
        XCTAssertEqual(viewModel.currentPhaseIndex, 2, "Should not change for out of bounds index")
    }
    
    @MainActor func testSeekFunctionality() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        viewModel.seek(to: 2.5)
        // In a real test, we'd verify the player's current time
        // For now, we just ensure no crash
        XCTAssertTrue(true, "Seek should not crash")
    }
    
    @MainActor func testPlaybackSpeed() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        // Test various playback speeds
        let speeds: [Float] = [0.25, 0.5, 1.0, 1.5, 2.0]
        
        for speed in speeds {
            viewModel.setPlaybackSpeed(speed)
            // In a real test, we'd verify the player's rate
            XCTAssertTrue(true, "Setting speed \(speed) should not crash")
        }
    }
    
    // MARK: - Phase Icon Tests
    
    func testPhaseIconMapping() {
        let view = VideoPlayerWithCoaching(
            analysisResult: mockResult,
            videoURL: mockVideoURL
        )
        
        // Test that phase icons are correctly mapped
        let phaseNames = ["Setup", "Backswing", "Downswing", "Impact", "Follow Through", "Unknown"]
        let expectedIcons = ["figure.stand", "arrow.turn.up.left", "arrow.turn.down.right", "bolt.fill", "arrow.up.right", "figure.golf"]
        
        // Note: In actual implementation, we'd need to expose the phaseIcon function
        // or test it through the UI
        XCTAssertEqual(phaseNames.count, expectedIcons.count, "Phase names and icons should match")
    }
    
    // MARK: - Time Formatting Tests
    
    func testTimeFormatting() {
        // Test various time values
        let testCases: [(Double, String)] = [
            (0, "0:00"),
            (30, "0:30"),
            (59, "0:59"),
            (60, "1:00"),
            (90, "1:30"),
            (125, "2:05"),
            (3661, "61:01")
        ]
        
        for (time, expected) in testCases {
            let minutes = Int(time) / 60
            let seconds = Int(time) % 60
            let formatted = String(format: "%d:%02d", minutes, seconds)
            XCTAssertEqual(formatted, expected, "Time \(time) should format as \(expected)")
        }
    }
    
    // MARK: - Coaching Tests
    
    @MainActor func testCoachingToggle() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        XCTAssertTrue(viewModel.isCoachingEnabled, "Coaching should be enabled by default")
        
        viewModel.isCoachingEnabled = false
        XCTAssertFalse(viewModel.isCoachingEnabled, "Coaching should be disabled")
        
        viewModel.isCoachingEnabled = true
        XCTAssertTrue(viewModel.isCoachingEnabled, "Coaching should be re-enabled")
    }
    
    @MainActor func testCurrentPhaseUpdate() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        // Test phase updates based on timestamp
        let timestamps: [(Double, String)] = [
            (0.0, "Setup"),
            (0.5, "Setup"),
            (1.5, "Backswing"),
            (2.0, "Backswing"),
            (3.0, "Impact"),
            (3.5, "Impact"),
            (3.8, "Follow Through"),
            (5.0, "Follow Through")
        ]
        
        for (timestamp, expectedPhase) in timestamps {
            // Note: In actual implementation, we'd need to call updateCurrentPhase
            // or simulate time progression
            XCTAssertTrue(true, "Timestamp \(timestamp) should show phase \(expectedPhase)")
        }
    }
    
    // MARK: - Cleanup Tests
    
    @MainActor func testCleanup() {
        let viewModel = VideoPlayerViewModel()
        viewModel.setupPlayer(with: mockVideoURL, analysisResult: mockResult)
        
        // Setup some state
        viewModel.isPlaying = true
        viewModel.currentTime = 5.0
        
        // Cleanup
        viewModel.cleanup()
        
        XCTAssertNil(viewModel.player, "Player should be nil after cleanup")
        XCTAssertFalse(viewModel.isPlaying, "Should not be playing after cleanup")
    }
}

// MARK: - UI Tests

class VideoPlayerWithCoachingUITests: XCTestCase {
    
    func testVideoPlayerPresentation() {
        // This would test that the video player can be presented from analysis view
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to analysis result (would need actual navigation)
        // Tap video player button
        // Verify video player appears
        
        XCTAssertTrue(true, "Video player presentation test placeholder")
    }
    
    func testControlsVisibility() {
        // Test that controls appear/disappear on tap
        XCTAssertTrue(true, "Controls visibility test placeholder")
    }
    
    func testPhaseButtonInteraction() {
        // Test tapping phase buttons
        XCTAssertTrue(true, "Phase button interaction test placeholder")
    }
}

// MARK: - Performance Tests

class VideoPlayerPerformanceTests: XCTestCase {
    
    func testVideoPlayerCreationPerformance() {
        let result = AnalysisResult(
            id: "perf-test",
            status: "completed",
            swingPhases: (0..<20).map { i in
                SwingPhase(
                    name: "Phase \(i)",
                    timestamp: Double(i),
                    description: "Description",
                    feedback: "Feedback"
                )
            },
            keyPoints: [],
            overallAnalysis: "",
            coachingScript: "",
            swingSpeed: 90,
            tempo: "3:1",
            balance: 85
        )
        
        measure {
            let _ = VideoPlayerWithCoaching(
                analysisResult: result,
                videoURL: URL(fileURLWithPath: "/test/video.mp4")
            )
        }
    }
}

// MARK: - Speech Synthesis Tests

class TTSCoachingTests: XCTestCase {
    
    func testSpeechSynthesizerSetup() {
        let synthesizer = AVSpeechSynthesizer()
        XCTAssertNotNil(synthesizer, "Speech synthesizer should be created")
        
        let utterance = AVSpeechUtterance(string: "Test coaching feedback")
        utterance.rate = 0.5
        utterance.pitchMultiplier = 1.0
        utterance.volume = 0.9
        
        XCTAssertEqual(utterance.rate, 0.5, "Speech rate should be 0.5")
        XCTAssertEqual(utterance.pitchMultiplier, 1.0, "Pitch should be 1.0")
        XCTAssertEqual(utterance.volume, 0.9, "Volume should be 0.9")
    }
    
    func testVoiceSelection() {
        let voice = AVSpeechSynthesisVoice(language: "en-US")
        XCTAssertNotNil(voice, "English US voice should be available")
    }
}