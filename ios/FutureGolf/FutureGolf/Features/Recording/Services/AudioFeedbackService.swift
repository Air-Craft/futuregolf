import Foundation
import AudioToolbox

class AudioFeedbackService {
    func playSwingTone() {
        AudioServicesPlaySystemSound(1057) // "Tink"
    }
    
    func playCompletionTone() {
        AudioServicesPlaySystemSound(1025) // "Complete"
    }
}
