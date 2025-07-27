import Foundation

class APIClient {
    private let baseURL = "https://golf-swing-analysis-467208.web.app/api/v1"
    private let session = URLSession.shared
    
    func uploadAndAnalyzeVideo(url: URL) async -> AnalysisResult? {
        do {
            let videoData = try Data(contentsOf: url)
            
            var request = URLRequest(url: URL(string: "\(baseURL)/videos/upload")!)
            request.httpMethod = "POST"
            
            let boundary = UUID().uuidString
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
            
            var body = Data()
            
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"file\"; filename=\"video.mov\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: video/quicktime\r\n\r\n".data(using: .utf8)!)
            body.append(videoData)
            body.append("\r\n".data(using: .utf8)!)
            
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"user_id\"\r\n\r\n".data(using: .utf8)!)
            body.append("1\r\n".data(using: .utf8)!)
            
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"title\"\r\n\r\n".data(using: .utf8)!)
            body.append("Golf Swing Analysis\r\n".data(using: .utf8)!)
            
            body.append("--\(boundary)--\r\n".data(using: .utf8)!)
            
            request.httpBody = body
            
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                print("Upload failed with status: \((response as? HTTPURLResponse)?.statusCode ?? -1)")
                print("Response data: \(String(data: data, encoding: .utf8) ?? "")")
                throw APIError.uploadFailed
            }
            
            let uploadResponse = try JSONDecoder().decode(UploadResponse.self, from: data)
            
            // Trigger analysis
            await triggerAnalysis(videoId: uploadResponse.id)
            
            // Poll for results
            return await pollForAnalysis(videoId: uploadResponse.id)
            
        } catch {
            print("API Error: \(error)")
            return nil
        }
    }
    
    private func triggerAnalysis(videoId: String) async {
        do {
            var request = URLRequest(url: URL(string: "\(baseURL)/video-analysis/analyze/\(videoId)")!)
            request.httpMethod = "POST"
            
            let (_, response) = try await session.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                print("Analysis trigger status: \(httpResponse.statusCode)")
            }
        } catch {
            print("Failed to trigger analysis: \(error)")
        }
    }
    
    private func pollForAnalysis(videoId: String) async -> AnalysisResult? {
        let maxAttempts = 60
        var attempts = 0
        
        while attempts < maxAttempts {
            do {
                let url = URL(string: "\(baseURL)/video-analysis/video/\(videoId)")!
                let (data, _) = try await session.data(from: url)
                
                // Print raw response for debugging
                if let jsonString = String(data: data, encoding: .utf8) {
                    print("Analysis response: \(jsonString)")
                }
                
                let response = try JSONDecoder().decode(AnalysisResponse.self, from: data)
                
                if let analysis = response.analysis {
                    if analysis.status == "completed", let aiAnalysis = analysis.ai_analysis {
                        return AnalysisResult(
                            id: String(analysis.id),
                            status: analysis.status,
                            swingPhases: aiAnalysis.swingPhases,
                            keyPoints: aiAnalysis.keyPoints,
                            overallAnalysis: aiAnalysis.overallAnalysis,
                            coachingScript: aiAnalysis.coachingScript
                        )
                    } else if analysis.status == "failed" {
                        throw APIError.analysisFailed
                    }
                }
                
                try await Task.sleep(nanoseconds: 2_000_000_000)
                attempts += 1
                
            } catch {
                print("Polling error: \(error)")
                return nil
            }
        }
        
        return nil
    }
}

enum APIError: Error {
    case uploadFailed
    case analysisFailed
}

struct UploadResponse: Codable {
    let success: Bool
    let video_id: Int
    let status: String
    
    var id: String {
        return String(video_id)
    }
}

struct AnalysisResponse: Codable {
    let success: Bool
    let analysis: AnalysisInfo?
}

struct AnalysisInfo: Codable {
    let id: Int
    let status: String
    let ai_analysis: AnalysisData?
}

struct AnalysisData: Codable {
    let swings: [SwingAnalysis]?
    let summary: Summary?
    let coaching_script: CoachingScript?
    
    // Computed properties to match our UI expectations
    var swingPhases: [SwingPhase] {
        guard let firstSwing = swings?.first else { return [] }
        var phases: [SwingPhase] = []
        
        if let setup = firstSwing.phases?.setup {
            phases.append(SwingPhase(
                name: "Setup",
                startFrame: setup.start_frame ?? 0,
                endFrame: setup.end_frame ?? 0,
                keyObservations: firstSwing.comments ?? []
            ))
        }
        if let backswing = firstSwing.phases?.backswing {
            phases.append(SwingPhase(
                name: "Backswing", 
                startFrame: backswing.start_frame ?? 0,
                endFrame: backswing.end_frame ?? 0,
                keyObservations: []
            ))
        }
        if let downswing = firstSwing.phases?.downswing {
            phases.append(SwingPhase(
                name: "Downswing",
                startFrame: downswing.start_frame ?? 0,
                endFrame: downswing.end_frame ?? 0,
                keyObservations: []
            ))
        }
        if let followThrough = firstSwing.phases?.follow_through {
            phases.append(SwingPhase(
                name: "Follow Through",
                startFrame: followThrough.start_frame ?? 0,
                endFrame: followThrough.end_frame ?? 0,
                keyObservations: []
            ))
        }
        
        return phases
    }
    
    var keyPoints: [String] {
        var points: [String] = []
        if let highlights = summary?.highlights {
            points.append(contentsOf: highlights)
        }
        if let improvements = summary?.improvements {
            points.append(contentsOf: improvements)
        }
        return points
    }
    
    var overallAnalysis: String {
        var analysis = ""
        if let highlights = summary?.highlights {
            analysis += "Highlights:\n" + highlights.joined(separator: "\n")
        }
        if let improvements = summary?.improvements {
            if !analysis.isEmpty { analysis += "\n\n" }
            analysis += "Areas for Improvement:\n" + improvements.joined(separator: "\n")
        }
        return analysis
    }
    
    var coachingScript: String {
        guard let lines = coaching_script?.lines else { return "" }
        return lines.map { $0.text }.joined(separator: "\n\n")
    }
}

struct SwingAnalysis: Codable {
    let score: Int?
    let phases: SwingPhases?
    let comments: [String]?
}

struct SwingPhases: Codable {
    let setup: PhaseInfo?
    let backswing: PhaseInfo?
    let downswing: PhaseInfo?
    let follow_through: PhaseInfo?
}

struct PhaseInfo: Codable {
    let start_frame: Int?
    let end_frame: Int?
    let start_timestamp: Double?
    let end_timestamp: Double?
}

struct Summary: Codable {
    let highlights: [String]?
    let improvements: [String]?
}

struct CoachingScript: Codable {
    let lines: [CoachingLine]?
}

struct CoachingLine: Codable {
    let text: String
    let start_frame_number: Int
}

struct SwingPhase: Codable {
    let name: String
    let startFrame: Int
    let endFrame: Int
    let keyObservations: [String]
    
    enum CodingKeys: String, CodingKey {
        case name
        case startFrame = "start_frame"
        case endFrame = "end_frame"
        case keyObservations = "key_observations"
    }
}