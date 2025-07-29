import XCTest
@testable import FutureGolf

class APIClientTests: XCTestCase {
    
    var apiClient: APIClient!
    
    override func setUp() {
        super.setUp()
        apiClient = APIClient()
    }
    
    override func tearDown() {
        apiClient = nil
        super.tearDown()
    }
    
    // MARK: - Model Tests
    
    func testUploadResponseDecoding() throws {
        let json = """
        {
            "success": true,
            "video_id": 123,
            "status": "uploaded"
        }
        """
        
        let data = json.data(using: .utf8)!
        let response = try JSONDecoder().decode(UploadResponse.self, from: data)
        
        XCTAssertTrue(response.success)
        XCTAssertEqual(response.video_id, 123)
        XCTAssertEqual(response.status, "uploaded")
        XCTAssertEqual(response.id, "123")
    }
    
    func testAnalysisResponseDecoding() throws {
        let json = """
        {
            "success": true,
            "analysis": {
                "id": 456,
                "status": "completed",
                "ai_analysis": {
                    "swings": [{
                        "score": 85,
                        "phases": {
                            "setup": {
                                "start_frame": 0,
                                "end_frame": 30,
                                "start_timestamp": 0.0,
                                "end_timestamp": 1.0
                            }
                        },
                        "comments": ["Good setup position"],
                        "metrics": {
                            "clubheadSpeed": 95,
                            "backswingTime": 1.2,
                            "downswingTime": 0.4,
                            "balanceScore": 88
                        }
                    }],
                    "summary": {
                        "highlights": ["Good posture", "Smooth transition"],
                        "improvements": ["Work on follow through", "Increase hip rotation"]
                    },
                    "coaching_script": {
                        "lines": [
                            {"text": "Great swing!", "start_frame_number": 0},
                            {"text": "Focus on your follow through", "start_frame_number": 120}
                        ]
                    }
                }
            }
        }
        """
        
        let data = json.data(using: .utf8)!
        let response = try JSONDecoder().decode(AnalysisResponse.self, from: data)
        
        XCTAssertTrue(response.success)
        XCTAssertNotNil(response.analysis)
        XCTAssertEqual(response.analysis?.id, 456)
        XCTAssertEqual(response.analysis?.status, "completed")
        
        // Test computed properties
        let aiAnalysis = response.analysis?.ai_analysis
        XCTAssertNotNil(aiAnalysis)
        XCTAssertEqual(aiAnalysis?.swingSpeed, 95)
        XCTAssertEqual(aiAnalysis?.tempo, "3.0:1")
        XCTAssertEqual(aiAnalysis?.balance, 88)
        
        // Test swing phases
        XCTAssertFalse(aiAnalysis?.swingPhases.isEmpty ?? true)
        XCTAssertEqual(aiAnalysis?.swingPhases.first?.name, "Setup")
        
        // Test key points
        XCTAssertEqual(aiAnalysis?.keyPoints.count, 4)
        XCTAssertTrue(aiAnalysis?.keyPoints.contains("Good posture") ?? false)
        
        // Test coaching script
        XCTAssertFalse(aiAnalysis?.coachingScript.isEmpty ?? true)
        XCTAssertTrue(aiAnalysis?.coachingScript.contains("Great swing!") ?? false)
    }
    
    func testSwingMetricsCalculation() throws {
        let metrics = SwingMetrics(
            clubheadSpeed: 102,
            backswingTime: 1.5,
            downswingTime: 0.5,
            balanceScore: 92
        )
        
        let analysisData = AnalysisData(
            swings: [SwingAnalysis(
                score: 90,
                phases: nil,
                comments: nil,
                metrics: metrics
            )],
            summary: nil,
            coaching_script: nil
        )
        
        XCTAssertEqual(analysisData.swingSpeed, 102)
        XCTAssertEqual(analysisData.tempo, "3.0:1")
        XCTAssertEqual(analysisData.balance, 92)
    }
    
    func testDefaultMetricsValues() {
        let analysisData = AnalysisData(
            swings: nil,
            summary: nil,
            coaching_script: nil
        )
        
        // Test default values
        XCTAssertEqual(analysisData.swingSpeed, 85)
        XCTAssertEqual(analysisData.tempo, "3:1")
        XCTAssertEqual(analysisData.balance, 88)
    }
    
    // MARK: - Error Handling Tests
    
    func testAPIErrorTypes() {
        XCTAssertNotNil(APIError.uploadFailed)
        XCTAssertNotNil(APIError.analysisFailed)
    }
    
    func testAnalysisResultInitialization() {
        let result = AnalysisResult(
            id: "test-123",
            status: "completed",
            swingPhases: [
                SwingPhase(
                    name: "Setup",
                    timestamp: 0.0,
                    description: "Initial position",
                    feedback: "Good stance"
                )
            ],
            keyPoints: ["Point 1", "Point 2"],
            overallAnalysis: "Great swing overall",
            coachingScript: "Keep up the good work",
            swingSpeed: 98,
            tempo: "2.8:1",
            balance: 91
        )
        
        XCTAssertEqual(result.id, "test-123")
        XCTAssertEqual(result.status, "completed")
        XCTAssertEqual(result.swingPhases.count, 1)
        XCTAssertEqual(result.keyPoints.count, 2)
        XCTAssertEqual(result.swingSpeed, 98)
        XCTAssertEqual(result.tempo, "2.8:1")
        XCTAssertEqual(result.balance, 91)
    }
    
    // MARK: - Phase Transformation Tests
    
    func testSwingPhaseTransformation() {
        let phaseInfo = PhaseInfo(
            start_frame: 0,
            end_frame: 30,
            start_timestamp: 0.0,
            end_timestamp: 1.0
        )
        
        let swingAnalysis = SwingAnalysis(
            score: 85,
            phases: SwingPhases(
                setup: phaseInfo,
                backswing: nil,
                downswing: nil,
                follow_through: nil
            ),
            comments: ["Test comment"],
            metrics: nil
        )
        
        let analysisData = AnalysisData(
            swings: [swingAnalysis],
            summary: nil,
            coaching_script: nil
        )
        
        let phases = analysisData.swingPhases
        XCTAssertEqual(phases.count, 1)
        XCTAssertEqual(phases.first?.name, "Setup")
        XCTAssertEqual(phases.first?.timestamp, 0.0)
        XCTAssertEqual(phases.first?.feedback, "Test comment")
    }
    
    func testAllPhasesTransformation() {
        let phases = SwingPhases(
            setup: PhaseInfo(start_frame: 0, end_frame: 30, start_timestamp: 0.0, end_timestamp: 1.0),
            backswing: PhaseInfo(start_frame: 31, end_frame: 60, start_timestamp: 1.0, end_timestamp: 2.0),
            downswing: PhaseInfo(start_frame: 61, end_frame: 90, start_timestamp: 2.0, end_timestamp: 3.0),
            follow_through: PhaseInfo(start_frame: 91, end_frame: 120, start_timestamp: 3.0, end_timestamp: 4.0)
        )
        
        let swingAnalysis = SwingAnalysis(
            score: 90,
            phases: phases,
            comments: nil,
            metrics: nil
        )
        
        let analysisData = AnalysisData(
            swings: [swingAnalysis],
            summary: nil,
            coaching_script: nil
        )
        
        let swingPhases = analysisData.swingPhases
        XCTAssertEqual(swingPhases.count, 4)
        
        let phaseNames = swingPhases.map { $0.name }
        XCTAssertEqual(phaseNames, ["Setup", "Backswing", "Downswing", "Follow Through"])
    }
}

// Note: Network mocking removed as APIClient doesn't support dependency injection
// These tests focus on JSON decoding and model transformation