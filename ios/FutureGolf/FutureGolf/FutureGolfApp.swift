//
//  FutureGolfApp.swift
//  FutureGolf
//
//  Created by Greg Plumbly on 25/07/2025.
//

import SwiftUI
import os.log
import AVFoundation

@main
struct FutureGolfApp: App {
    
    // Debug flag for direct recording screen launch
    private let debugLaunchRecording = ProcessInfo.processInfo.environment["DEBUG_LAUNCH_RECORDING"] == "1"
    
    init() {
        // Initialize connectivity monitoring
        _ = ConnectivityService.shared
        
        // Initialize video processing service
        _ = VideoProcessingService.shared
        
        // Initialize audio route manager
        _ = AudioRouteManager.shared
        
        // Test server connectivity at launch
        testServerConnection()
        
        // Start TTS cache warming in background
        warmTTSCache()
        
        // Process any pending video analyses
        processPendingAnalyses()
    }
    
    var body: some Scene {
        WindowGroup {
            if debugLaunchRecording {
                // Launch directly into recording screen for testing
                NavigationView {
                    DebugRecordingLauncher()
                }
                .withToastOverlay()
            } else {
                // Normal app flow
                HomeView()
                    .withToastOverlay()
            }
        }
    }
    
    private func testServerConnection() {
        print("🚀 APP LAUNCH: Testing server connectivity...")
        print("🚀 Server URL: \(Config.serverBaseURL)")
        
        Task {
            do {
                // Test basic connectivity
                let url = URL(string: "\(Config.serverBaseURL)/health")!
                var healthRequest = URLRequest(url: url)
                healthRequest.timeoutInterval = Config.healthCheckTimeout
                let (data, response) = try await URLSession.shared.data(for: healthRequest)
                
                if let httpResponse = response as? HTTPURLResponse {
                    print("🚀 Server health check - Status: \(httpResponse.statusCode)")
                    if let responseString = String(data: data, encoding: .utf8) {
                        print("🚀 Server response: \(responseString)")
                    }
                }
                
                // Test TTS endpoint specifically
                let ttsURL = URL(string: "\(Config.serverBaseURL)/api/v1/tts/coaching")!
                var ttsRequest = URLRequest(url: ttsURL)
                ttsRequest.httpMethod = "POST"
                ttsRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
                ttsRequest.timeoutInterval = Config.ttsSynthesisTimeout
                
                let testBody = [
                    "text": "Test",
                    "voice": "onyx",
                    "model": "tts-1-hd",
                    "speed": 0.9
                ]
                ttsRequest.httpBody = try JSONSerialization.data(withJSONObject: testBody)
                
                print("🚀 Testing TTS endpoint...")
                let startTime = Date()
                let (ttsData, ttsResponse) = try await URLSession.shared.data(for: ttsRequest)
                let elapsed = Date().timeIntervalSince(startTime)
                
                if let httpResponse = ttsResponse as? HTTPURLResponse {
                    print("🚀 TTS test - Status: \(httpResponse.statusCode), Time: \(String(format: "%.2f", elapsed))s, Data size: \(ttsData.count) bytes")
                }
                
            } catch {
                print("🚀 ❌ Server test failed: \(error)")
                print("🚀 Error type: \(type(of: error))")
                if let urlError = error as? URLError {
                    print("🚀 URLError code: \(urlError.code)")
                    print("🚀 URLError description: \(urlError.localizedDescription)")
                }
            }
        }
    }
    
    private func warmTTSCache() {
        print("🚀 APP LAUNCH: Starting TTS cache warming...")
        
        Task { @MainActor in
            // Check connectivity status
            let isConnected = ConnectivityService.shared.isConnected
            print("🚀 APP LAUNCH: Network connected: \(isConnected)")
            
            // Show connectivity status on launch if not connected
            if !isConnected {
                ToastManager.shared.show("Waiting for connectivity...", 
                                       type: .warning, 
                                       duration: .infinity, 
                                       id: "connectivity")
            }
            
            let cacheManager = TTSService.shared.cacheManager
            
            // Check current cache status
            let status = cacheManager.getCacheStatus()
            print("🚀 TTS Cache Status:")
            print("🚀   - Exists: \(status.exists)")
            print("🚀   - Phrase count: \(status.phraseCount)")
            if let lastRefresh = status.lastRefresh {
                let age = Date().timeIntervalSince(lastRefresh)
                print("🚀   - Last refresh: \(String(format: "%.1f", age/3600)) hours ago")
            }
            print("🚀   - Force refresh: \(Config.ttsForceCacheRefreshOnLaunch)")
            print("🚀   - Should refresh: \(cacheManager.shouldRefreshCache())")
            
            // Only warm cache if connected
            if isConnected {
                cacheManager.warmCache()
            } else {
                print("🚀 APP LAUNCH: No connectivity, skipping cache warming")
            }
        }
    }
    
    private func processPendingAnalyses() {
        print("🚀 APP LAUNCH: Checking for pending video analyses...")
        
        Task { @MainActor in
            let processingService = VideoProcessingService.shared
            let storageManager = AnalysisStorageManager.shared
            
            // Get pending analyses
            let pendingAnalyses = storageManager.getPendingAnalyses()
            print("🚀 Found \(pendingAnalyses.count) pending analyses")
            
            if !pendingAnalyses.isEmpty {
                // Check connectivity
                let isConnected = ConnectivityService.shared.isConnected
                
                if isConnected {
                    print("🚀 Network available, starting processing...")
                    processingService.processPendingAnalyses()
                } else {
                    print("🚀 No network connection, will process when connection restored")
                }
            }
        }
    }
}

// Debug wrapper for recording screen with enhanced error reporting
struct DebugRecordingLauncher: View {
    @State private var errorMessage: String?
    @State private var isRecordingScreenActive = false
    @State private var setupLogs: [String] = []
    
    private let logger = Logger(subsystem: "com.plumbly.FutureGolf", category: "DebugRecording")
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Debug Recording Screen Launcher")
                .font(.title2)
                .fontWeight(.bold)
            
            if !setupLogs.isEmpty {
                ScrollView {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Setup Logs:")
                            .font(.headline)
                        
                        ForEach(Array(setupLogs.enumerated()), id: \.offset) { index, log in
                            Text("\(index + 1). \(log)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .frame(maxHeight: 200)
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
            }
            
            if let error = errorMessage {
                Text("Error: \(error)")
                    .foregroundColor(.red)
                    .padding()
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(8)
            }
            
            Button("Test Recording Screen Setup") {
                testRecordingScreenSetup()
            }
            .buttonStyle(.borderedProminent)
            
            Button("Launch Recording Screen") {
                isRecordingScreenActive = true
            }
            .buttonStyle(.bordered)
            .disabled(errorMessage != nil)
            
            Spacer()
        }
        .padding()
        .navigationTitle("Debug Mode")
        .navigationBarTitleDisplayMode(.inline)
        .fullScreenCover(isPresented: $isRecordingScreenActive, onDismiss: {
            addLog("Recording screen dismissed")
        }) {
            RecordingScreen()
                .onAppear {
                    addLog("Recording screen appeared")
                }
        }
        .onAppear {
            addLog("Debug launcher appeared")
            logger.info("Debug recording launcher started")
        }
    }
    
    private func testRecordingScreenSetup() {
        addLog("Starting recording screen setup test...")
        errorMessage = nil
        
        Task {
            do {
                addLog("Testing camera permissions...")
                let cameraStatus = await checkCameraPermission()
                addLog("Camera permission status: \(cameraStatus)")
                
                addLog("Testing microphone permissions...")
                let micStatus = await checkMicrophonePermission()
                addLog("Microphone permission status: \(micStatus)")
                
                addLog("Testing API connectivity...")
                let apiStatus = await testAPIConnectivity()
                addLog("API connectivity: \(apiStatus)")
                
                addLog("All setup tests completed successfully!")
                
            } catch {
                let errorMsg = "Setup test failed: \(error.localizedDescription)"
                addLog(errorMsg)
                await MainActor.run {
                    errorMessage = errorMsg
                }
            }
        }
    }
    
    private func addLog(_ message: String) {
        let timestamp = DateFormatter().apply {
            $0.dateFormat = "HH:mm:ss.SSS"
        }.string(from: Date())
        
        let logMessage = "[\(timestamp)] \(message)"
        
        DispatchQueue.main.async {
            setupLogs.append(logMessage)
            // Keep only last 20 logs
            if setupLogs.count > 20 {
                setupLogs.removeFirst()
            }
        }
        
        logger.info("\(logMessage)")
        print("🐛 \(logMessage)")
    }
    
    private func checkCameraPermission() async -> String {
        let status = AVCaptureDevice.authorizationStatus(for: .video)
        
        switch status {
        case .authorized:
            return "✅ Authorized"
        case .denied:
            return "❌ Denied"
        case .restricted:
            return "⚠️ Restricted"
        case .notDetermined:
            addLog("Requesting camera permission...")
            let granted = await AVCaptureDevice.requestAccess(for: .video)
            return granted ? "✅ Granted" : "❌ User denied"
        @unknown default:
            return "❓ Unknown status"
        }
    }
    
    private func checkMicrophonePermission() async -> String {
        if #available(iOS 17.0, *) {
            let status = AVAudioApplication.shared.recordPermission
            
            switch status {
            case .granted:
                return "✅ Granted"
            case .denied:
                return "❌ Denied"
            case .undetermined:
                addLog("Requesting microphone permission...")
                let granted = await AVAudioApplication.requestRecordPermission()
                return granted ? "✅ Granted" : "❌ User denied"
            @unknown default:
                return "❓ Unknown status"
            }
        } else {
            let status = AVAudioSession.sharedInstance().recordPermission
            
            switch status {
            case .granted:
                return "✅ Granted"
            case .denied:
                return "❌ Denied"
            case .undetermined:
                addLog("Requesting microphone permission...")
                let granted = await withCheckedContinuation { continuation in
                    AVAudioSession.sharedInstance().requestRecordPermission { granted in
                        continuation.resume(returning: granted)
                    }
                }
                return granted ? "✅ Granted" : "❌ User denied"
            @unknown default:
                return "❓ Unknown status"
            }
        }
    }
    
    private func testAPIConnectivity() async -> String {
        do {
            let apiService = RecordingAPIService.shared
            let isHealthy = await apiService.checkServiceHealth()
            
            if isHealthy {
                addLog("API service is healthy")
                return "✅ APIs working"
            } else {
                return "❌ Health check failed"
            }
        } catch {
            addLog("API test error: \(error)")
            return "❌ \(error.localizedDescription)"
        }
    }
}

// Helper extension for cleaner syntax
extension DateFormatter {
    func apply(_ closure: (DateFormatter) -> Void) -> DateFormatter {
        closure(self)
        return self
    }
}
