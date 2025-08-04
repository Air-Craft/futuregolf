import Foundation
import Combine

@MainActor
class AppState: ObservableObject {
    @Published var currentRecordingId: String?
    @Published var currentRecordingURL: URL?

    func clearCurrentRecording() {
        currentRecordingId = nil
        currentRecordingURL = nil
    }

    func setCurrentRecording(url: URL, id: String) {
        currentRecordingURL = url
        currentRecordingId = id
    }
}
