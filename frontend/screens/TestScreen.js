import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import CoachingDisplay from '../components/CoachingDisplay';
import SwingReview from '../components/SwingReview';
import ttsManager from '../services/ttsManager';

export default function TestScreen() {
  const [showCoaching, setShowCoaching] = useState(false);
  const [showSwingReview, setShowSwingReview] = useState(false);

  const mockCoachingScript = `Great swing! Your setup position is solid with good posture and alignment. During the backswing, you maintain excellent spine angle and achieve a full shoulder turn. The transition from backswing to downswing is smooth, showing good tempo. At impact, your weight has transferred nicely to the front foot.

To improve further, focus on maintaining your spine angle through impact - you tend to stand up slightly. Also, work on keeping your head steady throughout the swing for better consistency. Practice these adjustments with slow-motion swings to build muscle memory.

Remember to keep your grip pressure light and consistent throughout the swing. This will help you maintain control while generating more clubhead speed.`;

  const mockAnalysisData = {
    ai_analysis: {
      overall_score: 78,
      coaching_feedback: mockCoachingScript,
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
  };

  const mockTimestamps = [
    { time: "0:02", label: "Setup" },
    { time: "0:04", label: "Backswing" },
    { time: "0:06", label: "Impact" },
    { time: "0:08", label: "Follow-through" }
  ];

  const testTTSWidget = async () => {
    try {
      const testText = "Welcome to FutureGolf! This is a test of the TTS popup widget. You should see an animated pulse circle that moves with the speech rhythm. The widget appears over any background and provides a smooth, synchronized experience.";
      
      console.log('Testing TTS Widget with text:', testText);
      await ttsManager.speak(testText, {
        voice: 'alloy',
        speed: 1.0,
        model: 'tts-1',
      });
    } catch (error) {
      console.error('TTS Widget test failed:', error);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Component Test</Text>
        <Text style={styles.subtitle}>Test the new coaching and swing review components</Text>
      </View>

      <View style={styles.content}>
        <TouchableOpacity 
          style={styles.testButton}
          onPress={() => setShowCoaching(true)}
        >
          <Ionicons name="school" size={24} color="#007AFF" />
          <Text style={styles.testButtonText}>Test Coaching Display</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.testButton}
          onPress={() => setShowSwingReview(true)}
        >
          <Ionicons name="analytics" size={24} color="#007AFF" />
          <Text style={styles.testButtonText}>Test Swing Review</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.testButton}
          onPress={() => testTTSWidget()}
        >
          <Ionicons name="volume-high" size={24} color="#007AFF" />
          <Text style={styles.testButtonText}>Test TTS Widget</Text>
        </TouchableOpacity>
      </View>

      {/* Coaching Display Modal */}
      <Modal
        visible={showCoaching}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={() => setShowCoaching(false)}
      >
        <View style={styles.modalContainer}>
          <TouchableOpacity 
            style={styles.closeButton}
            onPress={() => setShowCoaching(false)}
          >
            <Ionicons name="close" size={28} color="#1C1C1E" />
          </TouchableOpacity>
          
          <CoachingDisplay
            coachingScript={mockCoachingScript}
            timestamps={mockTimestamps}
            onTimestampPress={(timestamp) => console.log('Timestamp pressed:', timestamp)}
          />
        </View>
      </Modal>

      {/* Swing Review Modal */}
      <Modal
        visible={showSwingReview}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={() => setShowSwingReview(false)}
      >
        <SwingReview
          videoUri={null}
          analysisData={mockAnalysisData}
          isAnalyzing={false}
          onClose={() => setShowSwingReview(false)}
        />
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    backgroundColor: '#007AFF',
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#B3D4FF',
    textAlign: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  testButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  testButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginLeft: 16,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  closeButton: {
    position: 'absolute',
    top: 50,
    right: 20,
    zIndex: 1000,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 20,
    padding: 8,
  },
});