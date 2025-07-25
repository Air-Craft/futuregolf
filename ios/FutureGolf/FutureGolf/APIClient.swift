import Foundation

class APIClient {
    private let baseURL = "http://192.168.1.114:8000/api/v1"
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
            body.append("Content-Disposition: form-data; name=\"view_type\"\r\n\r\n".data(using: .utf8)!)
            body.append("face-on\r\n".data(using: .utf8)!)
            
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"golfer_handedness\"\r\n\r\n".data(using: .utf8)!)
            body.append("right\r\n".data(using: .utf8)!)
            
            body.append("--\(boundary)--\r\n".data(using: .utf8)!)
            
            request.httpBody = body
            
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                throw APIError.uploadFailed
            }
            
            let uploadResponse = try JSONDecoder().decode(UploadResponse.self, from: data)
            
            return await pollForAnalysis(videoId: uploadResponse.id)
            
        } catch {
            print("API Error: \(error)")
            return nil
        }
    }
    
    private func pollForAnalysis(videoId: String) async -> AnalysisResult? {
        let maxAttempts = 60
        var attempts = 0
        
        while attempts < maxAttempts {
            do {
                let url = URL(string: "\(baseURL)/video-analysis/video/\(videoId)")!
                let (data, _) = try await session.data(from: url)
                
                let response = try JSONDecoder().decode(AnalysisResponse.self, from: data)
                
                if response.status == "completed" {
                    return AnalysisResult(
                        id: response.id,
                        status: response.status,
                        swingPhases: response.result?.swingPhases ?? [],
                        keyPoints: response.result?.keyPoints ?? [],
                        overallAnalysis: response.result?.overallAnalysis ?? "",
                        coachingScript: response.result?.coachingScript ?? ""
                    )
                } else if response.status == "failed" {
                    throw APIError.analysisFailed
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
    let id: String
    let status: String
    let message: String
}

struct AnalysisResponse: Codable {
    let id: String
    let status: String
    let result: AnalysisData?
}

struct AnalysisData: Codable {
    let swingPhases: [SwingPhase]
    let keyPoints: [String]
    let overallAnalysis: String
    let coachingScript: String
    
    enum CodingKeys: String, CodingKey {
        case swingPhases = "swing_phases"
        case keyPoints = "key_points"
        case overallAnalysis = "overall_analysis"
        case coachingScript = "coaching_script"
    }
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