import React from 'react';
import { View, StyleSheet } from 'react-native';
import VideoRecording from '../components/VideoRecording';

export default function VideoRecordingScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <VideoRecording navigation={navigation} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});