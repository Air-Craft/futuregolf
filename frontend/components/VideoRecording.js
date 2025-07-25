import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Modal,
  Dimensions,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Video } from 'expo-av';
import * as MediaLibrary from 'expo-media-library';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import SwingReview from './SwingReview';
import api from '../services/api';

const { width, height } = Dimensions.get('window');

export default function VideoRecording({ navigation }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [cameraType, setCameraType] = useState('back');
  const [isRecording, setIsRecording] = useState(false);
  const [recordedVideo, setRecordedVideo] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState('');
  
  const cameraRef = useRef(null);
  const recordingTimerRef = useRef(null);

  useEffect(() => {
    requestMediaLibraryPermission();
  }, []);

  const requestMediaLibraryPermission = async () => {
    try {
      await MediaLibrary.requestPermissionsAsync();
    } catch (error) {
      console.error('Error requesting media library permissions:', error);
    }
  };

  const startRecording = async () => {
    if (!cameraRef.current) return;
    
    try {
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start recording timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      const video = await cameraRef.current.recordAsync({
        maxDuration: 30, // 30 seconds max for golf swing
        mute: false,
      });
      
      setRecordedVideo({ ...video, wasRecorded: true });
      
    } catch (error) {
      console.error('Error starting recording:', error);
      Alert.alert('Recording Error', 'Failed to start recording. Please try again.');
    }
  };

  const stopRecording = async () => {
    if (!cameraRef.current) return;
    
    try {
      setIsRecording(false);
      clearInterval(recordingTimerRef.current);
      
      await cameraRef.current.stopRecording();
      setShowPreview(true); // Show preview after recording
      
    } catch (error) {
      console.error('Error stopping recording:', error);
      Alert.alert('Recording Error', 'Failed to stop recording.');
    }
  };

  const toggleCamera = () => {
    setCameraType(current => current === 'back' ? 'front' : 'back');
  };

  const pickVideoFromLibrary = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        allowsEditing: false,
        quality: 1,
      });

      if (!result.canceled && result.assets[0]) {
        const videoAsset = result.assets[0];
        setRecordedVideo({
          uri: videoAsset.uri,
          width: videoAsset.width,
          height: videoAsset.height,
          duration: videoAsset.duration,
          wasRecorded: false, // This was picked from library, not recorded
        });
        setShowPreview(true);
      }
    } catch (error) {
      console.error('Error picking video:', error);
      Alert.alert('Error', 'Failed to pick video from library');
    }
  };

  const uploadVideoForAnalysis = async (videoUri) => {
    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', {
        uri: videoUri,
        type: 'video/mp4',
        name: `swing_${Date.now()}.mp4`,
      });
      formData.append('title', `Golf Swing - ${new Date().toLocaleDateString()}`);
      formData.append('description', `${cameraType === 'back' ? 'Down-the-line' : 'Front'} view with driver`);
      formData.append('user_id', '1'); // TODO: Get from auth context when implemented
      
      // Upload video to backend
      const apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
      console.log('Uploading to:', `${apiBaseUrl}/videos/upload`);
      
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000); // 60 second timeout
      
      const uploadResponse = await fetch(`${apiBaseUrl}/videos/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type for FormData - let browser set it with boundary
          // Add authentication token when implemented
          // 'Authorization': `Bearer ${authToken}`,
        },
        signal: controller.signal,
      }).finally(() => clearTimeout(timeout));
      
      const responseText = await uploadResponse.text();
      console.log('Upload response:', uploadResponse.status, responseText);
      
      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.status} - ${responseText}`);
      }
      
      const uploadData = JSON.parse(responseText);
      return uploadData.video_id || uploadData.id;
      
    } catch (error) {
      console.error('Error uploading video:', error);
      throw error;
    }
  };

  const startVideoAnalysis = async (videoId) => {
    try {
      return await api.startAnalysis(videoId);
    } catch (error) {
      console.error('Error starting analysis:', error);
      throw error;
    }
  };

  const pollAnalysisStatus = async (videoId) => {
    try {
      return await api.pollAnalysis(videoId, 60, 2000, (status) => {
        setAnalysisStatus(status);
      });
    } catch (error) {
      console.error('Error polling analysis:', error);
      throw error;
    }
  };

  const saveVideo = async () => {
    if (!recordedVideo) return;
    
    try {
      setIsLoading(true);
      
      // Only save to device gallery if it was recorded (not picked from library)
      if (recordedVideo.wasRecorded) {
        const asset = await MediaLibrary.createAssetAsync(recordedVideo.uri);
        console.log('Saved recorded video to gallery');
      }
      
      // Upload video and start analysis
      setShowPreview(false);
      setIsAnalyzing(true);
      setShowAnalysis(true);
      
      // Upload video and start analysis
      setAnalysisStatus('Uploading video...');
      console.log('Uploading video for analysis...');
      const videoId = await uploadVideoForAnalysis(recordedVideo.uri);
      console.log('Video uploaded, ID:', videoId);
      
      setAnalysisStatus('Starting analysis...');
      await startVideoAnalysis(videoId);
      console.log('Analysis started, polling for results...');
      
      setAnalysisStatus('Analyzing swing...');
      const analysisResult = await pollAnalysisStatus(videoId);
      console.log('Analysis complete:', analysisResult);
      
      // Set the real analysis data
      setAnalysisData(analysisResult);
      setIsAnalyzing(false);
      setAnalysisStatus('');
      
      /* Mock analysis data for testing - REMOVED
      // Mock data removed - using real API now
      */
      
    } catch (error) {
      console.error('Error processing video:', error);
      const errorMessage = error.message || 'Failed to process video. Please try again.';
      Alert.alert('Upload Error', errorMessage);
      setIsAnalyzing(false);
      setShowAnalysis(false);
      setShowPreview(false);
      setRecordedVideo(null);
    } finally {
      setIsLoading(false);
    }
  };

  const retakeVideo = () => {
    setRecordedVideo(null);
    setShowPreview(false);
    setRecordingTime(0);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!permission) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>Requesting camera permissions...</Text>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>Camera permission denied</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Request Permissions</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Camera View */}
      <CameraView
        style={styles.camera}
        facing={cameraType}
        ref={cameraRef}
        mode="video"
      >
        {/* Recording Timer */}
        {isRecording && (
          <View style={styles.timerContainer}>
            <View style={styles.recordingDot} />
            <Text style={styles.timerText}>{formatTime(recordingTime)}</Text>
          </View>
        )}
        
        {/* Camera Type Indicator */}
        <View style={styles.cameraTypeContainer}>
          <Text style={styles.cameraTypeText}>
            {cameraType === 'back' ? 'Down-the-line' : 'Front view'}
          </Text>
        </View>
        
        {/* Controls */}
        <View style={styles.controlsContainer}>
          {/* Camera Toggle */}
          <View style={styles.controlWrapper}>
            <TouchableOpacity style={styles.controlButton} onPress={toggleCamera}>
              <Ionicons name="camera-reverse" size={30} color="white" />
            </TouchableOpacity>
            <Text style={styles.controlLabel}>Flip</Text>
          </View>
          
          {/* Record Button */}
          <View style={styles.controlWrapper}>
            <TouchableOpacity
              style={[styles.recordButton, isRecording && styles.recordButtonActive]}
              onPress={isRecording ? stopRecording : startRecording}
            >
              <View style={[styles.recordButtonInner, isRecording && styles.recordButtonInnerActive]} />
            </TouchableOpacity>
            <Text style={styles.controlLabel}>{isRecording ? 'Stop' : 'Record'}</Text>
          </View>
          
          {/* Upload Button */}
          <View style={styles.controlWrapper}>
            <TouchableOpacity style={styles.controlButton} onPress={pickVideoFromLibrary}>
              <Ionicons name="folder-open" size={30} color="white" />
            </TouchableOpacity>
            <Text style={styles.controlLabel}>Upload</Text>
          </View>
        </View>
      </CameraView>

      {/* Video Preview Modal */}
      <Modal
        visible={showPreview}
        animationType="slide"
        onRequestClose={() => setShowPreview(false)}
      >
        <View style={styles.previewContainer}>
          <Text style={styles.previewTitle}>Golf Swing Preview</Text>
          
          {recordedVideo && (
            <Video
              source={{ uri: recordedVideo.uri }}
              style={styles.previewVideo}
              useNativeControls
              resizeMode="contain"
              shouldPlay={false}
            />
          )}
          
          <View style={styles.previewControls}>
            <TouchableOpacity style={styles.previewButton} onPress={retakeVideo}>
              <Text style={styles.previewButtonText}>Retake</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.previewButton, styles.saveButton]} 
              onPress={() => {
                saveVideo().catch(error => {
                  console.error('Unhandled error in saveVideo:', error);
                  Alert.alert('Error', 'An unexpected error occurred. Please try again.');
                });
              }}
              disabled={isLoading}
            >
              <Text style={styles.previewButtonText}>
                {isLoading ? 'Saving...' : 'Save & Analyze'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      
      {/* Preview is now shown in stopRecording() and pickVideoFromLibrary() */}

      {/* Swing Review Modal */}
      <Modal
        visible={showAnalysis}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={() => {
          setShowAnalysis(false);
          setAnalysisData(null);
          setRecordedVideo(null);
        }}
      >
        <SwingReview
          videoUri={recordedVideo?.uri}
          analysisData={analysisData}
          isAnalyzing={isAnalyzing}
          analysisStatus={analysisStatus}
          onClose={() => {
            setShowAnalysis(false);
            setAnalysisData(null);
            setRecordedVideo(null);
          }}
        />
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  message: {
    color: '#fff',
    fontSize: 18,
    textAlign: 'center',
    margin: 20,
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 5,
    margin: 20,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
  },
  timerContainer: {
    position: 'absolute',
    top: 60,
    left: 20,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  recordingDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#ff0000',
    marginRight: 8,
  },
  timerText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  cameraTypeContainer: {
    position: 'absolute',
    top: 60,
    right: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  cameraTypeText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  controlsContainer: {
    position: 'absolute',
    bottom: 50,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  controlWrapper: {
    alignItems: 'center',
  },
  controlLabel: {
    color: 'white',
    fontSize: 12,
    marginTop: 5,
    fontWeight: '500',
  },
  controlButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#fff',
  },
  recordButtonActive: {
    borderColor: '#ff0000',
  },
  recordButtonInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#ff0000',
  },
  recordButtonInnerActive: {
    borderRadius: 8,
    width: 40,
    height: 40,
  },
  previewContainer: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  previewTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 20,
    marginTop: 50,
  },
  previewVideo: {
    width: width * 0.9,
    height: height * 0.6,
  },
  previewControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    paddingHorizontal: 40,
    marginTop: 40,
  },
  previewButton: {
    backgroundColor: '#666',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
    minWidth: 120,
  },
  saveButton: {
    backgroundColor: '#007AFF',
  },
  previewButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
});