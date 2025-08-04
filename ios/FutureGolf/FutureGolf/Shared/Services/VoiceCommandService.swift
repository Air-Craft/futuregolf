import Foundation
import Combine
import Factory

@MainActor
class VoiceCommandService {
    @Injected(\.onDeviceSTTService) private var onDeviceSTT
    private var voiceCommandCancellable: AnyCancellable?
    var onCommand: ((VoiceCommand) -> Void)?

    func startListening() async throws {
        let hasPermissions = await onDeviceSTT.requestPermissions()
        if !hasPermissions {
            throw RecordingError.audioPermissionDenied
        }
        onDeviceSTT.startListening()
        
        voiceCommandCancellable = onDeviceSTT.$lastCommand
            .compactMap { $0 }
            .sink { [weak self] command in
                self?.onCommand?(command)
            }
    }

    func stopListening() {
        onDeviceSTT.stopListening()
        voiceCommandCancellable?.cancel()
    }
}
