import Foundation
import Combine

@MainActor
class TTSCacheService: ObservableObject {
    @Published var isReady = false
    @Published var progress: Double = 0.0
    
    private var ttsCacheCheckTimer: Timer?
    private var analysisResult: AnalysisResult?

    func startMonitoring(for result: AnalysisResult) {
        self.analysisResult = result
        
        // Stop any existing timer
        ttsCacheCheckTimer?.invalidate()
        
        // Pre-cache TTS phrases for analysis
        TTSPhraseManager.shared.registerAnalysisPhrases(from: result)
        
        // Start caching analysis phrases in background
        Task {
            TTSService.shared.cacheManager.warmCache()
        }
        
        // Check immediately
        Task {
            await checkStatus()
        }
        
        // Then check every 0.5 seconds until ready
        ttsCacheCheckTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            Task {
                await self?.checkStatus()
            }
        }
    }

    private func checkStatus() async {
        guard let result = analysisResult else { return }
        
        let phrases = getPhrases(from: result)
        guard !phrases.isEmpty else {
            isReady = true
            progress = 1.0
            stopMonitoring()
            return
        }
        
        var cachedCount = 0
        for phrase in phrases {
            if await TTSService.shared.cacheManager.getCachedAudio(for: phrase) != nil {
                cachedCount += 1
            }
        }
        
        progress = Double(cachedCount) / Double(phrases.count)
        isReady = (cachedCount == phrases.count)
        
        if isReady {
            print("🎬 All TTS phrases cached for analysis")
            stopMonitoring()
        } else {
            print("🎬 TTS cache progress: \(cachedCount)/\(phrases.count)")
        }
    }

    private func getPhrases(from result: AnalysisResult) -> [String] {
        let lines = parseCoachingScript(result.coachingScript)
        var allPhrases: [String] = lines.map { $0.text }
        for phase in result.swingPhases {
            allPhrases.append(phase.feedback)
        }
        return allPhrases
    }

    private func parseCoachingScript(_ script: String) -> [(text: String, startFrameNumber: Int)] {
        var lines: [(text: String, startFrameNumber: Int)] = []
        let sentences = script.components(separatedBy: CharacterSet(charactersIn: ".!?"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        
        for (index, sentence) in sentences.enumerated() {
            lines.append((
                text: sentence + ".",
                startFrameNumber: index * 60 // Placeholder
            ))
        }
        return lines
    }

    func stopMonitoring() {
        ttsCacheCheckTimer?.invalidate()
        ttsCacheCheckTimer = nil
    }

    deinit {
        Task { @MainActor in
            stopMonitoring()
        }
    }
}
