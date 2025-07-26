import SwiftUI
import PhotosUI
import AVKit

struct ContentView: View {
    @State private var viewModel = VideoAnalysisViewModel()
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                if let videoURL = viewModel.selectedVideoURL {
                    VideoPlayer(player: AVPlayer(url: videoURL))
                        .frame(height: 300)
                        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 16, style: .continuous)
                                .strokeBorder(.thinMaterial, lineWidth: 1)
                        )
                        .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
                        .padding(.horizontal)
                }
                
                PhotosPicker(
                    selection: $viewModel.selectedItem,
                    matching: .videos
                ) {
                    Label("Select Video from Library", systemImage: "photo.on.rectangle")
                        .padding()
                        .buttonStyle(.borderedProminent)
                        .controlSize(.large)
                }
                .onChange(of: viewModel.selectedItem) { _, newItem in
                    Task {
                        await viewModel.loadVideo(from: newItem)
                    }
                }
                
                if viewModel.isUploading {
                    ProgressView("Uploading...")
                        .padding()
                }
                
                if viewModel.selectedVideoURL != nil && !viewModel.isUploading {
                    Button(action: {
                        Task {
                            await viewModel.uploadVideo()
                        }
                    }) {
                        Label("Analyze Video", systemImage: "waveform.badge.magnifyingglass")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .tint(.green)
                    .padding(.horizontal)
                }
                
                if let analysisResult = viewModel.analysisResult {
                    NavigationLink(destination: AnalysisResultView(result: analysisResult)) {
                        Label("View Analysis", systemImage: "chart.line.text.clipboard")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .tint(.purple)
                    .padding(.horizontal)
                }
                
                Spacer()
            }
            .navigationTitle("FutureGolf")
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK") { }
            } message: {
                Text(viewModel.errorMessage)
            }
        }
    }
}

#Preview {
    ContentView()
}