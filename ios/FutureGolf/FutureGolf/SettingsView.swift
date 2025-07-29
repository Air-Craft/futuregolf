import SwiftUI
import AVFoundation

struct SettingsView: View {
    @AppStorage("apiEndpoint") private var apiEndpoint = "http://192.168.1.114:8000"
    @AppStorage("viewType") private var viewType = "face-on"
    @AppStorage("golferHandedness") private var golferHandedness = "right"
    @AppStorage("enableHaptics") private var enableHaptics = true
    @AppStorage("autoAnalyze") private var autoAnalyze = false
    @AppStorage("saveAnalysisHistory") private var saveAnalysisHistory = true
    @AppStorage("coachingSpeechRate") private var coachingSpeechRate: Double = 0.48
    @AppStorage("coachingAutoPlay") private var coachingAutoPlay = true
    @AppStorage("coachingVoiceGender") private var coachingVoiceGender = "female"
    
    @State private var showingSignIn = false
    @State private var isSignedIn = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // API Configuration Section
                    VStack(alignment: .leading, spacing: 16) {
                        Label("API Configuration", systemImage: "server.rack")
                            .font(.headline)
                            .foregroundColor(.primary)
                            
                        VStack(alignment: .leading, spacing: 8) {
                            Text("API Endpoint")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            
                            TextField("Enter API URL", text: $apiEndpoint)
                                .textFieldStyle(.roundedBorder)
                                .autocapitalization(.none)
                                .disableAutocorrection(true)
                                .textContentType(.URL)
                        }
                    }
                    .padding()
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                    
                    // Video Analysis Settings
                    VStack(alignment: .leading, spacing: 16) {
                        Label("Video Analysis", systemImage: "video.badge.waveform")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        VStack(spacing: 16) {
                            // View Type Selector
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Camera View")
                                    .font(.subheadline)
                                    .foregroundColor(.primary)
                                
                                Picker("Camera View", selection: $viewType) {
                                    Text("Face On").tag("face-on")
                                    Text("Down the Line").tag("down-the-line")
                                }
                                .pickerStyle(.segmented)
                            }
                            
                            // Handedness Selector
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Golfer Handedness")
                                    .font(.subheadline)
                                    .foregroundColor(.primary)
                                
                                Picker("Handedness", selection: $golferHandedness) {
                                    Text("Right Handed").tag("right")
                                    Text("Left Handed").tag("left")
                                }
                                .pickerStyle(.segmented)
                            }
                        }
                    }
                    .padding()
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                    
                    // App Settings
                    VStack(alignment: .leading, spacing: 16) {
                        Label("App Settings", systemImage: "gear")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        VStack(spacing: 12) {
                            Toggle("Enable Haptics", isOn: $enableHaptics)
                            Toggle("Auto Analyze", isOn: $autoAnalyze)
                            Toggle("Save Analysis History", isOn: $saveAnalysisHistory)
                        }
                    }
                    .padding()
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                }
                .padding()
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

#Preview {
    SettingsView()
}