import Foundation
import AVFoundation

class RecordingService: NSObject, AVCaptureFileOutputRecordingDelegate {
    private var videoOutput: AVCaptureMovieFileOutput?
    private var onRecordingFinished: ((URL?, Error?) -> Void)?

    func setupVideoOutput(for session: AVCaptureSession) {
        videoOutput = AVCaptureMovieFileOutput()
        if let output = videoOutput, session.canAddOutput(output) {
            session.addOutput(output)
        }
    }

    func startRecording(completion: @escaping (URL?, Error?) -> Void) {
        self.onRecordingFinished = completion
        let outputURL = createOutputFileURL()
        print("🎥 RecordingService: Starting recording to URL: \(outputURL.path)")
        videoOutput?.startRecording(to: outputURL, recordingDelegate: self)
    }

    func stopRecording() {
        videoOutput?.stopRecording()
    }

    private func createOutputFileURL() -> URL {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let fileName = "swing_recording_\(Date().timeIntervalSince1970).mp4"
        return documentsPath.appendingPathComponent(fileName)
    }

    func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
        if let error = error {
            print("🎥 RecordingService: Recording finished with error: \(error.localizedDescription)")
        } else {
            print("🎥 RecordingService: Recording finished successfully at URL: \(outputFileURL.path)")
            // Verify the file exists
            if FileManager.default.fileExists(atPath: outputFileURL.path) {
                print("🎥 RecordingService: Verified file exists at path.")
            } else {
                print("🚨 RecordingService: ERROR - File does not exist at path after recording finished.")
            }
        }
        onRecordingFinished?(outputFileURL, error)
    }
}