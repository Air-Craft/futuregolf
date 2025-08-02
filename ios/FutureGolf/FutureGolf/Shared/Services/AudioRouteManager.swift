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
    private var lastConfiguredForHeadphones: Bool?
    private var lastConfigurationTime: Date = .distantPast
    
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
            // Only reconfigure if category changed (speaker vs headphones)
            if shouldReconfigureAudio() {
                configureForPlayback()
            }
            
        case .oldDeviceUnavailable:
            print("🎧 Audio device disconnected")
            updateCurrentRoute()
            // Only reconfigure if category changed
            if shouldReconfigureAudio() {
                configureForPlayback()
            }
            
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
            
            // Check if headphones are connected first
            let currentRoute = session.currentRoute
            let hasHeadphones = currentRoute.outputs.contains { output in
                return output.portType == .headphones ||
                       output.portType == .bluetoothA2DP ||
                       output.portType == .bluetoothHFP ||
                       output.portType == .bluetoothLE ||
                       output.portType == .airPlay
            }
            
            // Build options based on output device
            var options: AVAudioSession.CategoryOptions = [
                .allowBluetooth,
                .allowBluetoothA2DP,
                .allowAirPlay,
                .defaultToSpeaker  // Use speaker when no headphones connected
            ]
            
            // Only add .duckOthers when using speakers to avoid chorusing with headphones
            if !hasHeadphones {
                options.insert(.duckOthers)
                print("🎧 Adding .duckOthers option for speaker playback")
            } else {
                print("🎧 Skipping .duckOthers option for headphone playback to prevent chorusing")
            }
            
            // Use .playAndRecord to support both TTS and voice recording
            try session.setCategory(
                .playAndRecord,
                mode: .default,
                options: options
            )
            
            // If no headphones, ensure we're using the speaker, not earpiece
            if !hasHeadphones {
                try session.overrideOutputAudioPort(.speaker)
            }
            
            try session.setActive(true, options: [])
            
            print("🎧 Audio session configured for playback")
            print("🎧 Using speaker override: \(!hasHeadphones)")
            print("🎧 Headphones connected: \(hasHeadphones)")
            
            // Track last configuration
            lastConfiguredForHeadphones = hasHeadphones
            lastConfigurationTime = Date()
        } catch {
            print("🎧 Failed to configure audio session: \(error)")
        }
    }
    
    /// Configure audio session for recording
    func configureForRecording() {
        do {
            let session = AVAudioSession.sharedInstance()
            
            // Check current route to see if we need speaker override
            let currentRoute = session.currentRoute
            let hasHeadphones = currentRoute.outputs.contains { output in
                return output.portType == .headphones ||
                       output.portType == .bluetoothA2DP ||
                       output.portType == .bluetoothHFP ||
                       output.portType == .bluetoothLE ||
                       output.portType == .airPlay
            }
            
            // Build options based on output device
            var options: AVAudioSession.CategoryOptions = [
                .allowBluetooth,
                .defaultToSpeaker  // Ensure speaker is used when no headphones
            ]
            
            // Only add .duckOthers when using speakers to avoid chorusing with headphones
            if !hasHeadphones {
                options.insert(.duckOthers)
                print("🎧 Adding .duckOthers option for speaker recording")
            } else {
                print("🎧 Skipping .duckOthers option for headphone recording to prevent chorusing")
            }
            
            // Use measurement mode for better voice recognition
            try session.setCategory(
                .playAndRecord,
                mode: .measurement,
                options: options
            )
            
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
            print("🎧 Headphones connected: \(hasHeadphones)")
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
    
    /// Check if we should reconfigure audio based on route change
    private func shouldReconfigureAudio() -> Bool {
        // Don't reconfigure too frequently (debounce)
        guard Date().timeIntervalSince(lastConfigurationTime) > 0.5 else {
            print("🎧 Skipping reconfiguration (too soon)")
            return false
        }
        
        // Check if headphone state actually changed
        if let lastHeadphones = lastConfiguredForHeadphones {
            let changed = lastHeadphones != isHeadphonesConnected
            if changed {
                print("🎧 Headphone state changed: \(lastHeadphones) → \(isHeadphonesConnected)")
            }
            return changed
        }
        
        // First configuration
        return true
    }
    
    /// Force refresh audio configuration
    func refreshAudioConfiguration() {
        print("🎧 Refreshing audio configuration...")
        
        // Log current route
        print(getCurrentRouteInfo())
        
        // Force reconfiguration
        lastConfiguredForHeadphones = nil
        configureForPlayback()
    }
}