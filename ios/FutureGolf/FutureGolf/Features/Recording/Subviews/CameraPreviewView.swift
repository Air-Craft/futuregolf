import SwiftUI
import AVFoundation

struct CameraPreviewView: View {
    let session: AVCaptureSession

    var body: some View {
        VideoPreview(session: session)
    }
}

struct VideoPreview: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        view.backgroundColor = .systemPink // Bright pink for easy debugging
        
        print("📸 CameraPreviewView: makeUIView called.")
        
        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.videoGravity = .resizeAspectFill
        
        // Use DispatchQueue.main.async to ensure layer is added on main thread after view is in hierarchy
        DispatchQueue.main.async {
            previewLayer.frame = view.bounds
            view.layer.addSublayer(previewLayer)
            print("📸 CameraPreviewView: Preview layer added to view.")
        }
        
        context.coordinator.previewLayer = previewLayer
        
        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        // This ensures the layer resizes correctly on orientation change, etc.
        DispatchQueue.main.async {
            context.coordinator.previewLayer?.frame = uiView.bounds
        }
        print("📸 CameraPreviewView: updateUIView called, frame: \(uiView.frame)")
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator {
        var previewLayer: AVCaptureVideoPreviewLayer?
    }
}
