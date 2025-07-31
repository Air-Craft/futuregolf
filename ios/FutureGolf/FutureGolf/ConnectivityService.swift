import Foundation
import Network
import Combine

// MARK: - Connectivity Service

@MainActor
class ConnectivityService: ObservableObject {
    static let shared = ConnectivityService()
    
    @Published var isConnected: Bool = true
    @Published var connectionType: NWInterface.InterfaceType?
    
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "com.futuregolf.connectivity")
    private var cancellables = Set<AnyCancellable>()
    
    // Callbacks for when connectivity is restored
    private var onConnectivityCallbacks: [UUID: () -> Void] = [:]
    
    private init() {
        startMonitoring()
        setupDebugToasts()
    }
    
    deinit {
        monitor.cancel()
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
    
    /// Check if a specific host is reachable
    func isHostReachable(_ urlString: String) async -> Bool {
        guard isConnected else { return false }
        
        guard let url = URL(string: urlString) else { return false }
        
        var request = URLRequest(url: url)
        request.httpMethod = "HEAD"
        request.timeoutInterval = 5.0
        
        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let httpResponse = response as? HTTPURLResponse {
                return (200...299).contains(httpResponse.statusCode)
            }
            return false
        } catch {
            return false
        }
    }
    
    // MARK: - Private Methods
    
    private func startMonitoring() {
        monitor.pathUpdateHandler = { [weak self] path in
            Task { @MainActor in
                self?.updateConnectionStatus(path)
            }
        }
        
        monitor.start(queue: queue)
    }
    
    @MainActor
    private func updateConnectionStatus(_ path: NWPath) {
        let wasConnected = isConnected
        
        isConnected = path.status == .satisfied
        
        // Update connection type
        if isConnected {
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
        
        // Call callbacks if connectivity was restored
        if !wasConnected && isConnected {
            print("🌐 Connectivity restored")
            for callback in onConnectivityCallbacks.values {
                callback()
            }
        }
        
        // Debug logging
        if Config.isDebugEnabled {
            if isConnected {
                print("🌐 Network connected via \(connectionTypeString)")
            } else {
                print("🌐 Network disconnected")
            }
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
        #if DEBUG
        // Show connectivity status changes as toasts
        $isConnected
            .removeDuplicates()
            .dropFirst() // Don't show initial state
            .sink { isConnected in
                if isConnected {
                    if self.connectionType != nil {
                        let typeString = self.connectionTypeString
                        ToastManager.shared.show("Connected via \(typeString)", type: .success)
                    } else {
                        ToastManager.shared.show("Connected", type: .success)
                    }
                } else {
                    ToastManager.shared.show("No network connection", type: .error)
                }
            }
            .store(in: &cancellables)
        #endif
    }
}

// MARK: - Connectivity-Aware Protocol

protocol ConnectivityAware {
    func onConnectivityRestored()
    func onConnectivityLost()
}

// Extension to make it easier to use
extension ConnectivityAware where Self: AnyObject {
    @MainActor
    func setupConnectivityMonitoring() {
        _ = ConnectivityService.shared.onConnectivityRestored { [weak self] in
            self?.onConnectivityRestored()
        }
        
        // Store the callback ID if needed for cleanup
        // You might want to store this in a property for later removal
    }
}