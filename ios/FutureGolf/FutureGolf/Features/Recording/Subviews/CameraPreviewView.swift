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
    
    class CameraContainerView: UIView {
        var previewLayer: AVCaptureVideoPreviewLayer?
        
        override func layoutSubviews() {
            super.layoutSubviews()
            
            // Ensure preview layer always matches view bounds
            CATransaction.begin()
            CATransaction.setDisableActions(true)
            previewLayer?.frame = bounds
            CATransaction.commit()
            
            print("📸 CameraContainerView: layoutSubviews - frame updated to: \(bounds)")
        }
    }

    func makeUIView(context: Context) -> UIView {
        let view = CameraContainerView()
        view.backgroundColor = .black
        
        print("📸 CameraPreviewView: makeUIView called. Session running: \(session.isRunning)")
        
        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.videoGravity = .resizeAspectFill
        
        // Store references
        view.previewLayer = previewLayer
        context.coordinator.previewLayer = previewLayer
        context.coordinator.containerView = view
        
        // Add the layer at index 0 to ensure it's behind any other layers
        view.layer.insertSublayer(previewLayer, at: 0)
        
        // Set initial frame
        previewLayer.frame = view.bounds
        
        // Ensure proper masking
        view.layer.masksToBounds = true
        
        // Check session status and connection
        if !session.isRunning {
            print("⚠️ CameraPreviewView: Session is not running when creating preview!")
        }
        
        if let connection = previewLayer.connection {
            print("📸 CameraPreviewView: Preview layer connection established. Enabled: \(connection.isEnabled), Active: \(connection.isActive)")
        } else {
            print("⚠️ CameraPreviewView: No connection on preview layer!")
        }
        
        print("📸 CameraPreviewView: Preview layer added to view")
        
        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        // Ensure preview layer fills the view and check connection
        if let containerView = uiView as? CameraContainerView {
            // Trigger layout update
            containerView.setNeedsLayout()
            
            // Debug session and connection status
            if let previewLayer = context.coordinator.previewLayer {
                print("📸 CameraPreviewView: updateUIView - Session running: \(session.isRunning)")
                if let connection = previewLayer.connection {
                    print("📸 CameraPreviewView: Connection - Enabled: \(connection.isEnabled), Active: \(connection.isActive)")
                }
            }
        }
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator {
        var previewLayer: AVCaptureVideoPreviewLayer?
        var containerView: CameraContainerView?
    }
}
