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
                    LiquidGlassCard(
                        content: {
                            VStack(alignment: .leading, spacing: 16) {
                                Label("API Configuration", systemImage: "server.rack")
                                    .font(.headline)
                                    .foregroundColor(.glassText)
                                
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("API Endpoint")
                                        .font(.caption)
                                        .foregroundColor(.glassSecondaryText)
                                    
                                    TextField("Enter API URL", text: $apiEndpoint)
                                        .textFieldStyle(.plain)
                                        .padding(12)
                                        .background(Material.ultraThin, in: RoundedRectangle(cornerRadius: 8))
                                        .autocapitalization(.none)
                                        .disableAutocorrection(true)
                                        .textContentType(.URL)
                                }
                            }
                            .padding()
                        },
                        cornerRadius: 16,
                        glassIntensity: .light
                    )
                    .padding(.horizontal)
                    
                    // Video Analysis Settings
                    LiquidGlassCard(
                        content: {
                            VStack(alignment: .leading, spacing: 16) {
                                Label("Video Analysis", systemImage: "video.badge.waveform")
                                    .font(.headline)
                                    .foregroundColor(.glassText)
                                
                                VStack(spacing: 16) {
                                    // View Type Selector
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Camera View")
                                            .font(.subheadline)
                                            .foregroundColor(.glassText)
                                        
                                        HStack(spacing: 0) {
                                            ForEach([("face-on", "Face On"), ("down-the-line", "Down the Line")], id: \.0) { value, title in
                                                Button(action: {
                                                    withAnimation(.liquidGlassSpring) {
                                                        viewType = value
                                                        LiquidGlassHaptics.selection()
                                                    }
                                                }) {
                                                    Text(title)
                                                        .font(.subheadline)
                                                        .fontWeight(viewType == value ? .medium : .regular)
                                                        .foregroundColor(viewType == value ? .white : .glassText)
                                                        .frame(maxWidth: .infinity)
                                                        .padding(.vertical, 10)
                                                        .background {
                                                            if viewType == value {
                                                                RoundedRectangle(cornerRadius: 8)
                                                                    .fill(Color.golfGreen)
                                                            }
                                                        }
                                                }
                                                .buttonStyle(.plain)
                                            }
                                        }
                                        .background(Material.ultraThin, in: RoundedRectangle(cornerRadius: 8))
                                    }
                                    
                                    // Handedness Selector
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Golfer Handedness")
                                            .font(.subheadline)
                                            .foregroundColor(.glassText)
                                        
                                        HStack(spacing: 0) {
                                            ForEach([("right", "Right Handed", "figure.golf"), ("left", "Left Handed", "figure.golf")], id: \.0) { value, title, icon in
                                                Button(action: {
                                                    withAnimation(.liquidGlassSpring) {
                                                        golferHandedness = value
                                                        LiquidGlassHaptics.selection()
                                                    }
                                                }) {
                                                    HStack(spacing: 8) {
                                                        Image(systemName: icon)
                                                            .font(.system(size: 16))
                                                            .scaleEffect(x: value == "left" ? -1 : 1)
                                                        Text(title)
                                                            .font(.subheadline)
                                                    }
                                                    .fontWeight(golferHandedness == value ? .medium : .regular)
                                                    .foregroundColor(golferHandedness == value ? .white : .glassText)
                                                    .frame(maxWidth: .infinity)
                                                    .padding(.vertical, 10)
                                                    .background {
                                                        if golferHandedness == value {
                                                            RoundedRectangle(cornerRadius: 8)
                                                                .fill(Color.golfGreen)
                                                        }
                                                    }
                                                }
                                                .buttonStyle(.plain)
                                            }
                                        }
                                        .background(Material.ultraThin, in: RoundedRectangle(cornerRadius: 8))
                                    }
                                    
                                    Divider()
                                        .overlay(Color.glassSecondaryText.opacity(0.2))
                                    
                                    // Toggle Settings
                                    SettingsToggleRow(
                                        title: "Auto-Analyze",
                                        subtitle: "Automatically start analysis after video selection",
                                        icon: "wand.and.stars",
                                        isOn: $autoAnalyze
                                    )
                                    
                                    SettingsToggleRow(
                                        title: "Save History",
                                        subtitle: "Keep analysis results for future reference",
                                        icon: "clock.arrow.circlepath",
                                        isOn: $saveAnalysisHistory
                                    )
                                }
                            }
                            .padding()
                        },
                        cornerRadius: 16,
                        glassIntensity: .light
                    )
                    .padding(.horizontal)
                    
                    // App Preferences
                    LiquidGlassCard(
                        content: {
                            VStack(alignment: .leading, spacing: 16) {
                                Label("App Preferences", systemImage: "slider.horizontal.3")
                                    .font(.headline)
                                    .foregroundColor(.glassText)
                                
                                SettingsToggleRow(
                                    title: "Haptic Feedback",
                                    subtitle: "Vibration feedback for interactions",
                                    icon: "iphone.radiowaves.left.and.right",
                                    isOn: $enableHaptics
                                )
                            }
                            .padding()
                        },
                        cornerRadius: 16,
                        glassIntensity: .light
                    )
                    .padding(.horizontal)
                    
                    // Coaching Settings
                    LiquidGlassCard(
                        content: {
                            VStack(alignment: .leading, spacing: 16) {
                                Label("Coaching Settings", systemImage: "speaker.wave.3")
                                    .font(.headline)
                                    .foregroundColor(.glassText)
                                
                                VStack(alignment: .leading, spacing: 16) {
                                    // Speech Rate Slider
                                    VStack(alignment: .leading, spacing: 8) {
                                        HStack {
                                            Image(systemName: "hare")
                                                .foregroundColor(.glassSecondaryText)
                                            Text("Speech Rate")
                                                .font(.subheadline)
                                                .foregroundColor(.glassText)
                                            Spacer()
                                            Text(String(format: "%.1fx", coachingSpeechRate))
                                                .font(.caption)
                                                .foregroundColor(.glassSecondaryText)
                                        }
                                        
                                        Slider(value: $coachingSpeechRate, in: 0.3...0.7, step: 0.05)
                                            .tint(.fairwayGreen)
                                    }
                                    
                                    Divider()
                                        .background(Color.glassSeparator)
                                    
                                    // Auto-play coaching toggle
                                    SettingsToggleRow(
                                        title: "Auto-play Coaching",
                                        subtitle: "Automatically speak feedback during playback",
                                        icon: "play.circle",
                                        isOn: $coachingAutoPlay
                                    )
                                    
                                    // Voice Gender Picker
                                    VStack(alignment: .leading, spacing: 8) {
                                        HStack {
                                            Image(systemName: "person.wave.2")
                                                .foregroundColor(.glassSecondaryText)
                                            Text("Voice Type")
                                                .font(.subheadline)
                                                .foregroundColor(.glassText)
                                        }
                                        
                                        Picker("Voice Type", selection: $coachingVoiceGender) {
                                            Text("Female").tag("female")
                                            Text("Male").tag("male")
                                        }
                                        .pickerStyle(.segmented)
                                    }
                                    
                                    // Test Coaching Button
                                    Button(action: testCoachingVoice) {
                                        HStack {
                                            Image(systemName: "play.fill")
                                            Text("Test Coaching Voice")
                                        }
                                        .frame(maxWidth: .infinity)
                                    }
                                    .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
                                }
                            }
                            .padding()
                        },
                        cornerRadius: 16,
                        glassIntensity: .light
                    )
                    .padding(.horizontal)
                    
                    // Account Section
                    LiquidGlassCard(
                        content: {
                            VStack(alignment: .leading, spacing: 16) {
                                Label("Account", systemImage: "person.circle")
                                    .font(.headline)
                                    .foregroundColor(.glassText)
                                
                                if isSignedIn {
                                    HStack {
                                        Image(systemName: "person.fill")
                                            .font(.title2)
                                            .foregroundColor(.fairwayGreen)
                                            .frame(width: 50, height: 50)
                                            .background(Circle().fill(Material.ultraThin))
                                        
                                        VStack(alignment: .leading, spacing: 4) {
                                            Text("John Doe")
                                                .font(.headline)
                                                .foregroundColor(.glassText)
                                            Text("john.doe@example.com")
                                                .font(.caption)
                                                .foregroundColor(.glassSecondaryText)
                                        }
                                        
                                        Spacer()
                                    }
                                    
                                    Button(action: {
                                        withAnimation(.liquidGlassSpring) {
                                            isSignedIn = false
                                            LiquidGlassHaptics.impact(.light)
                                        }
                                    }) {
                                        HStack {
                                            Image(systemName: "rectangle.portrait.and.arrow.forward")
                                            Text("Sign Out")
                                        }
                                        .foregroundColor(.red)
                                        .frame(maxWidth: .infinity)
                                    }
                                    .buttonStyle(LiquidGlassButtonStyle(isProminent: false))
                                } else {
                                    Button(action: {
                                        showingSignIn = true
                                        LiquidGlassHaptics.impact(.medium)
                                    }) {
                                        HStack {
                                            Image(systemName: "person.badge.plus")
                                            Text("Sign In")
                                                .fontWeight(.medium)
                                        }
                                        .foregroundColor(.white)
                                        .frame(maxWidth: .infinity)
                                    }
                                    .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
                                }
                                
                                Divider()
                                    .overlay(Color.glassSecondaryText.opacity(0.2))
                                
                                // App Info
                                VStack(spacing: 12) {
                                    InfoRow(label: "Version", value: "1.0.0")
                                    InfoRow(label: "Build", value: "2025.1")
                                }
                            }
                            .padding()
                        },
                        cornerRadius: 16,
                        glassIntensity: .light
                    )
                    .padding(.horizontal)
                    .padding(.bottom, 32)
                }
                .padding(.top)
            }
            .background(Color.glassBackground.ignoresSafeArea())
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.large)
            .liquidGlassNavigationBar()
            .sheet(isPresented: $showingSignIn) {
                // Sign in view would go here
                SignInPlaceholder()
            }
        }
    }
    
    private func testCoachingVoice() {
        let synthesizer = AVSpeechSynthesizer()
        let testText = "Great swing! Keep your left arm straight and rotate through your hips for more power."
        
        let utterance = AVSpeechUtterance(string: testText)
        utterance.rate = Float(coachingSpeechRate)
        utterance.pitchMultiplier = 1.05
        utterance.volume = 0.9
        
        // Select voice based on gender preference
        let languageCode = "en-US"
        let voices = AVSpeechSynthesisVoice.speechVoices().filter { $0.language.hasPrefix(languageCode) }
        
        if coachingVoiceGender == "female" {
            // Try to find a female voice
            if let femaleVoice = voices.first(where: { 
                $0.identifier.contains("Samantha") || 
                $0.identifier.contains("Ava") || 
                $0.identifier.contains("Zoe") ||
                $0.name.lowercased().contains("female")
            }) {
                utterance.voice = femaleVoice
            } else {
                utterance.voice = AVSpeechSynthesisVoice(language: languageCode)
            }
        } else {
            // Try to find a male voice
            if let maleVoice = voices.first(where: { 
                $0.identifier.contains("Alex") || 
                $0.identifier.contains("Daniel") || 
                $0.identifier.contains("Fred") ||
                $0.name.lowercased().contains("male")
            }) {
                utterance.voice = maleVoice
            } else {
                utterance.voice = AVSpeechSynthesisVoice(language: languageCode)
            }
        }
        
        synthesizer.speak(utterance)
        
        // Haptic feedback
        if enableHaptics {
            LiquidGlassHaptics.impact(.medium)
        }
    }
}

// Settings Toggle Row Component
struct SettingsToggleRow: View {
    let title: String
    let subtitle: String?
    let icon: String
    @Binding var isOn: Bool
    
    init(title: String, subtitle: String? = nil, icon: String, isOn: Binding<Bool>) {
        self.title = title
        self.subtitle = subtitle
        self.icon = icon
        self._isOn = isOn
    }
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(.fairwayGreen)
                .frame(width: 32)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                    .foregroundColor(.glassText)
                
                if let subtitle = subtitle {
                    Text(subtitle)
                        .font(.caption)
                        .foregroundColor(.glassSecondaryText)
                }
            }
            
            Spacer()
            
            Toggle("", isOn: $isOn)
                .labelsHidden()
                .tint(.fairwayGreen)
                .onChange(of: isOn) { _, _ in
                    LiquidGlassHaptics.impact(.light)
                }
        }
    }
}

// Info Row Component
struct InfoRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .font(.subheadline)
                .foregroundColor(.glassSecondaryText)
            Spacer()
            Text(value)
                .font(.subheadline)
                .foregroundColor(.glassText)
        }
    }
}

// Placeholder for Sign In View
struct SignInPlaceholder: View {
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            VStack {
                Text("Sign In View")
                    .font(.largeTitle)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.glassBackground)
            .navigationTitle("Sign In")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    SettingsView()
}