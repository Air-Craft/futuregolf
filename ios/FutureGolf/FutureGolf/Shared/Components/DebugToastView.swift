import SwiftUI

struct DebugToastView: View {
    @State private var progressToastId: String?
    @State private var progress: Double = 0.0
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Toast Debug")
                .font(.title)
                .fontWeight(.bold)
            
            // Basic toasts
            VStack(spacing: 10) {
                Text("Basic Toasts")
                    .font(.headline)
                
                Button("Show Info Toast") {
                    ToastManager.shared.show("This is an info message", type: .info)
                }
                
                Button("Show Success Toast") {
                    ToastManager.shared.show("Operation successful!", type: .success)
                }
                
                Button("Show Warning Toast") {
                    ToastManager.shared.show("Please be careful", type: .warning)
                }
                
                Button("Show Error Toast") {
                    ToastManager.shared.show("Something went wrong", type: .error)
                }
            }
            .buttonStyle(.bordered)
            
            Divider()
            
            // Progress toast
            VStack(spacing: 10) {
                Text("Progress Toast")
                    .font(.headline)
                
                Button("Start Progress") {
                    progress = 0.0
                    progressToastId = ToastManager.shared.showProgress("Caching TTS...", progress: 0.0)
                    
                    // Simulate progress
                    Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { timer in
                        progress += 0.05
                        
                        Task { @MainActor in
                            if progress >= 1.0 {
                                timer.invalidate()
                                if let id = progressToastId {
                                    ToastManager.shared.dismissProgress(id: id)
                                    ToastManager.shared.show("TTS cache ready!", type: .success)
                                    progressToastId = nil
                                }
                            } else {
                                if let id = progressToastId {
                                    let phraseCount = 6
                                    let completed = Int(progress * Double(phraseCount))
                                    ToastManager.shared.updateProgress(
                                        id: id,
                                        progress: progress,
                                        label: "Caching TTS... (\(completed)/\(phraseCount))"
                                    )
                                }
                            }
                        }
                    }
                }
                .disabled(progressToastId != nil)
                
                Button("Cancel Progress") {
                    if let id = progressToastId {
                        ToastManager.shared.dismissProgress(id: id)
                        progressToastId = nil
                    }
                }
                .disabled(progressToastId == nil)
            }
            .buttonStyle(.bordered)
            
            Spacer()
        }
        .padding()
        .navigationTitle("Toast Debug")
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationView {
        DebugToastView()
    }
    .withToastOverlay()
}