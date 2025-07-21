/**
 * Global TTS Manager Service
 * Manages Text-to-Speech functionality and coordinates with the popup widget
 */

import { Audio } from 'expo-av';
import ApiService from './api';
import { AudioAnalyzer } from '../utils/audioAnalyzer';

class TTSManager {
  constructor() {
    this.isInitialized = false;
    this.isPlaying = false;
    this.currentSound = null;
    this.audioAnalyzer = AudioAnalyzer.createSpeechAnalyzer();
    this.rmsCallback = null;
    this.statusCallback = null;
    this.completionCallback = null;
    this.errorCallback = null;
    this.analysisInterval = null;
    this.currentText = '';
    this.currentVoice = 'alloy';
    this.currentSpeed = 1.0;
  }

  /**
   * Initialize the TTS manager
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Configure basic audio session for playback
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      this.isInitialized = true;
      console.log('TTS Manager initialized successfully');
    } catch (error) {
      console.error('Failed to initialize TTS Manager:', error);
      // Don't throw error, just continue without audio mode config
      this.isInitialized = true;
      console.log('TTS Manager initialized with basic configuration');
    }
  }

  /**
   * Set callbacks for TTS events
   */
  setCallbacks({
    onRMS = () => {},
    onStatus = () => {},
    onCompletion = () => {},
    onError = () => {},
  }) {
    this.rmsCallback = onRMS;
    this.statusCallback = onStatus;
    this.completionCallback = onCompletion;
    this.errorCallback = onError;
  }

  /**
   * Start speaking text using OpenAI TTS
   */
  async speak(text, options = {}) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    const {
      voice = 'alloy',
      speed = 1.0,
      model = 'tts-1',
    } = options;

    try {
      // Stop any current playback
      await this.stop();

      this.currentText = text;
      this.currentVoice = voice;
      this.currentSpeed = speed;

      // Notify status callback
      if (this.statusCallback) {
        this.statusCallback({ 
          isPlaying: false, 
          isLoading: true, 
          text: text,
          voice: voice,
          speed: speed 
        });
      }

      console.log('TTS: Generating audio for text:', text.substring(0, 50) + '...');

      // Generate TTS audio - get the response object instead of buffer
      const response = await ApiService.streamTTS(text, {
        voice,
        speed,
        model,
        responseFormat: 'mp3',
      });

      // Get the blob from the response
      const blob = await response.blob();
      
      // Convert blob to base64 data URI for React Native
      const reader = new FileReader();
      const audioUri = await new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });

      // Create and load the sound
      const { sound } = await Audio.Sound.createAsync(
        { uri: audioUri },
        { shouldPlay: true }
      );

      this.currentSound = sound;
      this.isPlaying = true;

      // Start RMS analysis
      this.startRMSAnalysis();

      // Set up playback status updates
      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded) {
          if (status.didJustFinish) {
            this.handlePlaybackComplete();
          } else if (status.error) {
            this.handlePlaybackError(status.error);
          }
        }
      });

      // Notify status callback
      if (this.statusCallback) {
        this.statusCallback({ 
          isPlaying: true, 
          isLoading: false, 
          text: text,
          voice: voice,
          speed: speed 
        });
      }

      console.log('TTS: Audio playback started');

    } catch (error) {
      console.error('TTS: Failed to speak:', error);
      this.handlePlaybackError(error);
    }
  }

  /**
   * Stop current TTS playback
   */
  async stop() {
    try {
      if (this.currentSound) {
        await this.currentSound.stopAsync();
        await this.currentSound.unloadAsync();
        this.currentSound = null;
      }

      this.isPlaying = false;
      this.stopRMSAnalysis();
      this.audioAnalyzer.reset();

      // Notify status callback
      if (this.statusCallback) {
        this.statusCallback({ 
          isPlaying: false, 
          isLoading: false, 
          text: '',
          voice: this.currentVoice,
          speed: this.currentSpeed 
        });
      }

      console.log('TTS: Playback stopped');

    } catch (error) {
      console.error('TTS: Error stopping playback:', error);
    }
  }

  /**
   * Pause current TTS playback
   */
  async pause() {
    try {
      if (this.currentSound && this.isPlaying) {
        await this.currentSound.pauseAsync();
        this.isPlaying = false;
        this.stopRMSAnalysis();

        // Notify status callback
        if (this.statusCallback) {
          this.statusCallback({ 
            isPlaying: false, 
            isLoading: false, 
            text: this.currentText,
            voice: this.currentVoice,
            speed: this.currentSpeed 
          });
        }
      }
    } catch (error) {
      console.error('TTS: Error pausing playback:', error);
    }
  }

  /**
   * Resume paused TTS playback
   */
  async resume() {
    try {
      if (this.currentSound && !this.isPlaying) {
        await this.currentSound.playAsync();
        this.isPlaying = true;
        this.startRMSAnalysis();

        // Notify status callback
        if (this.statusCallback) {
          this.statusCallback({ 
            isPlaying: true, 
            isLoading: false, 
            text: this.currentText,
            voice: this.currentVoice,
            speed: this.currentSpeed 
          });
        }
      }
    } catch (error) {
      console.error('TTS: Error resuming playback:', error);
    }
  }

  /**
   * Start RMS analysis for animation
   */
  startRMSAnalysis() {
    if (this.analysisInterval) {
      clearInterval(this.analysisInterval);
    }

    // Since we can't get real-time audio data from expo-av easily,
    // we'll simulate speech patterns based on the text
    const simulateRMS = () => {
      if (!this.isPlaying) return;

      // Generate realistic speech RMS pattern
      const time = Date.now() / 1000;
      const baseRMS = 0.3;
      const variation = 0.2 * Math.sin(time * 3) + 0.1 * Math.sin(time * 7);
      const rms = Math.max(0, baseRMS + variation);

      // Apply smoothing
      const smoothedRMS = this.audioAnalyzer.smoothRMS(rms);

      // Notify RMS callback
      if (this.rmsCallback) {
        this.rmsCallback(smoothedRMS);
      }
    };

    // Update at ~60fps
    this.analysisInterval = setInterval(simulateRMS, 16);
  }

  /**
   * Stop RMS analysis
   */
  stopRMSAnalysis() {
    if (this.analysisInterval) {
      clearInterval(this.analysisInterval);
      this.analysisInterval = null;
    }

    // Send zero RMS to stop animation
    if (this.rmsCallback) {
      this.rmsCallback(0);
    }
  }

  /**
   * Handle playback completion
   */
  handlePlaybackComplete() {
    this.isPlaying = false;
    this.stopRMSAnalysis();
    this.audioAnalyzer.reset();

    // Notify completion callback
    if (this.completionCallback) {
      this.completionCallback();
    }

    // Notify status callback
    if (this.statusCallback) {
      this.statusCallback({ 
        isPlaying: false, 
        isLoading: false, 
        text: '',
        voice: this.currentVoice,
        speed: this.currentSpeed 
      });
    }

    console.log('TTS: Playback completed');
  }

  /**
   * Handle playback error
   */
  handlePlaybackError(error) {
    this.isPlaying = false;
    this.stopRMSAnalysis();
    this.audioAnalyzer.reset();

    // Notify error callback
    if (this.errorCallback) {
      this.errorCallback(error);
    }

    // Notify status callback
    if (this.statusCallback) {
      this.statusCallback({ 
        isPlaying: false, 
        isLoading: false, 
        text: '',
        voice: this.currentVoice,
        speed: this.currentSpeed,
        error: error.toString() 
      });
    }

    console.error('TTS: Playback error:', error);
  }

  /**
   * Get current playback status
   */
  getStatus() {
    return {
      isPlaying: this.isPlaying,
      isLoading: false,
      text: this.currentText,
      voice: this.currentVoice,
      speed: this.currentSpeed,
    };
  }

  /**
   * Get available voices
   */
  async getVoices() {
    try {
      return await ApiService.getTTSVoices();
    } catch (error) {
      console.error('TTS: Failed to get voices:', error);
      return {
        voices: [
          { id: 'alloy', name: 'Alloy', description: 'Neutral and balanced' },
        ],
        default: 'alloy',
      };
    }
  }

  /**
   * Check TTS service health
   */
  async checkHealth() {
    try {
      return await ApiService.checkTTSHealth();
    } catch (error) {
      console.error('TTS: Health check failed:', error);
      return {
        status: 'error',
        message: error.toString(),
      };
    }
  }

  /**
   * Clean up resources
   */
  async cleanup() {
    await this.stop();
    this.rmsCallback = null;
    this.statusCallback = null;
    this.completionCallback = null;
    this.errorCallback = null;
    this.isInitialized = false;
  }
}

// Export singleton instance
export default new TTSManager();