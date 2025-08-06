import Foundation
import SwiftUI

enum NavigationRoute: Hashable {
    case recording
    case swingAnalysis(videoURL: URL, analysisId: String?)
    case previousAnalyses
    case tmpCoachingDemo
    
    // Custom Hashable implementation
    func hash(into hasher: inout Hasher) {
        switch self {
        case .recording:
            hasher.combine("recording")
        case .swingAnalysis(let url, let id):
            hasher.combine("swingAnalysis")
            hasher.combine(url)
            hasher.combine(id)
        case .previousAnalyses:
            hasher.combine("previousAnalyses")
        case .tmpCoachingDemo:
            hasher.combine("tmpCoachingDemo")
        }
        
    }
    
    // Custom Equatable implementation
    static func == (lhs: NavigationRoute, rhs: NavigationRoute) -> Bool {
        switch (lhs, rhs) {
        case (.recording, .recording):
            return true
        case (.swingAnalysis(let lhsURL, let lhsId), .swingAnalysis(let rhsURL, let rhsId)):
            return lhsURL == rhsURL && lhsId == rhsId
        default:
            return false
        }
    }
}

@MainActor
@Observable

class AppState {
    var path = NavigationPath()
    
    var currentRecordingId: String?
    var currentRecordingURL: URL?

    func clearCurrentRecording() {
        currentRecordingId = nil
        currentRecordingURL = nil
    }

    // MARK: - Navigation Methods
    
    func navigateTo(_ route: NavigationRoute) {
//        // Replace recording screen with analysis
//        if let lastRoute = path.last  {
//            if case .recording = lastRoute {
//                print("🚀 Removing RecordingView from the nav stack")
//                path.removeLast()
//            }
//        }
        print("🚀 Appening route: \(route)")
        path.append(route)
    }
    
    func popToRoot() {
        path.removeLast(path.count)
    }
}
