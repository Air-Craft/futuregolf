import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  Dimensions,
  Platform,
} from 'react-native';
import { BlurView } from 'expo-blur';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export default function TTSPopupWidget({
  isVisible = false,
  text = '',
  rmsValue = 0,
  showAction = false,
  actionText = '',
  onAction = () => {},
}) {
  // Animation values
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const pulseAnim = useRef(new Animated.Value(0.8)).current;
  const actionFadeAnim = useRef(new Animated.Value(0)).current;

  // State
  const [isRendered, setIsRendered] = useState(false);

  // Handle visibility animation
  useEffect(() => {
    if (isVisible) {
      setIsRendered(true);
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    } else {
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }).start(() => {
        setIsRendered(false);
      });
    }
  }, [isVisible]);

  // Handle RMS-based pulse animation
  useEffect(() => {
    if (isVisible && !showAction) {
      // Map RMS (0-1) to scale (0.8-1.5)
      const targetScale = 0.8 + (rmsValue * 0.7);
      
      Animated.timing(pulseAnim, {
        toValue: targetScale,
        duration: 50, // Fast response for real-time feel
        useNativeDriver: true,
      }).start();
    }
  }, [rmsValue, isVisible, showAction]);

  // Handle cross-fade between pulse and action
  useEffect(() => {
    if (showAction) {
      // Fade out pulse, fade in action
      Animated.parallel([
        Animated.timing(scaleAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(actionFadeAnim, {
          toValue: 1,
          duration: 200,
          delay: 100,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      // Fade in pulse, fade out action
      Animated.parallel([
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(actionFadeAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [showAction]);

  if (!isRendered) {
    return null;
  }

  return (
    <Animated.View 
      style={[styles.container, { opacity: fadeAnim }]}
      testID="tts-popup-widget"
    >
      <BlurView intensity={80} style={styles.blurContainer}>
        <View style={styles.content}>
          {/* Pulse Circle */}
          {!showAction && (
            <Animated.View
              testID="tts-pulse-circle"
              style={[
                styles.pulseCircle,
                {
                  opacity: scaleAnim,
                  transform: [
                    { scale: Animated.multiply(pulseAnim, scaleAnim) }
                  ],
                },
              ]}
            >
              {/* Inner circle for visual depth */}
              <View style={styles.innerCircle} />
              
              {/* Outer ring pulses */}
              <Animated.View 
                style={[
                  styles.outerRing,
                  {
                    transform: [
                      { scale: Animated.add(pulseAnim, 0.2) }
                    ],
                    opacity: Animated.subtract(1.5, pulseAnim),
                  }
                ]}
              />
            </Animated.View>
          )}

          {/* Text Display */}
          <Text 
            testID="tts-text-display"
            style={[
              styles.text,
              showAction && styles.actionText
            ]}
            numberOfLines={3}
            adjustsFontSizeToFit
          >
            {text}
          </Text>

          {/* Action Button */}
          {showAction && (
            <Animated.View
              style={{ opacity: actionFadeAnim }}
            >
              <TouchableOpacity
                testID="tts-action-button"
                style={styles.actionButton}
                onPress={onAction}
                activeOpacity={0.8}
              >
                <Text style={styles.actionButtonText}>{actionText}</Text>
              </TouchableOpacity>
            </Animated.View>
          )}
        </View>
      </BlurView>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 100,
    left: 20,
    right: 20,
    zIndex: 9999,
    elevation: 10,
  },
  blurContainer: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: Platform.OS === 'android' ? 'rgba(255, 255, 255, 0.9)' : undefined,
  },
  content: {
    padding: 24,
    alignItems: 'center',
  },
  pulseCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  innerCircle: {
    position: 'absolute',
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#0051D5',
  },
  outerRing: {
    position: 'absolute',
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 2,
    borderColor: '#007AFF',
    opacity: 0.5,
  },
  text: {
    fontSize: 18,
    fontWeight: '500',
    color: '#1C1C1E',
    textAlign: 'center',
    lineHeight: 24,
    maxWidth: screenWidth - 80,
  },
  actionText: {
    marginBottom: 16,
  },
  actionButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 25,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 4,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});