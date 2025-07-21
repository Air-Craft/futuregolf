// API Service for FutureGolf
// This service handles all API calls to the backend

// Use environment variable for API URL to support device testing
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiService {
  constructor() {
    this.authToken = null;
  }

  setAuthToken(token) {
    this.authToken = token;
  }

  getAuthHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    return headers;
  }

  async uploadVideo(videoUri, viewAngle, clubType) {
    const formData = new FormData();
    formData.append('video', {
      uri: videoUri,
      type: 'video/mp4',
      name: `swing_${Date.now()}.mp4`,
    });
    formData.append('view_angle', viewAngle);
    formData.append('club_type', clubType);

    const response = await fetch(`${API_BASE_URL}/videos/upload`, {
      method: 'POST',
      body: formData,
      headers: {
        ...this.getAuthHeaders(),
        'Content-Type': 'multipart/form-data',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to upload video');
    }

    return response.json();
  }

  async startAnalysis(videoId) {
    const response = await fetch(`${API_BASE_URL}/video-analysis/analyze/${videoId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to start analysis');
    }

    return response.json();
  }

  async getAnalysisStatus(videoId) {
    const response = await fetch(`${API_BASE_URL}/video-analysis/video/${videoId}`, {
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to get analysis status');
    }

    return response.json();
  }

  async getUserAnalyses() {
    const response = await fetch(`${API_BASE_URL}/video-analysis/user/analyses`, {
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to get user analyses');
    }

    return response.json();
  }

  async pollAnalysis(videoId, maxAttempts = 60, interval = 2000) {
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      const data = await this.getAnalysisStatus(videoId);
      
      if (data.analysis && data.analysis.status === 'completed') {
        return data.analysis;
      } else if (data.analysis && data.analysis.status === 'failed') {
        throw new Error(data.analysis.error_message || 'Analysis failed');
      }
      
      await new Promise(resolve => setTimeout(resolve, interval));
      attempts++;
    }
    
    throw new Error('Analysis timeout - please try again');
  }

  // TTS Methods
  async streamTTS(text, options = {}) {
    const {
      voice = 'alloy',
      model = 'tts-1',
      speed = 1.0,
      responseFormat = 'mp3',
      onAudioData = () => {},
      onError = () => {},
      onComplete = () => {},
    } = options;

    try {
      const response = await fetch(`${API_BASE_URL}/tts/stream`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          text,
          voice,
          model,
          speed,
          response_format: responseFormat,
        }),
      });

      if (!response.ok) {
        throw new Error(`TTS stream failed: ${response.status}`);
      }

      return response;
    } catch (error) {
      onError(error);
      throw error;
    }
  }

  async generateTTS(text, options = {}) {
    const {
      voice = 'alloy',
      model = 'tts-1',
      speed = 1.0,
      responseFormat = 'mp3',
    } = options;

    try {
      const response = await fetch(`${API_BASE_URL}/tts/generate`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          text,
          voice,
          model,
          speed,
          response_format: responseFormat,
        }),
      });

      if (!response.ok) {
        throw new Error(`TTS generation failed: ${response.status}`);
      }

      return response.arrayBuffer();
    } catch (error) {
      throw error;
    }
  }

  async getTTSVoices() {
    try {
      const response = await fetch(`${API_BASE_URL}/tts/voices`, {
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to get TTS voices');
      }

      return response.json();
    } catch (error) {
      throw error;
    }
  }

  async checkTTSHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/tts/health`, {
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('TTS health check failed');
      }

      return response.json();
    } catch (error) {
      throw error;
    }
  }
}

export default new ApiService();