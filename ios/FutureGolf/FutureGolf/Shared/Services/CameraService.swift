import Foundation
import AVFoundation
import UIKit

@MainActor
class CameraService: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    var captureSession: AVCaptureSession?
    var videoInput: AVCaptureDeviceInput?
    var videoDataOutput: AVCaptureVideoDataOutput?
    var currentCamera: AVCaptureDevice?
    var cameraPosition: AVCaptureDevice.Position = .front
    var onFrameCaptured: ((UIImage) -> Void)?
    var onFramerateUpdate: ((Double) -> Void)?

    private let sessionQueue = DispatchQueue(label: "com.futuregolf.sessionQueue")
    private let frameRateCalculator = FrameRateCalculator()

    override init() {
        super.init()
    }

    func setupCamera(for position: AVCaptureDevice.Position) async throws {
        print("📸 CameraService: Setting up camera for position \(position).")
        self.cameraPosition = position
        let session = AVCaptureSession()
        
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
        
        try setupCameraInput(for: position, in: session)
        setupVideoDataOutput(for: session)
        
        session.commitConfiguration()
        
        self.captureSession = session
        print("📸 CameraService: Capture session configured.")
        
        try await startSession()
    }
    
    private func startSession() async throws {
        guard let session = captureSession else { throw RecordingError.cameraHardwareError }
        
        print("📸 CameraService: Attempting to start session...")
        await withCheckedContinuation { continuation in
            sessionQueue.async {
                session.startRunning()
                print("📸 CameraService: Session isRunning: \(session.isRunning)")
                continuation.resume()
            }
        }
    }

    func setupCameraInput(for position: AVCaptureDevice.Position, in session: AVCaptureSession) throws {
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

    private func setupVideoDataOutput(for session: AVCaptureSession) {
        videoDataOutput = AVCaptureVideoDataOutput()
        
        if let output = videoDataOutput {
            output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32BGRA)]
            output.alwaysDiscardsLateVideoFrames = true
            output.setSampleBufferDelegate(self, queue: sessionQueue)
            
            if session.canAddOutput(output) {
                session.addOutput(output)
            }
        }
    }

    func switchCamera() {
        guard let session = captureSession else { return }
        
        let newPosition: AVCaptureDevice.Position = (cameraPosition == .back) ? .front : .back
        cameraPosition = newPosition
        
        sessionQueue.async {
            session.beginConfiguration()
            do {
                try self.setupCameraInput(for: newPosition, in: session)
            } catch {
                print("Error switching camera: \(error)")
            }
            session.commitConfiguration()
        }
    }
    
    func setZoomLevel(_ zoom: CGFloat) {
        guard let device = currentCamera else { return }
        do {
            try device.lockForConfiguration()
            device.videoZoomFactor = zoom
            device.unlockForConfiguration()
        } catch {
            print("Error setting zoom level: \(error)")
        }
    }
    
    func stopSession() {
        sessionQueue.async {
            self.captureSession?.stopRunning()
        }
    }
    
    nonisolated func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        Task {
            let frameRate = await frameRateCalculator.calculateFrameRate(from: sampleBuffer)
            Task { @MainActor in
                self.onFramerateUpdate?(frameRate)
            }
        }
        
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

actor FrameRateCalculator {
    private var lastFrameTimestamp = CMTime.zero
    
    func calculateFrameRate(from sampleBuffer: CMSampleBuffer) -> Double {
        let currentTimestamp = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
        let delta = currentTimestamp - lastFrameTimestamp
        lastFrameTimestamp = currentTimestamp
        
        guard delta.seconds > 0 else { return 0 }
        
        return 1.0 / delta.seconds
    }
}
