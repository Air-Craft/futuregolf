import XCTest
import SwiftUI
import AVFoundation
@testable import FutureGolf

@MainActor
final class RecordingScreenTests: XCTestCase {
    
    var recordingViewModel: RecordingViewModel!
    var mockTTSService: MockTTSService!
    
    override func setUp() {
        super.setUp()
        recordingViewModel = RecordingViewModel()
        mockTTSService = MockTTSService()
        recordingViewModel.ttsService = mockTTSService
    }
    
    override func tearDown() {
        recordingViewModel = nil
        mockTTSService = nil
        super.tearDown()
    }
    
    // MARK: - Camera Setup and Configuration Tests
    
    func testCameraConfiguration() {
        XCTAssertEqual(recordingViewModel.targetFrameRate, 120, "Target frame rate should be 120fps")
        XCTAssertEqual(recordingViewModel.minFrameRate, 60, "Minimum frame rate should be 60fps")
        XCTAssertEqual(recordingViewModel.resolution, .hd1920x1080, "Resolution should be 1080p")
        XCTAssertEqual(recordingViewModel.videoFormat, .mp4, "Format should be MP4")
        XCTAssertTrue(recordingViewModel.isPortraitMode, "Should be in portrait mode")
        XCTAssertEqual(recordingViewModel.cameraPosition, .back, "Should default to rear camera")
    }
    
    func testCameraPositionSwitch() {
        XCTAssertEqual(recordingViewModel.cameraPosition, .back, "Should start with rear camera")
        
        recordingViewModel.switchCamera()
        XCTAssertEqual(recordingViewModel.cameraPosition, .front, "Should switch to front camera")
        
        recordingViewModel.switchCamera()
        XCTAssertEqual(recordingViewModel.cameraPosition, .back, "Should switch back to rear camera")
    }
    
    func testAutoFocusConfiguration() {
        XCTAssertTrue(recordingViewModel.isAutoFocusEnabled, "Auto focus should be enabled")
        XCTAssertEqual(recordingViewModel.focusMode, .continuousAutoFocus, "Should use continuous auto focus")
    }
    
    // MARK: - Recording Phase Tests
    
    func testRecordingPhases() {
        XCTAssertEqual(recordingViewModel.currentPhase, .setup, "Should start in setup phase")
        
        recordingViewModel.startRecording()
        XCTAssertEqual(recordingViewModel.currentPhase, .recording, "Should transition to recording phase")
        
        recordingViewModel.finishRecording()
        XCTAssertEqual(recordingViewModel.currentPhase, .processing, "Should transition to processing phase")
    }
    
    func testSetupPhaseUI() {
        recordingViewModel.currentPhase = .setup
        
        XCTAssertTrue(recordingViewModel.showPositioningIndicator, "Should show positioning indicator in setup")
        XCTAssertFalse(recordingViewModel.showProgressCircles, "Should not show progress circles in setup")
        XCTAssertFalse(recordingViewModel.isRecording, "Should not be recording in setup")
    }
    
    func testRecordingPhaseUI() {
        recordingViewModel.currentPhase = .recording
        
        XCTAssertFalse(recordingViewModel.showPositioningIndicator, "Should hide positioning indicator during recording")
        XCTAssertTrue(recordingViewModel.showProgressCircles, "Should show progress circles during recording")
        XCTAssertTrue(recordingViewModel.isRecording, "Should be recording")
    }
    
    // MARK: - Voice Begin Signal Tests
    
    func testVoiceBeginSignalDetection() {
        let expectation = XCTestExpectation(description: "Voice signal should trigger recording")
        
        recordingViewModel.onRecordingStarted = {
            expectation.fulfill()
        }
        
        // Simulate voice detection
        recordingViewModel.processVoiceInput("I'm ready to begin recording")
        
        wait(for: [expectation], timeout: 2.0)
        XCTAssertEqual(recordingViewModel.currentPhase, .recording, "Should start recording after voice signal")
    }
    
    func testVoiceSignalThreshold() {
        // Test confidence threshold
        recordingViewModel.processVoiceInput("maybe")
        XCTAssertEqual(recordingViewModel.currentPhase, .setup, "Low confidence should not trigger recording")
        
        recordingViewModel.processVoiceInput("yes I'm ready to begin")
        XCTAssertEqual(recordingViewModel.currentPhase, .recording, "High confidence should trigger recording")
    }
    
    // MARK: - Swing Detection Tests
    
    func testSwingCountInitialization() {
        XCTAssertEqual(recordingViewModel.swingCount, 0, "Should start with 0 swings")
        XCTAssertEqual(recordingViewModel.targetSwingCount, 3, "Should target 3 swings")
    }
    
    func testSwingDetection() {
        recordingViewModel.currentPhase = .recording
        
        recordingViewModel.processSwingDetection(isSwingDetected: true)
        XCTAssertEqual(recordingViewModel.swingCount, 1, "Should increment swing count")
        
        recordingViewModel.processSwingDetection(isSwingDetected: true)
        XCTAssertEqual(recordingViewModel.swingCount, 2, "Should increment to 2 swings")
        
        recordingViewModel.processSwingDetection(isSwingDetected: true)
        XCTAssertEqual(recordingViewModel.swingCount, 3, "Should reach target swing count")
        XCTAssertEqual(recordingViewModel.currentPhase, .processing, "Should transition to processing after 3 swings")
    }
    
    func testProgressCirclesUpdate() {
        recordingViewModel.currentPhase = .recording
        
        XCTAssertEqual(recordingViewModel.progressCircles.count, 3, "Should have 3 progress circles")
        XCTAssertTrue(recordingViewModel.progressCircles.allSatisfy { !$0.isCompleted }, "All circles should start incomplete")
        
        recordingViewModel.processSwingDetection(isSwingDetected: true)
        XCTAssertTrue(recordingViewModel.progressCircles[0].isCompleted, "First circle should be completed")
        XCTAssertFalse(recordingViewModel.progressCircles[1].isCompleted, "Second circle should not be completed")
        
        recordingViewModel.processSwingDetection(isSwingDetected: true)
        XCTAssertTrue(recordingViewModel.progressCircles[1].isCompleted, "Second circle should be completed")
    }
    
    // MARK: - TTS Audio Feedback Tests
    
    func testStartRecordingTTS() {
        recordingViewModel.startRecording()
        
        XCTAssertTrue(mockTTSService.spokenTexts.contains("Great. I'm now recording. Begin swinging when you're ready."), 
                     "Should speak start confirmation")
    }
    
    func testSwingCountTTS() {
        recordingViewModel.currentPhase = .recording
        recordingViewModel.swingCount = 0
        
        recordingViewModel.processSwingDetection(isSwingDetected: true)
        XCTAssertTrue(mockTTSService.spokenTexts.contains("Great. Take another when you're ready."), 
                     "Should speak first swing feedback")
        
        recordingViewModel.processSwingDetection(isSwingDetected: true)
        XCTAssertTrue(mockTTSService.spokenTexts.contains("Ok one more to go."), 
                     "Should speak second swing feedback")
    }
    
    func testCompletionTTS() {
        recordingViewModel.finishRecording()
        
        XCTAssertTrue(mockTTSService.spokenTexts.contains("That's great. I'll get to work analyzing your swings."), 
                     "Should speak completion message")
    }
    
    func testOvertimeTTS() {
        recordingViewModel.handleRecordingTimeout()
        
        XCTAssertTrue(mockTTSService.spokenTexts.contains("That's taken longer than I had planned. I'll analyze what we have."), 
                     "Should speak overtime message")
    }
    
    // MARK: - Timer and Timeout Tests
    
    func testRecordingTimer() {
        let expectation = XCTestExpectation(description: "Timer should update recording time")
        
        recordingViewModel.onTimeUpdate = { time in
            if time > 0 {
                expectation.fulfill()
            }
        }
        
        recordingViewModel.startRecording()
        
        wait(for: [expectation], timeout: 1.0)
        XCTAssertGreaterThan(recordingViewModel.recordingTime, 0, "Recording time should be greater than 0")
    }
    
    func testRecordingTimeout() {
        let expectation = XCTestExpectation(description: "Should timeout after threshold")
        
        recordingViewModel.recordingTimeout = 1.0 // 1 second for testing
        recordingViewModel.onTimeout = {
            expectation.fulfill()
        }
        
        recordingViewModel.startRecording()
        
        wait(for: [expectation], timeout: 2.0)
        XCTAssertEqual(recordingViewModel.currentPhase, .processing, "Should transition to processing on timeout")
    }
    
    // MARK: - Error Handling Tests
    
    func testCameraPermissionError() {
        recordingViewModel.handleCameraPermissionDenied()
        
        XCTAssertEqual(recordingViewModel.errorType, .cameraPermissionDenied, "Should set camera permission error")
        XCTAssertEqual(recordingViewModel.currentPhase, .error, "Should transition to error phase")
    }
    
    func testInsufficientStorageError() {
        recordingViewModel.handleInsufficientStorage()
        
        XCTAssertEqual(recordingViewModel.errorType, .insufficientStorage, "Should set storage error")
        XCTAssertEqual(recordingViewModel.currentPhase, .error, "Should transition to error phase")
    }
    
    func testCameraHardwareError() {
        recordingViewModel.handleCameraHardwareError()
        
        XCTAssertEqual(recordingViewModel.errorType, .cameraHardwareError, "Should set hardware error")
        XCTAssertEqual(recordingViewModel.currentPhase, .error, "Should transition to error phase")
    }
    
    // MARK: - Cancel Button Tests
    
    func testCancelButton() {
        recordingViewModel.currentPhase = .recording
        
        let expectation = XCTestExpectation(description: "Should handle cancel action")
        recordingViewModel.onCancelRequested = {
            expectation.fulfill()
        }
        
        recordingViewModel.handleCancelPressed()
        
        wait(for: [expectation], timeout: 1.0)
        XCTAssertTrue(mockTTSService.wasStopped, "Should stop TTS on cancel")
    }
    
    // MARK: - Left-handed Mode Tests
    
    func testLeftHandedModeToggle() {
        XCTAssertFalse(recordingViewModel.isLeftHandedMode, "Should default to right-handed")
        
        recordingViewModel.toggleLeftHandedMode()
        XCTAssertTrue(recordingViewModel.isLeftHandedMode, "Should switch to left-handed mode")
        
        recordingViewModel.toggleLeftHandedMode()
        XCTAssertFalse(recordingViewModel.isLeftHandedMode, "Should switch back to right-handed mode")
    }
    
    // MARK: - Still Image Processing Tests
    
    func testStillImageCapture() {
        recordingViewModel.currentPhase = .recording
        
        let expectation = XCTestExpectation(description: "Should capture still image")
        recordingViewModel.onStillCaptured = { image in
            XCTAssertNotNil(image, "Should capture still image")
            expectation.fulfill()
        }
        
        recordingViewModel.captureStillForAnalysis()
        
        wait(for: [expectation], timeout: 1.0)
    }
    
    func testStillImageInterval() {
        XCTAssertEqual(recordingViewModel.stillCaptureInterval, 0.25, "Should capture still every 0.25 seconds")
    }
}

// MARK: - UI Tests

class RecordingScreenUITests: XCTestCase {
    
    func testRecordingScreenNavigation() {
        let app = XCUIApplication()
        app.launch()
        
        // Tap "Analyze My Swing" button
        let analyzeButton = app.buttons["Analyze My Swing"]
        XCTAssertTrue(analyzeButton.waitForExistence(timeout: 5), "Analyze My Swing button should exist")
        
        analyzeButton.tap()
        
        // Verify recording screen appears
        let recordingScreen = app.otherElements["RecordingScreen"]
        XCTAssertTrue(recordingScreen.waitForExistence(timeout: 5), "Recording screen should appear")
    }
    
    func testCancelButtonExists() {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to recording screen
        app.buttons["Analyze My Swing"].tap()
        
        // Check cancel button exists in upper left
        let cancelButton = app.buttons["Cancel"]
        XCTAssertTrue(cancelButton.waitForExistence(timeout: 5), "Cancel button should exist")
    }
    
    func testCameraSwitchButton() {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to recording screen
        app.buttons["Analyze My Swing"].tap()
        
        // Check camera switch button exists
        let cameraSwitchButton = app.buttons["Switch Camera"]
        XCTAssertTrue(cameraSwitchButton.waitForExistence(timeout: 5), "Camera switch button should exist")
    }
    
    func testLeftHandedToggle() {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to recording screen
        app.buttons["Analyze My Swing"].tap()
        
        // Check left-handed toggle exists
        let leftHandedToggle = app.buttons["Left-Handed Mode"]
        XCTAssertTrue(leftHandedToggle.waitForExistence(timeout: 5), "Left-handed toggle should exist")
    }
    
    func testProgressCirclesAppearDuringRecording() {
        let app = XCUIApplication()
        app.launch()
        
        // Navigate to recording screen and start recording
        app.buttons["Analyze My Swing"].tap()
        
        // Wait for setup phase, then trigger recording
        // (This would require voice input simulation or manual trigger in actual test)
        
        // Check progress circles appear
        let progressCircles = app.otherElements["ProgressCircles"]
        // Note: This test would need to be completed with actual recording flow
    }
}

// MARK: - Performance Tests

class RecordingScreenPerformanceTests: XCTestCase {
    
    func testRecordingViewModelInitializationPerformance() {
        measure {
            let _ = RecordingViewModel()
        }
    }
    
    func testStillImageProcessingPerformance() {
        let viewModel = RecordingViewModel()
        let testImage = createTestImage()
        
        measure {
            viewModel.processStillImage(testImage)
        }
    }
    
    func testVoiceProcessingPerformance() {
        let viewModel = RecordingViewModel()
        
        measure {
            viewModel.processVoiceInput("I'm ready to begin recording")
        }
    }
    
    private func createTestImage() -> UIImage {
        let size = CGSize(width: 100, height: 100)
        UIGraphicsBeginImageContext(size)
        UIColor.blue.setFill()
        UIRectFill(CGRect(origin: .zero, size: size))
        let image = UIGraphicsGetImageFromCurrentImageContext()!
        UIGraphicsEndImageContext()
        return image
    }
}

// MARK: - Mock TTS Service

class MockTTSService: ObservableObject {
    var spokenTexts: [String] = []
    var wasStopped = false
    var isPlaying = false
    var isLoading = false
    
    func speakText(_ text: String, completion: @escaping (Bool) -> Void = { _ in }) {
        spokenTexts.append(text)
        completion(true)
    }
    
    func stopSpeaking() {
        wasStopped = true
        isPlaying = false
    }
    
    func pauseSpeaking() {
        isPlaying = false
    }
    
    func resumeSpeaking() {
        isPlaying = true
    }
    
    var isSpeaking: Bool {
        return isPlaying || isLoading
    }
}
