import SwiftUI

struct PreviousAnalysesView: View {
    @StateObject private var storageManager = AnalysisStorageManager.shared
    @State private var showRecordingScreen = false
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        ZStack {
            // Background
            Color(UIColor.systemBackground)
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                // Header with back button
                HStack {
                    Button(action: {
                        dismiss()
                    }) {
                        Label("Home", systemImage: "chevron.left")
                            .foregroundColor(.primary)
                    }
                    
                    Spacer()
                    
                    Text("Previous Analyses")
                        .font(.headline)
                    
                    Spacer()
                    
                    // Placeholder for balance
                    Color.clear
                        .frame(width: 60)
                }
                .padding()
                
                // Analyses list
                ScrollView {
                    VStack(spacing: 16) {
                        // Record new swing button
                        Button(action: {
                            showRecordingScreen = true
                        }) {
                            HStack {
                                Image(systemName: "video.circle.fill")
                                    .font(.largeTitle)
                                    .foregroundColor(.white)
                                
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("Analyze My Swing")
                                        .font(.headline)
                                        .foregroundColor(.white)
                                    Text("Record a new swing video")
                                        .font(.caption)
                                        .foregroundColor(.white.opacity(0.8))
                                }
                                
                                Spacer()
                                
                                Image(systemName: "chevron.right")
                                    .foregroundColor(.white.opacity(0.6))
                            }
                            .padding()
                            .background(Color.fairwayGreen)
                            .cornerRadius(12)
                        }
                        .padding(.horizontal)
                        
                        // Previous analyses
                        ForEach(storageManager.storedAnalyses.sorted(by: { $0.recordedAt > $1.recordedAt })) { analysis in
                            AnalysisRow(analysis: analysis)
                                .padding(.horizontal)
                        }
                    }
                    .padding(.vertical)
                }
            }
        }
        .navigationBarHidden(true)
        .fullScreenCover(isPresented: $showRecordingScreen) {
            NavigationView {
                RecordingScreen()
            }
        }
    }
}

struct AnalysisRow: View {
    let analysis: StoredAnalysis
    @StateObject private var storageManager = AnalysisStorageManager.shared
    @State private var showAnalysis = false
    
    private var statusColor: Color {
        switch analysis.status {
        case .completed:
            return .green
        case .pending, .uploading, .analyzing:
            return .orange
        case .failed:
            return .red
        }
    }
    
    private var statusText: String {
        switch analysis.status {
        case .pending:
            return "Waiting for connection"
        case .uploading:
            return "Uploading..."
        case .analyzing:
            return "Analyzing..."
        case .completed:
            return "Complete"
        case .failed:
            return "Failed"
        }
    }
    
    var body: some View {
        Button(action: {
            showAnalysis = true
        }) {
            HStack(spacing: 16) {
                // Thumbnail
                ZStack {
                    if let thumbnail = storageManager.getThumbnail(id: analysis.id) {
                        Image(uiImage: thumbnail)
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                            .frame(width: 80, height: 60)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    } else {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.gray.opacity(0.3))
                            .frame(width: 80, height: 60)
                        
                        Image(systemName: "video")
                            .foregroundColor(.gray)
                    }
                    
                    // Status overlay for pending
                    if analysis.status == .pending {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.black.opacity(0.6))
                        
                        Image(systemName: "wifi.slash")
                            .foregroundColor(.white)
                            .font(.caption)
                    }
                }
                
                // Details
                VStack(alignment: .leading, spacing: 4) {
                    Text(analysis.recordedAt.formatted(date: .abbreviated, time: .shortened))
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    HStack {
                        Circle()
                            .fill(statusColor)
                            .frame(width: 8, height: 8)
                        
                        Text(statusText)
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        if analysis.status == .uploading {
                            Text("\(Int(analysis.uploadProgress * 100))%")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(Color.gray.opacity(0.1))
            .cornerRadius(12)
        }
        .buttonStyle(PlainButtonStyle())
        .fullScreenCover(isPresented: $showAnalysis) {
            SwingAnalysisView(
                videoURL: analysis.videoURL,
                analysisId: analysis.id
            )
        }
    }
}

#Preview {
    PreviousAnalysesView()
}