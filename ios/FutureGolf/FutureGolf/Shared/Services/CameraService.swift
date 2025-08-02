import Foundation
import AVFoundation
import UIKit

@MainActor
class CameraService: NSObject {
    var captureSession: AVCaptureSession?
    var videoInput: AVCaptureDeviceInput?
    var videoDataOutput: AVCaptureVideoDataOutput?
    var currentCamera: AVCaptureDevice?
    var cameraPosition: AVCaptureDevice.Position = .front
    var onFrameCaptured: ((UIImage) -> Void)?

    private let videoDataOutputQueue = DispatchQueue(label: "com.futuregolf.cameravideodata")

    override init() {
        super.init()
    }

    func setupCamera(for position: AVCaptureDevice.Position) async throws {
        self.cameraPosition = position
        captureSession = AVCaptureSession()
        
        guard let session = captureSession else {
            throw RecordingError.cameraHardwareError
        }
        
        let cameraAuthStatus = AVCaptureDevice.authorizationStatus(for: .video)
        if cameraAuthStatus != .authorized {
            if cameraAuthStatus == .notDetermined {
                let granted = await AVCaptureDevice.requestAccess(for: .video)
                if !granted {
                    throw RecordingError.cameraPermissionDenied
                }
            } else {
                throw RecordingError.cameraPermissionDenied
            }
        }
        
        session.beginConfiguration()
        
        if session.canSetSessionPreset(.hd1920x1080) {
            session.sessionPreset = .hd1920x1080
        }
        
        try setupCameraInput(for: position)
        setupVideoDataOutput()
        
        session.commitConfiguration()
        
        DispatchQueue.global(qos: .userInitiated).async {
            session.startRunning()
        }
    }

    func setupCameraInput(for position: AVCaptureDevice.Position) throws {
        guard let session = captureSession else { return }
        
        if let existingInput = videoInput {
            session.removeInput(existingInput)
        }
        
        let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: position) ?? AVCaptureDevice.default(for: .video)
        
        guard let camera = camera else {
            throw RecordingError.cameraHardwareError
        }
        
        self.currentCamera = camera
        
        let input = try AVCaptureDeviceInput(device: camera)
        
        if session.canAddInput(input) {
            session.addInput(input)
            self.videoInput = input
        } else {
            throw RecordingError.cameraHardwareError
        }
    }

    private func setupVideoDataOutput() {
        guard let session = captureSession else { return }
        
        videoDataOutput = AVCaptureVideoDataOutput()
        
        if let output = videoDataOutput {
            output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32BGRA)]
            output.alwaysDiscardsLateVideoFrames = true
            output.setSampleBufferDelegate(self, queue: videoDataOutputQueue)
            
            if session.canAddOutput(output) {
                session.addOutput(output)
            }
        }
    }

    func switchCamera() {
        let newPosition: AVCaptureDevice.Position = (cameraPosition == .back) ? .front : .back
        cameraPosition = newPosition
        
        Task {
            try? setupCameraInput(for: newPosition)
        }
    }
    
    func setZoomLevel(_ zoom: CGFloat) {
        guard let device = currentCamera else { return }
        
        do {
            try device.lockForConfiguration()
            let maxZoom = min(device.activeFormat.videoMaxZoomFactor, 4.0)
            let scaledZoom = 1.0 + (1.0 - zoom) * (maxZoom - 1.0)
            device.videoZoomFactor = scaledZoom
            device.unlockForConfiguration()
        } catch {
            print("Error setting zoom level: \(error)")
        }
    }
    
    func stopSession() {
        captureSession?.stopRunning()
    }
}

extension CameraService: AVCaptureVideoDataOutputSampleBufferDelegate {
    nonisolated func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()
        
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return }
        
        let image = UIImage(cgImage: cgImage)
        
        Task { @MainActor in
            self.onFrameCaptured?(image)
        }
    }
}
