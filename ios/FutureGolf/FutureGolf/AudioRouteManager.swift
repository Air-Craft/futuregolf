import Foundation
import AVFoundation
import Combine

// MARK: - Audio Route Manager

@MainActor
class AudioRouteManager: ObservableObject {
    static let shared = AudioRouteManager()
    
    @Published var currentRoute: String = "Unknown"
    @Published var isHeadphonesConnected: Bool = false
    
    private var routeChangeObserver: NSObjectProtocol?
    
    private init() {
        setupRouteChangeNotification()
        updateCurrentRoute()
    }
    
    deinit {
        if let observer = routeChangeObserver {
            NotificationCenter.default.removeObserver(observer)
        }
    }
    
    // MARK: - Setup
    
    private func setupRouteChangeNotification() {
        routeChangeObserver = NotificationCenter.default.addObserver(
            forName: AVAudioSession.routeChangeNotification,
            object: AVAudioSession.sharedInstance(),
            queue: .main
        ) { [weak self] notification in
            Task { @MainActor in
                self?.handleRouteChange(notification)
            }
        }
    }
    
    // MARK: - Route Change Handling
    
    private func handleRouteChange(_ notification: Notification) {
        guard let userInfo = notification.userInfo,
              let reasonValue = userInfo[AVAudioSessionRouteChangeReasonKey] as? UInt,
              let reason = AVAudioSession.RouteChangeReason(rawValue: reasonValue) else {
            return
        }
        
        switch reason {
        case .newDeviceAvailable:
            print("🎧 New audio device available")
            updateCurrentRoute()
            // Reconfigure to use the new device
            configureForPlayback()
            
        case .oldDeviceUnavailable:
            print("🎧 Audio device disconnected")
            updateCurrentRoute()
            // Reconfigure to ensure speaker is used
            configureForPlayback()
            
        case .categoryChange:
            print("🎧 Audio category changed")
            updateCurrentRoute()
            
        default:
            updateCurrentRoute()
        }
    }
    
    // MARK: - Route Information
    
    private func updateCurrentRoute() {
        let session = AVAudioSession.sharedInstance()
        let currentRoute = session.currentRoute
        
        // Check outputs
        var routeDescription = "Unknown"
        var hasHeadphones = false
        
        for output in currentRoute.outputs {
            switch output.portType {
            case .headphones:
                routeDescription = "Headphones"
                hasHeadphones = true
            case .bluetoothA2DP, .bluetoothHFP, .bluetoothLE:
                routeDescription = "Bluetooth"
                hasHeadphones = true
            case .airPlay:
                routeDescription = "AirPlay"
                hasHeadphones = true
            case .carAudio:
                routeDescription = "CarPlay"
                hasHeadphones = true
            case .builtInSpeaker:
                routeDescription = "Speaker"
            case .builtInReceiver:
                routeDescription = "Phone"
            default:
                routeDescription = output.portName
            }
            
            // Use the first output as the primary route
            break
        }
        
        self.currentRoute = routeDescription
        self.isHeadphonesConnected = hasHeadphones
        
        print("🎧 Audio route updated: \(routeDescription)")
        
        // Show debug toast in debug builds
        #if DEBUG
        ToastManager.shared.show("Audio: \(routeDescription)", type: .info, duration: 2.0)
        #endif
    }
    
    // MARK: - Public Methods
    
    /// Configure audio session for optimal routing
    func configureForPlayback() {
        do {
            let session = AVAudioSession.sharedInstance()
            
            // Use .playAndRecord to support both TTS and voice recording
            // Allow Bluetooth and respect current audio route
            try session.setCategory(
                .playAndRecord,
                mode: .default,
                options: [
                    .duckOthers,
                    .allowBluetooth,
                    .allowBluetoothA2DP,
                    .allowAirPlay,
                    .defaultToSpeaker  // Use speaker when no headphones connected
                ]
            )
            
            // Check if headphones are connected
            let currentRoute = session.currentRoute
            let hasHeadphones = currentRoute.outputs.contains { output in
                return output.portType == .headphones ||
                       output.portType == .bluetoothA2DP ||
                       output.portType == .bluetoothHFP ||
                       output.portType == .bluetoothLE
            }
            
            // If no headphones, ensure we're using the speaker, not earpiece
            if !hasHeadphones {
                try session.overrideOutputAudioPort(.speaker)
            }
            
            try session.setActive(true, options: [])
            
            print("🎧 Audio session configured for playback")
            print("🎧 Using speaker override: \(!hasHeadphones)")
        } catch {
            print("🎧 Failed to configure audio session: \(error)")
        }
    }
    
    /// Configure audio session for recording
    func configureForRecording() {
        do {
            let session = AVAudioSession.sharedInstance()
            
            // Use measurement mode for better voice recognition
            try session.setCategory(
                .playAndRecord,
                mode: .measurement,
                options: [
                    .duckOthers,
                    .allowBluetooth,
                    .defaultToSpeaker  // Ensure speaker is used when no headphones
                ]
            )
            
            // Check current route to see if we need speaker override
            let currentRoute = session.currentRoute
            let hasHeadphones = currentRoute.outputs.contains { output in
                return output.portType == .headphones ||
                       output.portType == .bluetoothA2DP ||
                       output.portType == .bluetoothHFP ||
                       output.portType == .bluetoothLE
            }
            
            // Only override to speaker if no headphones connected
            if !hasHeadphones {
                try session.overrideOutputAudioPort(.speaker)
            }
            
            try session.setActive(true, options: .notifyOthersOnDeactivation)
            
            // Log input device for debugging
            if let inputs = session.currentRoute.inputs.first {
                print("🎤 Recording using input: \(inputs.portName) (\(inputs.portType.rawValue))")
            }
            
            print("🎧 Audio session configured for recording")
        } catch {
            print("🎧 Failed to configure audio session: \(error)")
        }
    }
    
    /// Get current audio route info
    func getCurrentRouteInfo() -> String {
        let session = AVAudioSession.sharedInstance()
        let route = session.currentRoute
        
        var info = "Audio Route Info:\n"
        
        info += "Inputs:\n"
        for input in route.inputs {
            info += "  - \(input.portName) (\(input.portType.rawValue))\n"
        }
        
        info += "Outputs:\n"
        for output in route.outputs {
            info += "  - \(output.portName) (\(output.portType.rawValue))\n"
        }
        
        return info
    }
    
    /// Force refresh audio configuration
    func refreshAudioConfiguration() {
        print("🎧 Refreshing audio configuration...")
        
        // Log current route
        print(getCurrentRouteInfo())
        
        // Reconfigure based on current usage
        let session = AVAudioSession.sharedInstance()
        if session.isOtherAudioPlaying {
            configureForPlayback()
        } else {
            // Default to playback config
            configureForPlayback()
        }
    }
}