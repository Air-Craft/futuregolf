import { StatusBar } from 'expo-status-bar';
import React, { useState, useEffect } from 'react';
import AppNavigator from './navigation/AppNavigator';
import TTSPopupWidget from './components/TTSPopupWidget';
import ttsManager from './services/ttsManager';

export default function App() {
  const [ttsState, setTTSState] = useState({
    isVisible: false,
    text: '',
    rmsValue: 0,
    showAction: false,
    actionText: '',
    onAction: () => {},
  });

  useEffect(() => {
    // Initialize TTS manager
    ttsManager.initialize().catch(console.error);

    // Set up TTS callbacks
    ttsManager.setCallbacks({
      onRMS: (rms) => {
        setTTSState(prev => ({
          ...prev,
          rmsValue: rms,
        }));
      },
      onStatus: (status) => {
        setTTSState(prev => ({
          ...prev,
          isVisible: status.isPlaying || status.isLoading,
          text: status.text,
        }));
      },
      onCompletion: () => {
        setTTSState(prev => ({
          ...prev,
          isVisible: false,
          text: '',
          rmsValue: 0,
          showAction: false,
        }));
      },
      onError: (error) => {
        console.error('TTS Error:', error);
        setTTSState(prev => ({
          ...prev,
          isVisible: false,
          text: '',
          rmsValue: 0,
          showAction: false,
        }));
      },
    });

    // Cleanup on unmount
    return () => {
      ttsManager.cleanup();
    };
  }, []);

  return (
    <>
      <AppNavigator />
      <TTSPopupWidget
        isVisible={ttsState.isVisible}
        text={ttsState.text}
        rmsValue={ttsState.rmsValue}
        showAction={ttsState.showAction}
        actionText={ttsState.actionText}
        onAction={ttsState.onAction}
      />
      <StatusBar style="auto" />
    </>
  );
}
