import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Video } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import CoachingDisplay from './CoachingDisplay';

const { width, height } = Dimensions.get('window');

export default function SwingReview({ 
  videoUri, 
  analysisData,
  onClose,
  isAnalyzing = false 
}) {
  const [activeTab, setActiveTab] = useState('video');
  const [videoStatus, setVideoStatus] = useState({});
  const [showOverlay, setShowOverlay] = useState(true);
  const videoRef = useRef(null);

  // Extract coaching data from analysis
  const coachingScript = analysisData?.ai_analysis?.coaching_feedback || '';
  const swingMetrics = analysisData?.ai_analysis?.swing_metrics || {};
  const bodyAngles = analysisData?.ai_analysis?.body_angles || {};
  const recommendations = analysisData?.ai_analysis?.recommendations || [];
  const overallScore = analysisData?.ai_analysis?.overall_score || 0;

  useEffect(() => {
    // Auto-play video when component mounts
    if (videoRef.current && videoUri) {
      videoRef.current.playAsync();
    }
  }, [videoUri]);

  const handleVideoPress = () => {
    if (videoRef.current) {
      if (videoStatus.isPlaying) {
        videoRef.current.pauseAsync();
      } else {
        videoRef.current.playAsync();
      }
    }
  };

  const handleSeekToTimestamp = async (timestamp) => {
    if (videoRef.current && activeTab === 'video') {
      // Convert timestamp string (e.g., "0:15") to milliseconds
      const [minutes, seconds] = timestamp.split(':').map(Number);
      const milliseconds = (minutes * 60 + seconds) * 1000;
      await videoRef.current.setPositionAsync(milliseconds);
      await videoRef.current.playAsync();
    }
  };

  const renderMetricCard = (title, value, unit = '', icon) => (
    <View style={styles.metricCard}>
      {icon && <Ionicons name={icon} size={24} color="#007AFF" />}
      <Text style={styles.metricTitle}>{title}</Text>
      <Text style={styles.metricValue}>
        {value}
        {unit && <Text style={styles.metricUnit}> {unit}</Text>}
      </Text>
    </View>
  );

  const renderRecommendation = (recommendation, index) => (
    <View key={index} style={styles.recommendationCard}>
      <View style={styles.recommendationHeader}>
        <Ionicons 
          name={recommendation.priority === 'high' ? 'alert-circle' : 'information-circle'} 
          size={20} 
          color={recommendation.priority === 'high' ? '#FF3B30' : '#007AFF'} 
        />
        <Text style={styles.recommendationTitle}>{recommendation.title}</Text>
      </View>
      <Text style={styles.recommendationText}>{recommendation.description}</Text>
    </View>
  );

  const renderVideoTab = () => (
    <View style={styles.videoContainer}>
      <TouchableOpacity 
        activeOpacity={0.9} 
        onPress={handleVideoPress}
        style={styles.videoWrapper}
      >
        <Video
          ref={videoRef}
          source={{ uri: videoUri }}
          style={styles.video}
          useNativeControls={false}
          resizeMode="contain"
          shouldPlay={false}
          isLooping={true}
          onPlaybackStatusUpdate={setVideoStatus}
        />
        
        {/* Play/Pause Overlay */}
        {!videoStatus.isPlaying && (
          <View style={styles.playOverlay}>
            <Ionicons name="play-circle" size={80} color="rgba(255,255,255,0.9)" />
          </View>
        )}

        {/* Analysis Overlay */}
        {showOverlay && analysisData && (
          <View style={styles.analysisOverlay}>
            {/* Score Badge */}
            <View style={styles.scoreBadge}>
              <Text style={styles.scoreLabel}>Score</Text>
              <Text style={styles.scoreValue}>{overallScore}/100</Text>
            </View>

            {/* Key Metrics */}
            <View style={styles.overlayMetrics}>
              <View style={styles.overlayMetric}>
                <Text style={styles.overlayMetricLabel}>Tempo</Text>
                <Text style={styles.overlayMetricValue}>{swingMetrics.tempo || 'N/A'}</Text>
              </View>
              <View style={styles.overlayMetric}>
                <Text style={styles.overlayMetricLabel}>Balance</Text>
                <Text style={styles.overlayMetricValue}>{swingMetrics.balance || 'N/A'}</Text>
              </View>
            </View>
          </View>
        )}
      </TouchableOpacity>

      {/* Overlay Toggle */}
      <TouchableOpacity
        style={styles.overlayToggle}
        onPress={() => setShowOverlay(!showOverlay)}
      >
        <Ionicons 
          name={showOverlay ? "eye-off" : "eye"} 
          size={24} 
          color="#fff" 
        />
      </TouchableOpacity>
    </View>
  );

  const renderAnalysisTab = () => (
    <ScrollView style={styles.analysisContainer} showsVerticalScrollIndicator={false}>
      {/* Overall Performance */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Overall Performance</Text>
        <View style={styles.performanceCard}>
          <View style={styles.scoreCircle}>
            <Text style={styles.bigScore}>{overallScore}</Text>
            <Text style={styles.scoreSubtext}>out of 100</Text>
          </View>
          <Text style={styles.performanceSummary}>
            {overallScore >= 80 ? 'Excellent swing!' : 
             overallScore >= 60 ? 'Good swing with room for improvement' : 
             'Keep practicing - you\'re making progress!'}
          </Text>
        </View>
      </View>

      {/* Swing Metrics */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Swing Metrics</Text>
        <View style={styles.metricsGrid}>
          {renderMetricCard('Club Speed', swingMetrics.clubSpeed || '—', 'mph', 'speedometer-outline')}
          {renderMetricCard('Swing Plane', swingMetrics.swingPlane || '—', '°', 'analytics-outline')}
          {renderMetricCard('Tempo Ratio', swingMetrics.tempoRatio || '—', '', 'time-outline')}
          {renderMetricCard('Impact Position', swingMetrics.impactPosition || '—', '', 'locate-outline')}
        </View>
      </View>

      {/* Body Angles */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Body Positions</Text>
        <View style={styles.bodyAnglesContainer}>
          <View style={styles.angleItem}>
            <Text style={styles.angleLabel}>Spine Angle</Text>
            <Text style={styles.angleValue}>{bodyAngles.spineAngle || '—'}°</Text>
          </View>
          <View style={styles.angleItem}>
            <Text style={styles.angleLabel}>Hip Rotation</Text>
            <Text style={styles.angleValue}>{bodyAngles.hipRotation || '—'}°</Text>
          </View>
          <View style={[styles.angleItem, styles.lastAngleItem]}>
            <Text style={styles.angleLabel}>Shoulder Turn</Text>
            <Text style={styles.angleValue}>{bodyAngles.shoulderTurn || '—'}°</Text>
          </View>
        </View>
      </View>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recommendations</Text>
          {recommendations.map(renderRecommendation)}
        </View>
      )}
    </ScrollView>
  );

  const renderCoachingTab = () => (
    <CoachingDisplay
      coachingScript={coachingScript}
      timestamps={analysisData?.ai_analysis?.timestamps || []}
      onTimestampPress={handleSeekToTimestamp}
      isLoading={isAnalyzing}
    />
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.closeButton}>
          <Ionicons name="close" size={28} color="#1C1C1E" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Swing Analysis</Text>
        <View style={{ width: 28 }} />
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'video' && styles.activeTab]}
          onPress={() => setActiveTab('video')}
        >
          <Ionicons 
            name="videocam" 
            size={24} 
            color={activeTab === 'video' ? '#007AFF' : '#8E8E93'} 
          />
          <Text style={[styles.tabText, activeTab === 'video' && styles.activeTabText]}>
            Video
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'analysis' && styles.activeTab]}
          onPress={() => setActiveTab('analysis')}
        >
          <Ionicons 
            name="analytics" 
            size={24} 
            color={activeTab === 'analysis' ? '#007AFF' : '#8E8E93'} 
          />
          <Text style={[styles.tabText, activeTab === 'analysis' && styles.activeTabText]}>
            Analysis
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'coaching' && styles.activeTab]}
          onPress={() => setActiveTab('coaching')}
        >
          <Ionicons 
            name="school" 
            size={24} 
            color={activeTab === 'coaching' ? '#007AFF' : '#8E8E93'} 
          />
          <Text style={[styles.tabText, activeTab === 'coaching' && styles.activeTabText]}>
            Coaching
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      <View style={styles.content}>
        {isAnalyzing ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.loadingText}>Analyzing your swing...</Text>
            <Text style={styles.loadingSubtext}>This may take a moment</Text>
          </View>
        ) : (
          <>
            {activeTab === 'video' && renderVideoTab()}
            {activeTab === 'analysis' && renderAnalysisTab()}
            {activeTab === 'coaching' && renderCoachingTab()}
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 16,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#007AFF',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#8E8E93',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  loadingSubtext: {
    marginTop: 8,
    fontSize: 14,
    color: '#8E8E93',
  },
  videoContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  videoWrapper: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  video: {
    width: width,
    height: height * 0.6,
  },
  playOverlay: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
  },
  analysisOverlay: {
    position: 'absolute',
    top: 20,
    left: 20,
    right: 20,
  },
  scoreBadge: {
    backgroundColor: 'rgba(0, 122, 255, 0.9)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    alignSelf: 'flex-start',
  },
  scoreLabel: {
    color: '#fff',
    fontSize: 12,
    opacity: 0.8,
  },
  scoreValue: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  overlayMetrics: {
    flexDirection: 'row',
    marginTop: 16,
  },
  overlayMetric: {
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 8,
  },
  overlayMetricLabel: {
    color: '#fff',
    fontSize: 11,
    opacity: 0.8,
  },
  overlayMetricValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  overlayToggle: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  analysisContainer: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 12,
  },
  performanceCard: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  scoreCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  bigScore: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#fff',
  },
  scoreSubtext: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.8,
  },
  performanceSummary: {
    fontSize: 16,
    color: '#1C1C1E',
    textAlign: 'center',
    lineHeight: 22,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
  },
  metricCard: {
    backgroundColor: '#fff',
    width: (width - 48) / 2,
    margin: 4,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  metricTitle: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 8,
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  metricUnit: {
    fontSize: 14,
    fontWeight: 'normal',
    color: '#8E8E93',
  },
  bodyAnglesContainer: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    padding: 16,
    borderRadius: 12,
  },
  angleItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  lastAngleItem: {
    borderBottomWidth: 0,
  },
  angleLabel: {
    fontSize: 16,
    color: '#1C1C1E',
  },
  angleValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#007AFF',
  },
  recommendationCard: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  recommendationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginLeft: 8,
    flex: 1,
  },
  recommendationText: {
    fontSize: 14,
    color: '#3C3C43',
    lineHeight: 20,
  },
});