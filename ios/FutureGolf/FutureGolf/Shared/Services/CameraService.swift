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

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: position) ?? AVCaptureDevice.default(for: .video) else {
            throw RecordingError.cameraHardwareError
        }

        self.currentCamera = camera

        do {
            try camera.lockForConfiguration()

//            if camera.isLowLightBoostSupported {
//                print("📸 Disabled low light boost.")
//            }

            var bestFormat: AVCaptureDevice.Format?
            let targetFrameRate = Config.preferredFrameRate

            // Find the best format that supports 1080p at the desired frame rate
            for format in camera.formats {
                let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
                if dimensions.width == 1920 && dimensions.height == 1080 {
                    for range in format.videoSupportedFrameRateRanges {
                        if range.maxFrameRate >= targetFrameRate {
                            bestFormat = format
                            break
                        }
                    }
                }
                if bestFormat != nil {
                    break
                }
            }

            var actualFrameRate = Config.fallbackFrameRate
            if let bestFormat = bestFormat {
                camera.activeFormat = bestFormat
                let frameDuration = CMTimeMake(value: 1, timescale: Int32(targetFrameRate))
                camera.activeVideoMinFrameDuration = frameDuration
                camera.activeVideoMaxFrameDuration = frameDuration
                actualFrameRate = targetFrameRate
                print("📸 Desired frame rate set to \(targetFrameRate) FPS for position \(position)")
            } else {
                print("⚠️ Could not find a 1920x1080 format supporting \(targetFrameRate) FPS for position \(position). Using default.")
                // If we couldn't set our preferred rate, let's read what the default is.
                if camera.activeVideoMinFrameDuration.seconds > 0 {
                    actualFrameRate = round(1.0 / camera.activeVideoMinFrameDuration.seconds)
                }
            }

            // Report the configured frame rate
            Task { @MainActor in
                self.onFramerateUpdate?(actualFrameRate)
            }

            camera.unlockForConfiguration()
        } catch {
            print("🚨 Could not lock camera for configuration: \(error)")
            // Report fallback frame rate on error
            Task { @MainActor in
                self.onFramerateUpdate?(Config.fallbackFrameRate)
            }
        }

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
        // Frame rate is now set during configuration, no need to calculate it here.
        
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
