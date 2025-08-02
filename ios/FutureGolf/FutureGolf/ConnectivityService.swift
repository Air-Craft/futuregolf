import Foundation
import Network
import Combine
import UIKit

// MARK: - Connectivity Service

@MainActor
class ConnectivityService: ObservableObject {
    // Temporary singleton for TTSService compatibility
    static let shared = ConnectivityService()
    
    // Published properties for UI binding
    @Published var isConnected: Bool = false // Combined network + server connectivity
    @Published var connectionType: NWInterface.InterfaceType?
    
    // Server connectivity tracking
    private(set) var lastConnectivityCheck: Date = .distantPast
    private var isNetworkAvailable: Bool = false
    private var isServerReachable: Bool = false
    
    // Monitoring infrastructure
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "com.futuregolf.connectivity")
    private var serverCheckTimer: Timer?
    private var cancellables = Set<AnyCancellable>()
    
    // App lifecycle
    private var isAppActive = true
    
    // Callbacks for when connectivity is restored
    private var onConnectivityCallbacks: [UUID: () -> Void] = [:]
    
    // Server endpoint
    private let serverHealthEndpoint = "\(Config.apiBaseURL)/health"
    
    init() {
        // Initialization will be handled by startMonitoring
    }
    
    deinit {
        monitor.cancel()
        serverCheckTimer?.invalidate()
    }
    
    // MARK: - Public Methods
    
    /// Register a callback to be called when connectivity is restored
    func onConnectivityRestored(_ callback: @escaping () -> Void) -> UUID {
        let id = UUID()
        onConnectivityCallbacks[id] = callback
        
        // If already connected, call immediately
        if isConnected {
            callback()
        }
        
        return id
    }
    
    /// Remove a connectivity callback
    func removeCallback(_ id: UUID) {
        onConnectivityCallbacks.removeValue(forKey: id)
    }
    
    /// Get best guess of connectivity based on last check
    var isLikelyConnected: Bool {
        // If checked within last 5 seconds, use cached result
        if Date().timeIntervalSince(lastConnectivityCheck) < 5.0 {
            return isConnected
        }
        // Otherwise just check network availability
        return isNetworkAvailable
    }
    
    // MARK: - Private Methods
    
    private func setupLifecycleObservers() {
        NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)
            .sink { [weak self] _ in
                Task { @MainActor in
                    self?.applicationDidBecomeActive()
                }
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: UIApplication.willResignActiveNotification)
            .sink { [weak self] _ in
                Task { @MainActor in
                    self?.applicationWillResignActive()
                }
            }
            .store(in: &cancellables)
    }
    
    private func applicationDidBecomeActive() {
        print("🌐 App became active, resuming connectivity monitoring")
        isAppActive = true
        // Check immediately
        Task {
            await checkServerHealth()
        }
        // Resume polling
        startServerHealthPolling()
    }
    
    private func applicationWillResignActive() {
        print("🌐 App resigning active, suspending connectivity monitoring")
        isAppActive = false
        // Stop polling to save battery
        serverCheckTimer?.invalidate()
        serverCheckTimer = nil
    }
    
    func startMonitoring() {
        setupLifecycleObservers()
        setupDebugToasts()
        
        // Start monitoring network path
        monitor.pathUpdateHandler = { [weak self] path in
            Task { @MainActor in
                self?.updateNetworkStatus(path)
            }
        }
        
        monitor.start(queue: queue)
        
        // Start server health checking immediately
        Task {
            await checkServerHealth()
            startServerHealthPolling()
        }
    }
    
    private func updateNetworkStatus(_ path: NWPath) {
        let wasNetworkAvailable = isNetworkAvailable
        
        isNetworkAvailable = path.status == .satisfied
        
        // Update connection type
        if isNetworkAvailable {
            if path.usesInterfaceType(.wifi) {
                connectionType = .wifi
            } else if path.usesInterfaceType(.cellular) {
                connectionType = .cellular
            } else if path.usesInterfaceType(.wiredEthernet) {
                connectionType = .wiredEthernet
            } else {
                connectionType = .other
            }
        } else {
            connectionType = nil
        }
        
        // If network status changed, check server immediately
        if wasNetworkAvailable != isNetworkAvailable {
            Task {
                await checkServerHealth()
            }
        }
        
        // Debug logging
        if Config.isDebugEnabled {
            if isNetworkAvailable {
                print("🌐 Network available via \(connectionTypeString)")
            } else {
                print("🌐 Network unavailable")
            }
        }
    }
    
    private func startServerHealthPolling() {
        // Cancel existing timer
        serverCheckTimer?.invalidate()
        
        // Only poll when app is active
        guard isAppActive else { return }
        
        // Poll every 1 second
        serverCheckTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self = self, self.isAppActive else { return }
                await self.checkServerHealth()
            }
        }
    }
    
    private func checkServerHealth() async {
        // Skip if no network
        guard isNetworkAvailable else {
            updateConnectivityStatus(serverReachable: false)
            return
        }
        
        lastConnectivityCheck = Date()
        
        guard let url = URL(string: serverHealthEndpoint) else {
            updateConnectivityStatus(serverReachable: false)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 2.0 // Short timeout for health check
        
        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let httpResponse = response as? HTTPURLResponse {
                let serverReachable = (200...299).contains(httpResponse.statusCode)
                updateConnectivityStatus(serverReachable: serverReachable)
            } else {
                updateConnectivityStatus(serverReachable: false)
            }
        } catch {
            updateConnectivityStatus(serverReachable: false)
        }
    }
    
    private func updateConnectivityStatus(serverReachable: Bool) {
        let wasServerReachable = isServerReachable
        let wasConnected = isConnected
        
        isServerReachable = serverReachable
        
        // Combined connectivity = network AND server
        let newConnected = isNetworkAvailable && isServerReachable
        
        // Only update if status actually changed
        if isConnected != newConnected {
            isConnected = newConnected
            
            if wasConnected && !isConnected {
                // Lost connectivity
                print("🌐 Connectivity lost")
                showConnectivityToast(connected: false)
            } else if !wasConnected && isConnected {
                // Gained connectivity
                print("🌐 Connectivity restored")
                showConnectivityToast(connected: true)
                onConnectivityRestored()
            }
        }
        
        // Debug logging
        if Config.isDebugEnabled && wasServerReachable != isServerReachable {
            print("🌐 Server reachable: \(isServerReachable)")
        }
    }
    
    private func showConnectivityToast(connected: Bool) {
        if connected {
            // Clear any existing connectivity warning
            ToastManager.shared.dismiss(id: "connectivity")
            // Show success briefly
            ToastManager.shared.show("Connected", type: .success, duration: 2.0)
        } else {
            // Show persistent warning
            ToastManager.shared.show("Waiting for connectivity...", 
                                   type: .warning, 
                                   duration: .infinity, 
                                   id: "connectivity")
        }
    }
    
    private func onConnectivityRestored() {
        // Call all registered callbacks
        for callback in onConnectivityCallbacks.values {
            callback()
        }
        
        // Resume pending operations
        Task {
            // 1. Warm TTS cache
            TTSService.shared.cacheManager.warmCache()
            
            // 2. Resume any pending swing analyses
            // This will be handled by SwingAnalysisViewModel subscribers
        }
    }
    
    private var connectionTypeString: String {
        switch connectionType {
        case .wifi:
            return "WiFi"
        case .cellular:
            return "Cellular"
        case .wiredEthernet:
            return "Ethernet"
        case .loopback:
            return "Loopback"
        default:
            return "Unknown"
        }
    }
    
    private func setupDebugToasts() {
        // Don't show debug toasts in release mode
        guard Config.isDebugEnabled else { return }
        
        // We handle toasts in showConnectivityToast() for unified messaging
        // This method is kept for potential future debug-specific toasts
    }
}

// MARK: - Connectivity-Aware Protocol

protocol ConnectivityAware {
    func onConnectivityRestored()
    func onConnectivityLost()
}

// Extension removed - no longer using singleton pattern