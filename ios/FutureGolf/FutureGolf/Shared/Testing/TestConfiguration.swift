import Foundation
import SwiftUI
import Combine

/// Configuration for UI testing with mock data
struct TestConfiguration {
    static let shared = TestConfiguration()
    
    let isUITesting: Bool
    let analysisMode: AnalysisTestMode
    let connectivityState: ConnectivityTestState
    let shouldSimulateConnectionRestore: Bool
    
    private init() {
        let args = ProcessInfo.processInfo.arguments
        let env = ProcessInfo.processInfo.environment
        
        // Check if UI testing
        isUITesting = args.contains("--uitesting")
        
        // Determine analysis mode
        if let mode = env["ANALYSIS_MODE"] {
            switch mode {
            case "offline":
                analysisMode = .offline
            case "processing":
                analysisMode = .processing
            case "tts_caching":
                analysisMode = .ttsCaching
            case "tts_complete":
                analysisMode = .ttsComplete
            case "completed":
                analysisMode = .completed
            default:
                analysisMode = .processing
            }
        } else {
            analysisMode = .processing
        }
        
        // Determine connectivity state
        if let state = env["CONNECTIVITY_STATE"] {
            switch state {
            case "offline":
                connectivityState = .offline
            case "online":
                connectivityState = .online
            default:
                connectivityState = .online
            }
        } else {
            connectivityState = .online
        }
        
        // Check if should simulate connection restore
        shouldSimulateConnectionRestore = env["SIMULATE_CONNECTION_RESTORE"] == "true"
    }
    
    /// Create mock analysis result for testing
    func createMockAnalysisResult() -> AnalysisResult {
        // Load from test fixture
        if let url = Bundle.main.url(forResource: "test_analysis", withExtension: "json", subdirectory: "FutureGolfTestsShared/fixtures"),
           let _ = try? Data(contentsOf: url) {
            // Parse the test fixture JSON
            // For now, return a simple mock
        }
        
        return AnalysisResult(
            id: "test-analysis-001",
            status: "completed",
            swingPhases: [
                SwingPhase(name: "Setup", timestamp: 1.0, description: "Initial stance", feedback: "Good posture, maintain spine angle"),
                SwingPhase(name: "Backswing", timestamp: 1.5, description: "Club to top", feedback: "Full shoulder turn achieved"),
                SwingPhase(name: "Downswing", timestamp: 3.0, description: "Transition", feedback: "Smooth transition, watch hip rotation"),
                SwingPhase(name: "Impact", timestamp: 3.8, description: "Ball contact", feedback: "Solid contact, hands ahead of ball"),
                SwingPhase(name: "Follow Through", timestamp: 4.5, description: "Finish", feedback: "Complete the rotation")
            ],
            keyPoints: ["Great tempo", "Solid impact position", "Good balance throughout"],
            overallAnalysis: "Your swing shows good fundamentals with room for improvement in hip rotation and follow through. Focus on maintaining your spine angle throughout the swing.",
            coachingScript: "Let's work on your hip rotation. Notice how your hips should lead the downswing. Try to feel the rotation starting from the ground up.",
            swingSpeed: 95,
            tempo: "3:1",
            balance: 88
        )
    }
    
    /// Check if running E2E tests
    var isE2ETesting: Bool {
        return isUITesting && ProcessInfo.processInfo.arguments.contains("--swingAnalysisE2ETest")
    }
}

enum AnalysisTestMode {
    case offline
    case processing
    case ttsCaching
    case ttsComplete
    case completed
}

enum ConnectivityTestState {
    case offline
    case online
}

// MARK: - Mock Connectivity Service for Testing

@MainActor
class MockConnectivityService: ObservableObject {
    static let shared = MockConnectivityService()
    
    @Published var isConnected: Bool
    
    private init() {
        let config = TestConfiguration.shared
        self.isConnected = config.connectivityState == .online
        
        // Simulate connection restore if needed
        if config.shouldSimulateConnectionRestore {
            Task {
                try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
                self.isConnected = true
                ToastManager.shared.show("Connected", type: .success, duration: 2.0)
            }
        }
    }
    
    func simulateConnectionLoss() {
        isConnected = false
        ToastManager.shared.show("Waiting for connectivity...", type: .warning, duration: .infinity, id: "connectivity")
    }
    
    func simulateConnectionRestored() {
        isConnected = true
        ToastManager.shared.dismiss(id: "connectivity")
        ToastManager.shared.show("Connected", type: .success, duration: 2.0)
    }
}