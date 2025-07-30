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
    
    var body: some Scene {
        WindowGroup {
            if debugLaunchRecording {
                // Launch directly into recording screen for testing
                NavigationView {
                    DebugRecordingLauncher()
                }
            } else {
                // Normal app flow
                HomeView()
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
