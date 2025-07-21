import React from 'react';
import { render, act, waitFor } from '@testing-library/react-native';
import { Animated } from 'react-native';
import TTSPopupWidget from '../../components/TTSPopupWidget';
import MockAudioStream from '../mocks/mockAudioStream';
import AudioAnalyzer from '../../utils/audioAnalyzer';

// Mock the blur view since it's not available in test environment
jest.mock('expo-blur', () => ({
  BlurView: ({ children }) => children,
}));

describe('TTSPopupWidget', () => {
  let mockAudioStream;
  let audioAnalyzer;

  beforeEach(() => {
    mockAudioStream = new MockAudioStream();
    audioAnalyzer = new AudioAnalyzer();
    jest.useFakeTimers();
  });

  afterEach(() => {
    mockAudioStream.stopStream();
    jest.useRealTimers();
  });

  describe('Visibility', () => {
    it('should be hidden when isVisible is false', () => {
      const { queryByTestId } = render(
        <TTSPopupWidget
          isVisible={false}
          text="Test text"
          rmsValue={0}
        />
      );
      
      const widget = queryByTestId('tts-popup-widget');
      expect(widget).toBeNull();
    });

    it('should be visible when isVisible is true', () => {
      const { getByTestId } = render(
        <TTSPopupWidget
          isVisible={true}
          text="Test text"
          rmsValue={0}
        />
      );
      
      const widget = getByTestId('tts-popup-widget');
      expect(widget).toBeTruthy();
    });

    it('should fade in smoothly when becoming visible', async () => {
      const { rerender, getByTestId } = render(
        <TTSPopupWidget
          isVisible={false}
          text="Test text"
          rmsValue={0}
        />
      );

      rerender(
        <TTSPopupWidget
          isVisible={true}
          text="Test text"
          rmsValue={0}
        />
      );

      await waitFor(() => {
        const widget = getByTestId('tts-popup-widget');
        expect(widget.props.style.opacity).toBeGreaterThan(0);
      });
    });
  });

  describe('Pulse Animation', () => {
    it('should scale pulse based on RMS value', async () => {
      const { getByTestId, rerender } = render(
        <TTSPopupWidget
          isVisible={true}
          text="Test text"
          rmsValue={0}
        />
      );

      const pulse = getByTestId('tts-pulse-circle');
      
      // Test different RMS values
      const testCases = [
        { rms: 0, expectedScale: 0.8 },      // Silence
        { rms: 0.3, expectedScale: 1.02 },   // Normal speech
        { rms: 0.7, expectedScale: 1.5 },    // Loud speech
      ];

      for (const { rms, expectedScale } of testCases) {
        rerender(
          <TTSPopupWidget
            isVisible={true}
            text="Test text"
            rmsValue={rms}
          />
        );

        act(() => {
          jest.advanceTimersByTime(100);
        });

        await waitFor(() => {
          const transform = pulse.props.style.transform;
          const scaleTransform = transform.find(t => t.scale);
          expect(scaleTransform.scale._value).toBeCloseTo(expectedScale, 1);
        });
      }
    });

    it('should animate smoothly between RMS values', async () => {
      const { getByTestId, rerender } = render(
        <TTSPopupWidget
          isVisible={true}
          text="Test text"
          rmsValue={0}
        />
      );

      // Simulate speech pattern
      const speechPattern = [0, 0.2, 0.4, 0.6, 0.4, 0.2, 0];
      
      for (const rms of speechPattern) {
        rerender(
          <TTSPopupWidget
            isVisible={true}
            text="Test text"
            rmsValue={rms}
          />
        );

        act(() => {
          jest.advanceTimersByTime(16); // ~60fps
        });
      }

      const pulse = getByTestId('tts-pulse-circle');
      expect(pulse).toBeTruthy();
    });

    it('should sync with mock audio stream', async () => {
      let capturedRMS = [];
      
      const { rerender } = render(
        <TTSPopupWidget
          isVisible={true}
          text="Test text"
          rmsValue={0}
        />
      );

      // Start mock audio stream
      mockAudioStream.setPattern('speech');
      mockAudioStream.startStream({
        onRMS: (rms) => {
          capturedRMS.push(rms);
          rerender(
            <TTSPopupWidget
              isVisible={true}
              text="Test text"
              rmsValue={rms}
            />
          );
        },
        updateInterval: 16, // 60fps
      });

      // Let it run for 100ms
      act(() => {
        jest.advanceTimersByTime(100);
      });

      mockAudioStream.stopStream();

      // Verify we received RMS updates
      expect(capturedRMS.length).toBeGreaterThan(0);
      expect(capturedRMS.some(rms => rms > 0)).toBe(true);
    });
  });

  describe('Text Display', () => {
    it('should display text in chunks', () => {
      const longText = "This is a very long text that should be displayed in chunks to fit the available space properly.";
      
      const { getByTestId } = render(
        <TTSPopupWidget
          isVisible={true}
          text={longText}
          rmsValue={0.3}
        />
      );

      const textElement = getByTestId('tts-text-display');
      expect(textElement.props.children).toBe(longText);
    });

    it('should handle empty text gracefully', () => {
      const { queryByTestId } = render(
        <TTSPopupWidget
          isVisible={true}
          text=""
          rmsValue={0.3}
        />
      );

      const textElement = queryByTestId('tts-text-display');
      expect(textElement).toBeTruthy();
      expect(textElement.props.children).toBe("");
    });

    it('should update text dynamically', () => {
      const { getByTestId, rerender } = render(
        <TTSPopupWidget
          isVisible={true}
          text="First text"
          rmsValue={0.3}
        />
      );

      let textElement = getByTestId('tts-text-display');
      expect(textElement.props.children).toBe("First text");

      rerender(
        <TTSPopupWidget
          isVisible={true}
          text="Second text"
          rmsValue={0.3}
        />
      );

      textElement = getByTestId('tts-text-display');
      expect(textElement.props.children).toBe("Second text");
    });
  });

  describe('Cross-fade to Action', () => {
    it('should show action button when provided', () => {
      const onAction = jest.fn();
      
      const { getByTestId, getByText } = render(
        <TTSPopupWidget
          isVisible={true}
          text="Ready to analyze?"
          rmsValue={0}
          showAction={true}
          actionText="Start Analysis"
          onAction={onAction}
        />
      );

      const actionButton = getByTestId('tts-action-button');
      expect(actionButton).toBeTruthy();
      expect(getByText('Start Analysis')).toBeTruthy();
    });

    it('should call onAction when button is pressed', () => {
      const onAction = jest.fn();
      
      const { getByTestId } = render(
        <TTSPopupWidget
          isVisible={true}
          text="Ready to analyze?"
          rmsValue={0}
          showAction={true}
          actionText="Start Analysis"
          onAction={onAction}
        />
      );

      const actionButton = getByTestId('tts-action-button');
      actionButton.props.onPress();
      
      expect(onAction).toHaveBeenCalledTimes(1);
    });

    it('should cross-fade between speech and action modes', async () => {
      const { getByTestId, rerender, queryByTestId } = render(
        <TTSPopupWidget
          isVisible={true}
          text="Speaking..."
          rmsValue={0.5}
          showAction={false}
        />
      );

      // Verify pulse is visible
      expect(getByTestId('tts-pulse-circle')).toBeTruthy();
      expect(queryByTestId('tts-action-button')).toBeNull();

      // Switch to action mode
      rerender(
        <TTSPopupWidget
          isVisible={true}
          text="Ready to analyze?"
          rmsValue={0}
          showAction={true}
          actionText="Start Analysis"
          onAction={() => {}}
        />
      );

      await waitFor(() => {
        expect(queryByTestId('tts-pulse-circle')).toBeNull();
        expect(getByTestId('tts-action-button')).toBeTruthy();
      });
    });
  });

  describe('Audio Analyzer Integration', () => {
    it('should properly smooth RMS values', () => {
      const analyzer = new AudioAnalyzer({ smoothingFactor: 0.3 });
      
      // Test smoothing
      const rmsValues = [0, 0.5, 0.5, 0.5];
      const smoothedValues = rmsValues.map(rms => analyzer.smoothRMS(rms));
      
      expect(smoothedValues[0]).toBe(0);
      expect(smoothedValues[1]).toBeCloseTo(0.15, 2); // 0 * 0.7 + 0.5 * 0.3
      expect(smoothedValues[2]).toBeCloseTo(0.255, 2); // 0.15 * 0.7 + 0.5 * 0.3
      expect(smoothedValues[3]).toBeCloseTo(0.3285, 2); // 0.255 * 0.7 + 0.5 * 0.3
    });

    it('should map RMS to appropriate scale values', () => {
      const analyzer = new AudioAnalyzer();
      
      expect(analyzer.rmsToScale(0)).toBe(0.8);      // Minimum scale
      expect(analyzer.rmsToScale(0.5)).toBe(1.15);   // Mid scale
      expect(analyzer.rmsToScale(1)).toBe(1.5);      // Maximum scale
    });
  });

  describe('Performance', () => {
    it('should handle rapid RMS updates at 60fps', async () => {
      const { rerender } = render(
        <TTSPopupWidget
          isVisible={true}
          text="Test"
          rmsValue={0}
        />
      );

      const startTime = Date.now();
      const frames = 60; // 1 second at 60fps

      for (let i = 0; i < frames; i++) {
        const rms = Math.sin(i * 0.1) * 0.5 + 0.5; // Oscillating RMS
        rerender(
          <TTSPopupWidget
            isVisible={true}
            text="Test"
            rmsValue={rms}
          />
        );
        
        act(() => {
          jest.advanceTimersByTime(16); // ~60fps
        });
      }

      const elapsed = Date.now() - startTime;
      expect(elapsed).toBeLessThan(100); // Should complete quickly
    });
  });
});