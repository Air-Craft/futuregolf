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
import { Ionicons } from '@expo/vector-icons';
import SwingReview from './SwingReview';

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
      
      setRecordedVideo(video);
      
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
      
    } catch (error) {
      console.error('Error stopping recording:', error);
      Alert.alert('Recording Error', 'Failed to stop recording.');
    }
  };

  const toggleCamera = () => {
    setCameraType(current => current === 'back' ? 'front' : 'back');
  };

  const uploadVideoForAnalysis = async (videoUri) => {
    try {
      // Create form data
      const formData = new FormData();
      formData.append('video', {
        uri: videoUri,
        type: 'video/mp4',
        name: `swing_${Date.now()}.mp4`,
      });
      formData.append('view_angle', cameraType === 'back' ? 'down_the_line' : 'front');
      formData.append('club_type', 'driver'); // Default to driver, can be made selectable
      
      // Upload video to backend
      const uploadResponse = await fetch('http://localhost:8000/api/v1/videos/upload', {
        method: 'POST',
        body: formData,
        headers: {
          // Add authentication token when implemented
          // 'Authorization': `Bearer ${authToken}`,
        },
      });
      
      if (!uploadResponse.ok) {
        throw new Error('Failed to upload video');
      }
      
      const uploadData = await uploadResponse.json();
      return uploadData.video_id;
      
    } catch (error) {
      console.error('Error uploading video:', error);
      throw error;
    }
  };

  const startVideoAnalysis = async (videoId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/video-analysis/analyze/${videoId}`, {
        method: 'POST',
        headers: {
          // Add authentication token when implemented
          // 'Authorization': `Bearer ${authToken}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to start analysis');
      }
      
      const data = await response.json();
      return data;
      
    } catch (error) {
      console.error('Error starting analysis:', error);
      throw error;
    }
  };

  const pollAnalysisStatus = async (videoId) => {
    const maxAttempts = 60; // 60 attempts at 2 seconds = 2 minutes max
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/video-analysis/video/${videoId}`, {
          headers: {
            // Add authentication token when implemented
            // 'Authorization': `Bearer ${authToken}`,
          },
        });
        
        if (!response.ok) {
          throw new Error('Failed to get analysis status');
        }
        
        const data = await response.json();
        
        if (data.analysis && data.analysis.status === 'completed') {
          return data.analysis;
        } else if (data.analysis && data.analysis.status === 'failed') {
          throw new Error(data.analysis.error_message || 'Analysis failed');
        }
        
        // Wait 2 seconds before next poll
        await new Promise(resolve => setTimeout(resolve, 2000));
        attempts++;
        
      } catch (error) {
        console.error('Error polling analysis:', error);
        throw error;
      }
    }
    
    throw new Error('Analysis timeout - please try again');
  };

  const saveVideo = async () => {
    if (!recordedVideo) return;
    
    try {
      setIsLoading(true);
      
      // Save to device gallery
      const asset = await MediaLibrary.createAssetAsync(recordedVideo.uri);
      
      // Upload video and start analysis
      setShowPreview(false);
      setIsAnalyzing(true);
      setShowAnalysis(true);
      
      // Mock analysis for development - replace with actual API calls
      // const videoId = await uploadVideoForAnalysis(recordedVideo.uri);
      // await startVideoAnalysis(videoId);
      // const analysisResult = await pollAnalysisStatus(videoId);
      
      // Mock analysis data for testing
      setTimeout(() => {
        setAnalysisData({
          ai_analysis: {
            overall_score: 78,
            coaching_feedback: "Great swing! Your setup position is solid with good posture and alignment. During the backswing, you maintain excellent spine angle and achieve a full shoulder turn. The transition from backswing to downswing is smooth, showing good tempo. At impact, your weight has transferred nicely to the front foot. To improve further, focus on maintaining your spine angle through impact - you tend to stand up slightly. Also, work on keeping your head steady throughout the swing for better consistency. Practice these adjustments with slow-motion swings to build muscle memory.",
            swing_metrics: {
              clubSpeed: "95",
              swingPlane: "48",
              tempoRatio: "3:1",
              impactPosition: "Centered"
            },
            body_angles: {
              spineAngle: "32",
              hipRotation: "45",
              shoulderTurn: "92"
            },
            recommendations: [
              {
                title: "Maintain Spine Angle",
                description: "Focus on keeping your spine angle consistent through impact to improve ball striking",
                priority: "high"
              },
              {
                title: "Head Position",
                description: "Keep your head steady and behind the ball at impact",
                priority: "medium"
              }
            ],
            timestamps: [
              { time: "0:02", label: "Setup" },
              { time: "0:04", label: "Backswing" },
              { time: "0:06", label: "Impact" },
              { time: "0:08", label: "Follow-through" }
            ]
          }
        });
        setIsAnalyzing(false);
      }, 3000);
      
    } catch (error) {
      console.error('Error processing video:', error);
      Alert.alert('Error', 'Failed to process video. Please try again.');
      setIsAnalyzing(false);
      setShowAnalysis(false);
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
          <TouchableOpacity style={styles.controlButton} onPress={toggleCamera}>
            <Ionicons name="camera-reverse" size={30} color="white" />
          </TouchableOpacity>
          
          {/* Record Button */}
          <TouchableOpacity
            style={[styles.recordButton, isRecording && styles.recordButtonActive]}
            onPress={isRecording ? stopRecording : startRecording}
          >
            <View style={[styles.recordButtonInner, isRecording && styles.recordButtonInnerActive]} />
          </TouchableOpacity>
          
          {/* Placeholder for alignment */}
          <View style={styles.controlButton} />
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
              onPress={saveVideo}
              disabled={isLoading}
            >
              <Text style={styles.previewButtonText}>
                {isLoading ? 'Saving...' : 'Save & Analyze'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      
      {/* Show preview when recording is complete */}
      {recordedVideo && !showPreview && (
        setShowPreview(true)
      )}

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