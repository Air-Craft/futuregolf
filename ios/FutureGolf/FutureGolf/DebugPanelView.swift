import SwiftUI

struct DebugPanelView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var showTTSCacheStatus = false
    @State private var cacheWarmedSuccessfully = false
    @State private var serverTestResult = ""
    @State private var isTesting = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // TTS Cache Section
                    sectionHeader("TTS Cache")
                    
                    VStack(spacing: 12) {
                        Button(action: warmTTSCache) {
                            HStack {
                                Image(systemName: "flame.fill")
                                Text("Warm TTS Cache")
                                Spacer()
                                if cacheWarmedSuccessfully {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundColor(.green)
                                }
                            }
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.orange.opacity(0.8))
                            .cornerRadius(12)
                        }
                        
                        Button(action: listCacheContents) {
                            HStack {
                                Image(systemName: "list.bullet")
                                Text("List Cache Contents")
                                Spacer()
                            }
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.blue.opacity(0.8))
                            .cornerRadius(12)
                        }
                        
                        Button(action: clearCache) {
                            HStack {
                                Image(systemName: "trash.fill")
                                Text("Clear TTS Cache")
                                Spacer()
                            }
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.red.opacity(0.8))
                            .cornerRadius(12)
                        }
                    }
                    
                    // Server Connection Section
                    sectionHeader("Server Connection")
                    
                    VStack(spacing: 12) {
                        HStack {
                            Text("API URL:")
                            Text(Config.apiBaseURL)
                                .font(.system(.body, design: .monospaced))
                                .foregroundColor(.secondary)
                        }
                        
                        Button(action: testServerConnection) {
                            HStack {
                                if isTesting {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                        .scaleEffect(0.8)
                                } else {
                                    Image(systemName: "network")
                                }
                                Text(isTesting ? "Testing..." : "Test Server Connection")
                                Spacer()
                            }
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.purple.opacity(0.8))
                            .cornerRadius(12)
                        }
                        .disabled(isTesting)
                        
                        if !serverTestResult.isEmpty {
                            Text(serverTestResult)
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .padding()
                                .background(Color.gray.opacity(0.1))
                                .cornerRadius(8)
                        }
                    }
                    
                    // Recording Section
                    sectionHeader("Recording Debug")
                    
                    VStack(spacing: 12) {
                        Button(action: testSwingDetection) {
                            HStack {
                                Image(systemName: "figure.golf")
                                Text("Test Swing Detection")
                                Spacer()
                            }
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.green.opacity(0.8))
                            .cornerRadius(12)
                        }
                        
                        Button(action: testOnDeviceSTT) {
                            HStack {
                                Image(systemName: "mic.fill")
                                Text("Test On-Device STT")
                                Spacer()
                            }
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.indigo.opacity(0.8))
                            .cornerRadius(12)
                        }
                    }
                    
                    // API Section
                    sectionHeader("API Debug")
                    
                    VStack(spacing: 12) {
                        Button(action: testHealthEndpoint) {
                            HStack {
                                Image(systemName: "heart.fill")
                                Text("Test Health Endpoint")
                                Spacer()
                            }
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.pink.opacity(0.8))
                            .cornerRadius(12)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Debug Panel")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    // MARK: - Helper Views
    
    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.headline)
            .foregroundColor(.primary)
            .padding(.bottom, 4)
    }
    
    // MARK: - Actions
    
    private func warmTTSCache() {
        print("🐛 DEBUG: Warming TTS cache...")
        TTSService.shared.cacheManager.warmCache()
        cacheWarmedSuccessfully = true
        
        // Reset after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            cacheWarmedSuccessfully = false
        }
    }
    
    private func listCacheContents() {
        print("🐛 DEBUG: Listing cache contents...")
        TTSService.shared.cacheManager.debugListCachedFiles()
    }
    
    private func clearCache() {
        print("🐛 DEBUG: Clearing TTS cache...")
        TTSService.shared.cacheManager.clearCache()
    }
    
    private func testServerConnection() {
        isTesting = true
        serverTestResult = ""
        
        Task {
            do {
                // Test health endpoint
                let healthURL = URL(string: "\(Config.apiBaseURL)/health")!
                var healthRequest = URLRequest(url: healthURL)
                healthRequest.timeoutInterval = Config.healthCheckTimeout
                
                let (healthData, healthResponse) = try await URLSession.shared.data(for: healthRequest)
                
                if let httpResponse = healthResponse as? HTTPURLResponse {
                    if httpResponse.statusCode == 200 {
                        serverTestResult = "✅ Server is reachable (Status: \(httpResponse.statusCode))"
                    } else {
                        serverTestResult = "⚠️ Server responded with status: \(httpResponse.statusCode)"
                    }
                }
                
                // Test TTS endpoint
                let testPhrase = "Test connection"
                let urlString = "\(Config.apiBaseURL)/tts/coaching"
                
                guard let url = URL(string: urlString) else {
                    serverTestResult += "\n❌ Invalid TTS URL"
                    isTesting = false
                    return
                }
                
                let requestBody = ["text": testPhrase, "voice": "onyx", "model": "tts-1-hd", "speed": 0.9]
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
                request.timeoutInterval = Config.ttsSynthesisTimeout
                
                let (data, response) = try await URLSession.shared.data(for: request)
                
                if let httpResponse = response as? HTTPURLResponse {
                    if httpResponse.statusCode == 200 {
                        serverTestResult += "\n✅ TTS endpoint working (Data: \(data.count) bytes)"
                    } else {
                        serverTestResult += "\n⚠️ TTS endpoint status: \(httpResponse.statusCode)"
                    }
                }
                
            } catch let error as URLError {
                serverTestResult = "❌ Network Error: \(error.localizedDescription)\nCode: \(error.code.rawValue)"
            } catch {
                serverTestResult = "❌ Error: \(error.localizedDescription)"
            }
            
            isTesting = false
        }
    }
    
    private func testSwingDetection() {
        print("🐛 DEBUG: Testing swing detection...")
        // Implementation would go here
    }
    
    private func testOnDeviceSTT() {
        print("🐛 DEBUG: Testing on-device STT...")
        Task {
            let hasPermissions = await OnDeviceSTTService.shared.requestPermissions()
            if hasPermissions {
                OnDeviceSTTService.shared.startListening()
                print("🐛 DEBUG: STT started - say 'begin' or 'stop'")
                
                // Stop after 5 seconds
                DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                    OnDeviceSTTService.shared.stopListening()
                    print("🐛 DEBUG: STT stopped")
                }
            } else {
                print("🐛 DEBUG: STT permissions denied")
            }
        }
    }
    
    private func testHealthEndpoint() {
        print("🐛 DEBUG: Testing health endpoint...")
        Task {
            do {
                let url = URL(string: "\(Config.apiBaseURL)/health")!
                let (data, response) = try await URLSession.shared.data(from: url)
                
                if let httpResponse = response as? HTTPURLResponse {
                    print("🐛 DEBUG: Health check status: \(httpResponse.statusCode)")
                    if let responseString = String(data: data, encoding: .utf8) {
                        print("🐛 DEBUG: Health response: \(responseString)")
                    }
                }
            } catch {
                print("🐛 DEBUG: Health check failed: \(error)")
            }
        }
    }
}

#Preview {
    DebugPanelView()
}