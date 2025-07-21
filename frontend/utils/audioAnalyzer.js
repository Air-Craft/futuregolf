/**
 * Audio Analyzer Utility
 * Provides real-time audio analysis including RMS extraction
 * with smoothing for animation purposes
 */

export class AudioAnalyzer {
  constructor(options = {}) {
    this.smoothingFactor = options.smoothingFactor || 0.3; // 0.3 = 30% new, 70% old
    this.minRMS = options.minRMS || 0;
    this.maxRMS = options.maxRMS || 1;
    this.previousRMS = 0;
    this.rmsHistory = [];
    this.historySize = options.historySize || 10;
  }

  /**
   * Calculate Root Mean Square (RMS) of audio buffer
   * @param {Float32Array|Uint8Array} buffer - Audio buffer
   * @returns {number} RMS value between 0 and 1
   */
  calculateRMS(buffer) {
    if (!buffer || buffer.length === 0) {
      return 0;
    }

    let sum = 0;
    let value;

    // Handle different buffer types
    if (buffer instanceof Float32Array) {
      // Float32Array: values already in [-1, 1]
      for (let i = 0; i < buffer.length; i++) {
        value = buffer[i];
        sum += value * value;
      }
    } else if (buffer instanceof Uint8Array) {
      // Uint8Array: convert from [0, 255] to [-1, 1]
      for (let i = 0; i < buffer.length; i++) {
        value = (buffer[i] - 128) / 128;
        sum += value * value;
      }
    } else {
      // Assume array-like with values in [-1, 1]
      for (let i = 0; i < buffer.length; i++) {
        value = buffer[i];
        sum += value * value;
      }
    }

    const rms = Math.sqrt(sum / buffer.length);
    return Math.max(0, Math.min(1, rms)); // Clamp to [0, 1]
  }

  /**
   * Apply smoothing to RMS value for animation
   * @param {number} currentRMS - Current RMS value
   * @returns {number} Smoothed RMS value
   */
  smoothRMS(currentRMS) {
    const smoothed = this.previousRMS * (1 - this.smoothingFactor) + 
                     currentRMS * this.smoothingFactor;
    this.previousRMS = smoothed;
    
    // Add to history
    this.rmsHistory.push(smoothed);
    if (this.rmsHistory.length > this.historySize) {
      this.rmsHistory.shift();
    }
    
    return smoothed;
  }

  /**
   * Get average RMS from history
   * @returns {number} Average RMS value
   */
  getAverageRMS() {
    if (this.rmsHistory.length === 0) {
      return 0;
    }
    const sum = this.rmsHistory.reduce((a, b) => a + b, 0);
    return sum / this.rmsHistory.length;
  }

  /**
   * Map RMS to animation scale
   * @param {number} rms - RMS value
   * @param {number} minScale - Minimum scale (default 0.8)
   * @param {number} maxScale - Maximum scale (default 1.5)
   * @returns {number} Scale value for animation
   */
  rmsToScale(rms, minScale = 0.8, maxScale = 1.5) {
    // Normalize RMS to [0, 1] range
    const normalized = (rms - this.minRMS) / (this.maxRMS - this.minRMS);
    // Map to scale range
    return minScale + (maxScale - minScale) * normalized;
  }

  /**
   * Map RMS to opacity for visual feedback
   * @param {number} rms - RMS value
   * @param {number} minOpacity - Minimum opacity (default 0.3)
   * @param {number} maxOpacity - Maximum opacity (default 1.0)
   * @returns {number} Opacity value
   */
  rmsToOpacity(rms, minOpacity = 0.3, maxOpacity = 1.0) {
    const normalized = (rms - this.minRMS) / (this.maxRMS - this.minRMS);
    return minOpacity + (maxOpacity - minOpacity) * normalized;
  }

  /**
   * Analyze audio buffer and return animation parameters
   * @param {Float32Array|Uint8Array} buffer - Audio buffer
   * @returns {Object} Animation parameters
   */
  analyzeBuffer(buffer) {
    const rawRMS = this.calculateRMS(buffer);
    const smoothedRMS = this.smoothRMS(rawRMS);
    
    return {
      rawRMS,
      smoothedRMS,
      scale: this.rmsToScale(smoothedRMS),
      opacity: this.rmsToOpacity(smoothedRMS),
      averageRMS: this.getAverageRMS(),
      isSilent: smoothedRMS < 0.01,
      isLoud: smoothedRMS > 0.7,
    };
  }

  /**
   * Reset analyzer state
   */
  reset() {
    this.previousRMS = 0;
    this.rmsHistory = [];
  }

  /**
   * Create analyzer with speech-optimized settings
   */
  static createSpeechAnalyzer() {
    return new AudioAnalyzer({
      smoothingFactor: 0.3,    // Good for speech
      minRMS: 0,              // Speech can be very quiet
      maxRMS: 0.7,            // Speech rarely exceeds 0.7 RMS
      historySize: 15,        // ~250ms at 60fps
    });
  }

  /**
   * Create analyzer with music-optimized settings
   */
  static createMusicAnalyzer() {
    return new AudioAnalyzer({
      smoothingFactor: 0.5,    // More responsive for music
      minRMS: 0.1,            // Music usually has a noise floor
      maxRMS: 0.9,            // Music can be louder
      historySize: 30,        // ~500ms at 60fps
    });
  }
}

/**
 * Web Audio API helper for real-time audio analysis
 */
export class WebAudioAnalyzer {
  constructor() {
    this.audioContext = null;
    this.analyser = null;
    this.source = null;
    this.dataArray = null;
    this.audioAnalyzer = AudioAnalyzer.createSpeechAnalyzer();
  }

  /**
   * Initialize Web Audio API analyzer from audio element
   * @param {HTMLAudioElement} audioElement - Audio element
   */
  async initFromAudioElement(audioElement) {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    this.source = this.audioContext.createMediaElementSource(audioElement);
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 2048;
    
    this.source.connect(this.analyser);
    this.analyser.connect(this.audioContext.destination);
    
    const bufferLength = this.analyser.frequencyBinCount;
    this.dataArray = new Uint8Array(bufferLength);
  }

  /**
   * Get current audio analysis
   * @returns {Object} Analysis results
   */
  analyze() {
    if (!this.analyser || !this.dataArray) {
      return this.audioAnalyzer.analyzeBuffer(new Float32Array(0));
    }

    this.analyser.getByteTimeDomainData(this.dataArray);
    return this.audioAnalyzer.analyzeBuffer(this.dataArray);
  }

  /**
   * Clean up resources
   */
  dispose() {
    if (this.source) {
      this.source.disconnect();
    }
    if (this.analyser) {
      this.analyser.disconnect();
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
    this.audioAnalyzer.reset();
  }
}

export default AudioAnalyzer;