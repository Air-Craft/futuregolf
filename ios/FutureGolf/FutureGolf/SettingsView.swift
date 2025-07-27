import SwiftUI

struct SettingsView: View {
    @AppStorage("apiEndpoint") private var apiEndpoint = "http://192.168.1.114:8000"
    @AppStorage("viewType") private var viewType = "face-on"
    @AppStorage("golferHandedness") private var golferHandedness = "right"
    
    var body: some View {
        NavigationStack {
            Form {
                Section("API Configuration") {
                    TextField("API Endpoint", text: $apiEndpoint)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                        .textContentType(.URL)
                }
                
                Section("Video Settings") {
                    Picker("View Type", selection: $viewType) {
                        Text("Face On").tag("face-on")
                        Text("Down the Line").tag("down-the-line")
                    }
                    
                    Picker("Golfer Handedness", selection: $golferHandedness) {
                        Text("Right Handed").tag("right")
                        Text("Left Handed").tag("left")
                    }
                }
                
                Section("Account") {
                    Button("Sign In") {
                        // TODO: Implement sign in
                    }
                    
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Settings")
            .scrollContentBackground(.hidden)
            .background(.regularMaterial)
        }
    }
}

#Preview {
    SettingsView()
}