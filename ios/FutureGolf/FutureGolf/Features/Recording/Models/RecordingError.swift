import Foundation

enum RecordingError: LocalizedError, Equatable {
    case cameraPermissionDenied
    case insufficientStorage
    case cameraHardwareError
    case audioPermissionDenied
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .cameraPermissionDenied:
            return "Camera access is required to record your swing. Please enable camera permissions in Settings."
        case .insufficientStorage:
            return "Not enough storage space available. Please free up space and try again."
        case .cameraHardwareError:
            return "Camera hardware error. Please restart the app and try again."
        case .audioPermissionDenied:
            return "Microphone access is required for voice commands. Please enable microphone permissions in Settings."
        case .networkError:
            return "Network connection required for voice processing. Please check your connection."
        }
    }
}
