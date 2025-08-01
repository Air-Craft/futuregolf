import Foundation
import AVFoundation
import Combine

/// Manages TTS audio caching for instant playback
class TTSCacheManager: ObservableObject {
    
    // MARK: - Properties
    
    private let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
    private let cacheDirectory: URL
    private let audioDirectory: URL
    private let metadataFile: URL
    private let tempDirectory: URL
    
    @Published var isCacheWarming = false
    @Published var cacheWarmingProgress: Double = 0.0
    
    private var connectivityCallbackId: UUID?
    private var progressToastId: String?
    
    // MARK: - Initialization
    
    init() {
        self.cacheDirectory = documentsDirectory.appendingPathComponent(Config.ttsCacheDirectory)
        self.audioDirectory = cacheDirectory.appendingPathComponent("audio")
        self.metadataFile = cacheDirectory.appendingPathComponent("metadata.json")
        self.tempDirectory = cacheDirectory.appendingPathComponent("temp")
        
        // Create directories if needed
        createDirectoriesIfNeeded()
        
        // Setup connectivity monitoring
        setupConnectivityMonitoring()
    }
    
    deinit {
        if let id = connectivityCallbackId {
            Task { @MainActor in
                ConnectivityService.shared.removeCallback(id)
            }
        }
    }
    
    // MARK: - Public Methods
    
    /// Warm the cache by pre-generating all recording journey audio
    func warmCache() {
        Task { @MainActor in
            print("🗣️💾 TTS Cache: Starting cache warm-up process...")
            
            // Check connectivity first
            guard ConnectivityService.shared.isConnected else {
                print("🗣️💾 TTS Cache: No network connection available, postponing cache warm-up")
                
                // Register for connectivity restoration if cache needs refresh
                if shouldRefreshCache() {
                    print("🗣️💾 TTS Cache: Registering for connectivity restoration callback")
                    registerForConnectivityRestoration()
                }
                return
            }
            
            print("🗣️💾 TTS Cache: Network connected, proceeding with cache check")
            let phrasesToCache = TTSPhraseManager.shared.getAllPhrases()
            print("🗣️💾 TTS Cache: Total phrases to cache: \(phrasesToCache.count)")
            
            // Check if force refresh is enabled
            if Config.ttsForceCacheRefreshOnLaunch {
                print("🗣️💾 TTS Cache: Force refresh enabled, clearing existing cache")
                clearCache()
            }
            
            // Check existing cache
            if let metadata = loadMetadata() {
                let age = Date().timeIntervalSince(metadata.lastRefresh)
                print("🗣️💾 TTS Cache: Found existing cache, age: \(String(format: "%.1f", age/3600)) hours")
                print("🗣️💾 TTS Cache: Cached phrases count: \(metadata.phrases.count)")
                
                // Verify cached files actually exist
                var validPhrases = 0
                for (_, phrase) in metadata.phrases {
                    let audioFile = audioDirectory.appendingPathComponent(phrase.filename)
                    if FileManager.default.fileExists(atPath: audioFile.path) {
                        validPhrases += 1
                    }
                }
                
                if validPhrases != metadata.phrases.count {
                    print("🗣️💾 TTS Cache: Cache inconsistent - expected \(metadata.phrases.count) files, found \(validPhrases)")
                    print("🗣️💾 TTS Cache: Forcing cache refresh due to missing files")
                    clearCache()
                    refreshCacheInBackground()
                    return
                }
                
                if !shouldRefreshCache() {
                    print("🗣️💾 TTS Cache: Cache is fresh and valid, skipping refresh")
                    return
                } else {
                    print("🗣️💾 TTS Cache: Cache needs refresh (interval: \(Config.ttsCacheRefreshInterval/3600) hours)")
                }
            } else {
                print("🗣️💾 TTS Cache: No existing cache found, creating new cache")
            }
            
            print("🗣️💾 TTS Cache: Starting background refresh...")
            refreshCacheInBackground()
        }
    }
    
    /// Get cached audio data for a given text
    func getCachedAudio(for text: String) async -> Data? {
        guard let phrase = TTSPhraseManager.shared.phraseFor(text: text) else {
            return nil
        }
        
        let audioFile = audioDirectory.appendingPathComponent(phrase.filename)
        
        do {
            let data = try Data(contentsOf: audioFile)
            print("🗣️💾 TTS Cache: Retrieved cached audio for '\(text.prefix(30))...' (\(data.count) bytes)")
            return data
        } catch {
            print("🗣️💾 TTS Cache: Failed to read cached audio for '\(text.prefix(30))...': \(error)")
            return nil
        }
    }
    
    /// Save audio data to cache
    func saveToCacheIfCacheable(text: String, data: Data) {
        guard let phrase = TTSPhraseManager.shared.phraseFor(text: text) else {
            return // Not a cacheable phrase
        }
        
        let audioFile = audioDirectory.appendingPathComponent(phrase.filename)
        
        do {
            try data.write(to: audioFile)
            
            // Update metadata
            let metadata = loadMetadata() ?? TTSCacheMetadata()
            var phrases = metadata.phrases
            phrases[phrase.hash] = GenericCachedPhrase(phrase: phrase, size: Int64(data.count))
            
            let updatedMetadata = TTSCacheMetadata(phrases: phrases)
            try saveMetadata(updatedMetadata)
            
            print("🗣️💾 TTS Cache: Saved audio to cache for '\(text.prefix(30))...' (\(data.count) bytes)")
        } catch {
            print("🗣️💾 TTS Cache: Failed to save audio to cache: \(error)")
        }
    }
    
    /// Check if cache should be refreshed
    func shouldRefreshCache() -> Bool {
        if Config.ttsForceCacheRefreshOnLaunch {
            return true
        }
        
        guard let metadata = loadMetadata() else {
            return true
        }
        
        let age = Date().timeIntervalSince(metadata.lastRefresh)
        return age > Config.ttsCacheRefreshInterval
    }
    
    /// Get cache status information
    func getCacheStatus() -> (exists: Bool, phraseCount: Int, lastRefresh: Date?) {
        guard let metadata = loadMetadata() else {
            return (false, 0, nil)
        }
        return (true, metadata.phrases.count, metadata.lastRefresh)
    }
    
    /// Clear all cached data
    func clearCache() {
        do {
            try FileManager.default.removeItem(at: cacheDirectory)
            createDirectoriesIfNeeded()
            print("🗣️💾 TTS Cache: Cache cleared successfully")
        } catch {
            print("🗣️💾 TTS Cache: Failed to clear cache: \(error)")
        }
    }
    
    /// Debug: List all cached files
    func debugListCachedFiles() {
        print("🗣️💾 TTS Cache Debug: Listing cached files...")
        print("🗣️💾   Cache directory: \(cacheDirectory.path)")
        print("🗣️💾   Is cache warming: \(isCacheWarming)")
        print("🗣️💾   Cache warming progress: \(String(format: "%.0f%%", cacheWarmingProgress * 100))")
        
        do {
            // Check if directories exist
            print("🗣️💾   Cache dir exists: \(FileManager.default.fileExists(atPath: cacheDirectory.path))")
            print("🗣️💾   Audio dir exists: \(FileManager.default.fileExists(atPath: audioDirectory.path))")
            print("🗣️💾   Temp dir exists: \(FileManager.default.fileExists(atPath: tempDirectory.path))")
            
            let audioFiles = try FileManager.default.contentsOfDirectory(at: audioDirectory, includingPropertiesForKeys: [.fileSizeKey])
            print("🗣️💾   Audio files count: \(audioFiles.count)")
            
            for file in audioFiles {
                let size = try file.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
                print("🗣️💾   - \(file.lastPathComponent) (\(size) bytes)")
            }
            
            if let metadata = loadMetadata() {
                print("🗣️💾   Metadata phrases: \(metadata.phrases.count)")
                for (hash, phrase) in metadata.phrases {
                    print("🗣️💾   - \(hash): '\(phrase.text.prefix(30))...' (\(phrase.size) bytes)")
                }
            } else {
                print("🗣️💾   No metadata file found")
            }
        } catch {
            print("🗣️💾   Error listing files: \(error)")
        }
    }
    
    // MARK: - Private Methods
    
    private func setupConnectivityMonitoring() {
        Task { @MainActor in
            // Register for connectivity restoration
            connectivityCallbackId = ConnectivityService.shared.onConnectivityRestored { [weak self] in
                guard let self = self else { return }
                
                // Check if we have pending cache warming
                if !self.isCacheWarming && self.shouldRefreshCache() {
                    print("🗣️💾 TTS Cache: Connectivity restored, starting cache warm-up")
                    self.warmCache()
                }
            }
        }
    }
    
    private func registerForConnectivityRestoration() {
        // Only register if not already registered
        guard connectivityCallbackId == nil else { 
            print("🗣️💾 TTS Cache: Already registered for connectivity restoration")
            return 
        }
        
        Task { @MainActor in
            connectivityCallbackId = ConnectivityService.shared.onConnectivityRestored { [weak self] in
                guard let self = self else { return }
                
                print("🗣️💾 TTS Cache: Connectivity restored callback triggered")
                
                // Remove the callback after it's used
                if let id = self.connectivityCallbackId {
                    ConnectivityService.shared.removeCallback(id)
                    self.connectivityCallbackId = nil
                }
                
                // Start cache warming
                if !self.isCacheWarming && self.shouldRefreshCache() {
                    print("🗣️💾 TTS Cache: Starting cache warm-up after connectivity restored")
                    self.warmCache()
                }
            }
            
            print("🗣️💾 TTS Cache: Registered for connectivity restoration with ID: \(String(describing: connectivityCallbackId))")
        }
    }
    
    private func createDirectoriesIfNeeded() {
        for directory in [cacheDirectory, audioDirectory, tempDirectory] {
            do {
                try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            } catch {
                print("🗣️💾 TTS Cache: Failed to create directory \(directory.lastPathComponent): \(error)")
            }
        }
    }
    
    private func refreshCacheInBackground() {
        Task {
            print("🗣️💾 TTS Cache: Task started for background cache refresh")
            
            // Note: Connectivity is already checked in warmCache(), so we can proceed here
            
            await MainActor.run {
                isCacheWarming = true
                cacheWarmingProgress = 0.0
                print("🗣️💾 TTS Cache: Set isCacheWarming to true")
                
                #if DEBUG
                // Show progress toast
                progressToastId = ToastManager.shared.showProgress("Caching TTS...", progress: 0.0)
                #endif
            }
            
            let phrasesToCache = TTSPhraseManager.shared.getAllPhrases()
            print("🗣️💾 TTS Cache: Beginning background cache refresh for \(phrasesToCache.count) phrases")
            print("🗣️💾 TTS Cache: Server URL: \(Config.serverBaseURL)")
            let startTime = Date()
            
            // Clear temp directory
            clearTempDirectory()
            print("🗣️💾 TTS Cache: Cleared temp directory")
            
            print("🗣️💾 TTS Cache: Starting task group for \(phrasesToCache.count) phrases")
            
            await withTaskGroup(of: (any TTSCacheablePhrase, Result<Data, Error>).self) { group in
                let phrases = phrasesToCache
                let totalCount = Double(phrases.count)
                
                print("🗣️💾 TTS Cache: Adding \(phrases.count) tasks to group")
                
                for (index, phrase) in phrases.enumerated() {
                    print("🗣️💾 TTS Cache: Adding task \(index + 1)/\(phrases.count) for phrase: '\(phrase.text.prefix(20))...'")
                    
                    group.addTask {
                        print("🗣️💾 TTS Cache: Task \(index + 1) started - Synthesizing phrase \(phrase.id): '\(phrase.text.prefix(30))...'")
                        do {
                            let data = try await self.synthesizePhrase(phrase.text)
                            print("🗣️💾 TTS Cache: ✅ Successfully cached phrase \(phrase.id) (\(data.count) bytes)")
                            return (phrase, .success(data))
                        } catch {
                            print("🗣️💾 TTS Cache: ❌ Failed to cache phrase \(phrase.id): \(error)")
                            print("🗣️💾 TTS Cache: Error details: \(error.localizedDescription)")
                            if let ttserror = error as? TTSError {
                                print("🗣️💾 TTS Cache: TTS Error type: \(ttserror)")
                            }
                            return (phrase, .failure(error))
                        }
                    }
                }
                
                print("🗣️💾 TTS Cache: Waiting for all tasks to complete...")
                
                var successCount = 0
                var failureCount = 0
                var tempCachedPhrases: [String: GenericCachedPhrase] = [:]
                
                for await (phrase, result) in group {
                    print("🗣️💾 TTS Cache: Received result for phrase: '\(phrase.text.prefix(20))...'")
                    
                    switch result {
                    case .success(let data):
                        print("🗣️💾 TTS Cache: Saving temp file for phrase: \(phrase.id)")
                        saveToCacheTemp(phrase: phrase, data: data)
                        tempCachedPhrases[phrase.hash] = GenericCachedPhrase(phrase: phrase, size: Int64(data.count))
                        successCount += 1
                        print("🗣️💾 TTS Cache: Progress: \(successCount)/\(phrases.count) succeeded")
                    case .failure(let error):
                        failureCount += 1
                        print("🗣️💾 TTS Cache: Progress: \(failureCount) failed, error: \(error)")
                    }
                    
                    // Update progress
                    let currentProgress = Double(successCount + failureCount) / totalCount
                    let currentSuccessCount = successCount
                    let totalPhraseCount = phrases.count
                    
                    await MainActor.run {
                        cacheWarmingProgress = currentProgress
                        print("🗣️💾 TTS Cache: Updated progress to \(String(format: "%.0f%%", currentProgress * 100))")
                        
                        #if DEBUG
                        // Update progress toast
                        if let toastId = progressToastId {
                            ToastManager.shared.updateProgress(
                                id: toastId, 
                                progress: currentProgress,
                                label: "Caching TTS... (\(currentSuccessCount)/\(totalPhraseCount))"
                            )
                        }
                        #endif
                    }
                }
                
                let elapsed = Date().timeIntervalSince(startTime)
                print("🗣️💾 TTS Cache: Cache refresh completed in \(String(format: "%.2f", elapsed))s")
                print("🗣️💾 TTS Cache: Success: \(successCount), Failed: \(failureCount)")
                
                if successCount == phrases.count {
                    atomicallyReplaceCache(with: tempCachedPhrases)
                    print("🗣️💾 TTS Cache: Cache successfully updated")
                } else {
                    print("🗣️💾 TTS Cache: ⚠️ Partial cache update, keeping existing cache")
                }
                
                let finalSuccessCount = successCount
                let totalPhrases = phrases.count
                
                await MainActor.run {
                    isCacheWarming = false
                    cacheWarmingProgress = 1.0
                    
                    #if DEBUG
                    // Dismiss progress toast and show result
                    if let toastId = progressToastId {
                        ToastManager.shared.dismissProgress(id: toastId)
                        progressToastId = nil
                        
                        if finalSuccessCount == totalPhrases {
                            ToastManager.shared.show("TTS cache ready!", type: .success)
                        } else if finalSuccessCount > 0 {
                            ToastManager.shared.show("TTS cache partially ready (\(finalSuccessCount)/\(totalPhrases))", type: .warning)
                        } else {
                            ToastManager.shared.show("TTS cache failed", type: .error)
                        }
                    }
                    #endif
                }
            }
        }
    }
    
    private func synthesizePhrase(_ text: String) async throws -> Data {
        let urlString = "\(Config.serverBaseURL)/api/v1/tts/coaching"
        print("🗣️💾 TTS Cache: Synthesizing from URL: \(urlString)")
        
        guard let url = URL(string: urlString) else {
            print("🗣️💾 TTS Cache: Invalid URL: \(urlString)")
            throw TTSError.invalidURL
        }
        
        let requestBody = TTSRequest(
            text: text,
            voice: "onyx",
            model: "tts-1-hd",
            speed: 0.9
        )
        
        let session = URLSession.shared
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(requestBody)
        request.timeoutInterval = Config.ttsSynthesisTimeout
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                print("🗣️💾 TTS Cache: Invalid response type")
                throw TTSError.invalidResponse
            }
            
            print("🗣️💾 TTS Cache: HTTP Status: \(httpResponse.statusCode)")
            
            guard httpResponse.statusCode == 200 else {
                print("🗣️💾 TTS Cache: Server error: \(httpResponse.statusCode)")
                if let errorData = String(data: data, encoding: .utf8) {
                    print("🗣️💾 TTS Cache: Error response: \(errorData)")
                }
                throw TTSError.serverError(httpResponse.statusCode)
            }
            
            print("🗣️💾 TTS Cache: Received \(data.count) bytes of audio data")
            return data
        } catch let error as URLError {
            print("🗣️💾 TTS Cache: Network error: \(error.code) - \(error.localizedDescription)")
            throw TTSError.networkError
        } catch {
            print("🗣️💾 TTS Cache: Unexpected error: \(error)")
            throw error
        }
    }
    
    private func saveToCacheTemp(phrase: any TTSCacheablePhrase, data: Data) {
        let tempAudioFile = tempDirectory.appendingPathComponent(phrase.filename)
        
        do {
            try data.write(to: tempAudioFile)
        } catch {
            print("🗣️💾 TTS Cache: Failed to save temp audio for \(phrase.id): \(error)")
        }
    }
    
    private func atomicallyReplaceCache(with phrases: [String: GenericCachedPhrase]) {
        do {
            // Move temp audio files to final location
            let tempAudioFiles = try FileManager.default.contentsOfDirectory(at: tempDirectory, includingPropertiesForKeys: nil)
            
            for tempFile in tempAudioFiles {
                let finalFile = audioDirectory.appendingPathComponent(tempFile.lastPathComponent)
                
                // Remove existing file if it exists
                if FileManager.default.fileExists(atPath: finalFile.path) {
                    try FileManager.default.removeItem(at: finalFile)
                }
                
                // Move temp file to final location
                try FileManager.default.moveItem(at: tempFile, to: finalFile)
            }
            
            // Update metadata
            let metadata = TTSCacheMetadata(phrases: phrases)
            try saveMetadata(metadata)
            
            // Clear temp directory
            clearTempDirectory()
            
        } catch {
            print("🗣️💾 TTS Cache: Failed to atomically replace cache: \(error)")
        }
    }
    
    private func clearTempDirectory() {
        do {
            try FileManager.default.removeItem(at: tempDirectory)
            try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
        } catch {
            print("🗣️💾 TTS Cache: Failed to clear temp directory: \(error)")
        }
    }
    
    private func loadMetadata() -> TTSCacheMetadata? {
        do {
            let data = try Data(contentsOf: metadataFile)
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(TTSCacheMetadata.self, from: data)
        } catch {
            print("🗣️💾 TTS Cache: Failed to load metadata: \(error)")
            return nil
        }
    }
    
    private func saveMetadata(_ metadata: TTSCacheMetadata) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        encoder.dateEncodingStrategy = .iso8601
        
        let data = try encoder.encode(metadata)
        try data.write(to: metadataFile)
    }
}

// MARK: - TTS Request Model (shared with TTSService)

struct TTSRequest: Codable {
    let text: String
    let voice: String
    let model: String
    let speed: Double
}

// MARK: - TTS Error Types (shared with TTSService)

enum TTSError: LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid TTS server URL"
        case .invalidResponse:
            return "Invalid server response"
        case .serverError(let code):
            return "Server error: \(code)"
        case .networkError:
            return "Network error"
        }
    }
}
