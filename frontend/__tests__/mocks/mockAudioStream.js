/**
 * Mock Audio Stream Generator for Testing TTS Widget
 * Provides various audio patterns with known RMS values for testing
 */

export class MockAudioStream {
  constructor() {
    this.isStreaming = false;
    this.currentPattern = 'speech';
    this.sampleRate = 44100;
    this.rmsCallback = null;
    this.audioCallback = null;
    this.frameSize = 1024;
    this.currentFrame = 0;
  }

  // Generate different audio patterns
  static patterns = {
    // Silence
    silence: () => 0,
    
    // Quiet speech (RMS ~0.2)
    quiet: (t) => 0.2 * Math.sin(2 * Math.PI * 440 * t),
    
    // Normal speech (RMS varies 0.1-0.6)
    speech: (t) => {
      const envelope = 0.3 + 0.3 * Math.sin(2 * Math.PI * 2 * t); // 2Hz modulation
      return envelope * Math.sin(2 * Math.PI * 440 * t);
    },
    
    // Loud speech (RMS ~0.8)
    loud: (t) => 0.8 * Math.sin(2 * Math.PI * 440 * t),
    
    // Natural speech pattern (realistic envelope)
    natural: (t) => {
      const word = Math.floor(t * 3) % 4; // 3 words per second
      const wordEnvelope = Math.sin(Math.PI * ((t * 3) % 1)); // Word envelope
      const amplitude = [0.2, 0.5, 0.3, 0.6][word]; // Different word amplitudes
      return amplitude * wordEnvelope * Math.sin(2 * Math.PI * 440 * t);
    },
    
    // Music pattern (consistent RMS ~0.5)
    music: (t) => 0.5 * Math.sin(2 * Math.PI * 440 * t) * Math.sin(2 * Math.PI * 3 * t),
  };

  // Set the audio pattern to use
  setPattern(patternName) {
    if (MockAudioStream.patterns[patternName]) {
      this.currentPattern = patternName;
    }
  }

  // Generate audio buffer for current pattern
  generateAudioBuffer() {
    const buffer = new Float32Array(this.frameSize);
    const pattern = MockAudioStream.patterns[this.currentPattern];
    
    for (let i = 0; i < this.frameSize; i++) {
      const t = (this.currentFrame * this.frameSize + i) / this.sampleRate;
      buffer[i] = pattern(t);
    }
    
    this.currentFrame++;
    return buffer;
  }

  // Calculate RMS of audio buffer
  calculateRMS(buffer) {
    let sum = 0;
    for (let i = 0; i < buffer.length; i++) {
      sum += buffer[i] * buffer[i];
    }
    return Math.sqrt(sum / buffer.length);
  }

  // Start streaming mock audio
  startStream(options = {}) {
    const {
      onRMS = () => {},
      onAudioData = () => {},
      updateInterval = 1000 / 60, // 60fps
    } = options;

    this.rmsCallback = onRMS;
    this.audioCallback = onAudioData;
    this.isStreaming = true;
    this.currentFrame = 0;

    this.streamInterval = setInterval(() => {
      if (!this.isStreaming) {
        clearInterval(this.streamInterval);
        return;
      }

      const audioBuffer = this.generateAudioBuffer();
      const rms = this.calculateRMS(audioBuffer);

      // Call callbacks
      if (this.audioCallback) {
        this.audioCallback(audioBuffer);
      }
      if (this.rmsCallback) {
        this.rmsCallback(rms);
      }
    }, updateInterval);
  }

  // Stop streaming
  stopStream() {
    this.isStreaming = false;
    if (this.streamInterval) {
      clearInterval(this.streamInterval);
    }
  }

  // Get test RMS values for different patterns
  static getTestRMSValues() {
    return {
      silence: 0,
      quiet: 0.141, // RMS of 0.2 amplitude sine wave
      speech: 0.212, // Average RMS of modulated speech
      loud: 0.566, // RMS of 0.8 amplitude sine wave
      natural: 0.283, // Average RMS of natural pattern
      music: 0.25, // RMS of music pattern
    };
  }

  // Generate a sequence of RMS values for testing animations
  static generateRMSSequence(pattern, duration = 1000, fps = 60) {
    const stream = new MockAudioStream();
    stream.setPattern(pattern);
    const sequence = [];
    const frames = Math.floor(duration * fps / 1000);

    for (let i = 0; i < frames; i++) {
      const buffer = stream.generateAudioBuffer();
      const rms = stream.calculateRMS(buffer);
      sequence.push({
        time: i * (1000 / fps),
        rms: rms,
      });
    }

    return sequence;
  }
}

// Helper function to create mock audio blob for testing
export function createMockAudioBlob(pattern = 'speech', duration = 3000) {
  const sampleRate = 44100;
  const samples = sampleRate * duration / 1000;
  const buffer = new Float32Array(samples);
  const patternFn = MockAudioStream.patterns[pattern];

  for (let i = 0; i < samples; i++) {
    const t = i / sampleRate;
    buffer[i] = patternFn(t);
  }

  // Convert to WAV format
  const wavBuffer = float32ArrayToWav(buffer, sampleRate);
  return new Blob([wavBuffer], { type: 'audio/wav' });
}

// Convert Float32Array to WAV format
function float32ArrayToWav(buffer, sampleRate) {
  const length = buffer.length;
  const arrayBuffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(arrayBuffer);

  // WAV header
  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, length * 2, true);

  // Convert float samples to 16-bit PCM
  let offset = 44;
  for (let i = 0; i < length; i++) {
    const sample = Math.max(-1, Math.min(1, buffer[i]));
    view.setInt16(offset, sample * 0x7FFF, true);
    offset += 2;
  }

  return arrayBuffer;
}

export default MockAudioStream;