import SwiftUI
import AVFoundation

struct CameraPreviewView: UIViewRepresentable {
    var viewModel: RecordingViewModel
    
    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        view.backgroundColor = .black
        context.coordinator.previewView = view
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {
        context.coordinator.previewView = uiView
        context.coordinator.setupPreviewLayer(for: viewModel.captureSession, in: uiView)
    }
    
    func makeCoordinator() -> CameraPreviewCoordinator {
        return CameraPreviewCoordinator()
    }
    
    class CameraPreviewCoordinator: NSObject {
        weak var previewView: UIView?
        private var previewLayer: AVCaptureVideoPreviewLayer?
        
        func setupPreviewLayer(for session: AVCaptureSession?, in view: UIView) {
            guard let session = session else { return }
            
            if let existingLayer = previewLayer {
                existingLayer.removeFromSuperlayer()
                previewLayer = nil
            }
            
            let newPreviewLayer = AVCaptureVideoPreviewLayer(session: session)
            newPreviewLayer.videoGravity = .resizeAspectFill
            newPreviewLayer.frame = view.bounds
            newPreviewLayer.backgroundColor = UIColor.black.cgColor
            
            view.layer.addSublayer(newPreviewLayer)
            previewLayer = newPreviewLayer
            
            DispatchQueue.global(qos: .userInitiated).async {
                if !session.isRunning {
                    session.startRunning()
                }
            }
        }
        
        deinit {
            previewLayer?.removeFromSuperlayer()
        }
    }
}
