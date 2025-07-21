import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import ttsManager from '../services/ttsManager';

const { width } = Dimensions.get('window');

export default function CoachingDisplay({ 
  coachingScript, 
  timestamps = [], 
  onTimestampPress,
  isLoading = false 
}) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechRate, setSpeechRate] = useState(1.0);
  const [ttsLoading, setTTSLoading] = useState(false);
  const scrollViewRef = useRef(null);

  useEffect(() => {
    return () => {
      // Cleanup: stop TTS when component unmounts
      ttsManager.stop();
    };
  }, []);

  const toggleSpeech = async () => {
    console.log('TTS: toggleSpeech called, isSpeaking:', isSpeaking);
    
    if (isSpeaking) {
      console.log('TTS: Stopping speech');
      await ttsManager.stop();
      setIsSpeaking(false);
      setTTSLoading(false);
    } else {
      console.log('TTS: Starting speech with text:', coachingScript?.substring(0, 50) + '...');
      
      if (!coachingScript) {
        console.warn('TTS: No coaching script available');
        return;
      }
      
      try {
        setTTSLoading(true);
        setIsSpeaking(true);
        
        await ttsManager.speak(coachingScript, {
          voice: 'alloy',
          speed: speechRate,
          model: 'tts-1',
        });
        
        setTTSLoading(false);
        console.log('TTS: Speech started successfully');
      } catch (error) {
        console.error('TTS: Failed to start speech:', error);
        setIsSpeaking(false);
        setTTSLoading(false);
      }
    }
  };


  const adjustSpeechRate = (delta) => {
    const newRate = Math.max(0.5, Math.min(2.0, speechRate + delta));
    setSpeechRate(newRate);
  };

  const renderTimestamp = (timestamp, index) => (
    <TouchableOpacity
      key={index}
      style={styles.timestampButton}
      onPress={() => onTimestampPress && onTimestampPress(timestamp.time)}
    >
      <Ionicons name="time-outline" size={16} color="#007AFF" />
      <Text style={styles.timestampText}>{timestamp.label || timestamp.time}</Text>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Analyzing your swing...</Text>
      </View>
    );
  }

  if (!coachingScript) {
    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="golf-outline" size={60} color="#C7C7CC" />
        <Text style={styles.emptyText}>No coaching feedback available</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header with controls */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI Coach Feedback</Text>
        
        {/* Speech Controls */}
        <View style={styles.speechControls}>
          <TouchableOpacity 
            style={styles.speedButton} 
            onPress={() => adjustSpeechRate(-0.25)}
          >
            <Ionicons name="remove-circle-outline" size={24} color="#007AFF" />
          </TouchableOpacity>
          
          <Text style={styles.speedText}>{speechRate.toFixed(2)}x</Text>
          
          <TouchableOpacity 
            style={styles.speedButton} 
            onPress={() => adjustSpeechRate(0.25)}
          >
            <Ionicons name="add-circle-outline" size={24} color="#007AFF" />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.playButton, (isSpeaking || ttsLoading) && styles.playButtonActive]}
            onPress={toggleSpeech}
            disabled={ttsLoading}
          >
            {ttsLoading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Ionicons 
                name={isSpeaking ? "pause" : "play"} 
                size={24} 
                color="#fff" 
              />
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Timestamps */}
      {timestamps.length > 0 && (
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          style={styles.timestampsContainer}
        >
          {timestamps.map(renderTimestamp)}
        </ScrollView>
      )}

      {/* Coaching Script */}
      <ScrollView 
        ref={scrollViewRef}
        style={styles.scriptContainer}
        showsVerticalScrollIndicator={true}
      >
        <View style={styles.scriptContent}>
          <Text style={styles.scriptText}>
            {coachingScript || 'No coaching feedback available'}
          </Text>
        </View>
      </ScrollView>

      {/* Professional Golf Tips Section */}
      <View style={styles.tipsContainer}>
        <View style={styles.tipHeader}>
          <Ionicons name="bulb-outline" size={20} color="#34C759" />
          <Text style={styles.tipTitle}>Pro Tip</Text>
        </View>
        <Text style={styles.tipText}>
          Focus on maintaining a steady head position throughout your swing for improved consistency.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
  },
  emptyText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 3,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  speechControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  speedButton: {
    padding: 8,
  },
  speedText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginHorizontal: 8,
    minWidth: 50,
    textAlign: 'center',
  },
  playButton: {
    backgroundColor: '#007AFF',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 16,
  },
  playButtonActive: {
    backgroundColor: '#FF3B30',
  },
  timestampsContainer: {
    backgroundColor: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 20,
    maxHeight: 60,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  timestampButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
  },
  timestampText: {
    fontSize: 14,
    color: '#007AFF',
    marginLeft: 4,
  },
  scriptContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scriptContent: {
    padding: 20,
  },
  scriptText: {
    fontSize: 16,
    lineHeight: 26,
    color: '#1C1C1E',
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  },
  highlightedText: {
    backgroundColor: '#FFF3CD',
    borderRadius: 4,
  },
  tipsContainer: {
    backgroundColor: '#E8F5E9',
    margin: 20,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#34C759',
  },
  tipHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  tipTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#34C759',
    marginLeft: 8,
  },
  tipText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#2E7D32',
  },
});