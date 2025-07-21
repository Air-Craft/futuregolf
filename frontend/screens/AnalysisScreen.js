import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, RefreshControl, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import SwingReview from '../components/SwingReview';

export default function AnalysisScreen({ navigation }) {
  const [analyses, setAnalyses] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [showReview, setShowReview] = useState(false);

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    try {
      // Mock data for development - replace with actual API call
      // const response = await fetch('http://localhost:8000/api/v1/video-analysis/user/analyses', {
      //   headers: {
      //     'Authorization': `Bearer ${authToken}`,
      //   },
      // });
      // const data = await response.json();
      // setAnalyses(data.analyses);
      
      // Mock analyses data
      setTimeout(() => {
        setAnalyses([
          {
            id: 1,
            video_id: 1,
            status: 'completed',
            created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
            completed_at: new Date(Date.now() - 86000000).toISOString(),
            confidence: 0.92,
            has_results: true,
            overall_score: 85,
            view_angle: 'Down-the-line',
            club_type: 'Driver',
            ai_analysis: {
              overall_score: 85,
              coaching_feedback: "Great swing! Your setup position is solid with good posture and alignment. During the backswing, you maintain excellent spine angle and achieve a full shoulder turn. The transition from backswing to downswing is smooth, showing good tempo. At impact, your weight has transferred nicely to the front foot. To improve further, focus on maintaining your spine angle through impact - you tend to stand up slightly. Also, work on keeping your head steady throughout the swing for better consistency.",
              swing_metrics: {
                clubSpeed: "105",
                swingPlane: "45",
                tempoRatio: "3:1",
                impactPosition: "Slightly toe"
              },
              body_angles: {
                spineAngle: "30",
                hipRotation: "48",
                shoulderTurn: "95"
              }
            }
          },
          {
            id: 2,
            video_id: 2,
            status: 'completed',
            created_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
            completed_at: new Date(Date.now() - 172000000).toISOString(),
            confidence: 0.88,
            has_results: true,
            overall_score: 72,
            view_angle: 'Front',
            club_type: '7 Iron',
            ai_analysis: {
              overall_score: 72,
              coaching_feedback: "Good foundation with room for improvement. Focus on weight transfer...",
              swing_metrics: {
                clubSpeed: "85",
                swingPlane: "52",
                tempoRatio: "2.5:1",
                impactPosition: "Centered"
              },
              body_angles: {
                spineAngle: "35",
                hipRotation: "40",
                shoulderTurn: "85"
              }
            }
          }
        ]);
        setIsLoading(false);
        setIsRefreshing(false);
      }, 1000);
      
    } catch (error) {
      console.error('Error loading analyses:', error);
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const onRefresh = () => {
    setIsRefreshing(true);
    loadAnalyses();
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#34C759';
    if (score >= 60) return '#FF9500';
    return '#FF3B30';
  };

  const renderAnalysisCard = (analysis) => (
    <TouchableOpacity
      key={analysis.id}
      style={styles.analysisCard}
      onPress={() => {
        setSelectedAnalysis(analysis);
        setShowReview(true);
      }}
    >
      <View style={styles.cardHeader}>
        <View style={styles.cardInfo}>
          <Text style={styles.cardDate}>{formatDate(analysis.created_at)}</Text>
          <View style={styles.cardDetails}>
            <Text style={styles.cardDetail}>{analysis.view_angle}</Text>
            <Text style={styles.cardDivider}>•</Text>
            <Text style={styles.cardDetail}>{analysis.club_type}</Text>
          </View>
        </View>
        <View style={[styles.scoreCircle, { backgroundColor: getScoreColor(analysis.overall_score) }]}>
          <Text style={styles.scoreText}>{analysis.overall_score}</Text>
        </View>
      </View>
      
      <Text style={styles.cardSummary} numberOfLines={2}>
        {analysis.ai_analysis.coaching_feedback}
      </Text>
      
      <View style={styles.cardFooter}>
        <View style={styles.metricsPreview}>
          <View style={styles.metricItem}>
            <Ionicons name="speedometer-outline" size={16} color="#8E8E93" />
            <Text style={styles.metricValue}>{analysis.ai_analysis.swing_metrics.clubSpeed} mph</Text>
          </View>
          <View style={styles.metricItem}>
            <Ionicons name="analytics-outline" size={16} color="#8E8E93" />
            <Text style={styles.metricValue}>{analysis.ai_analysis.swing_metrics.swingPlane}°</Text>
          </View>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
      </View>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading analyses...</Text>
      </View>
    );
  }
  return (
    <View style={styles.container}>
      <ScrollView 
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={onRefresh}
            tintColor="#007AFF"
          />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>Swing Analysis</Text>
          <Text style={styles.subtitle}>Review your golf swing insights</Text>
        </View>

        <View style={styles.content}>
          {analyses.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="analytics-outline" size={80} color="#C7C7CC" />
              <Text style={styles.emptyStateTitle}>No Analysis Yet</Text>
              <Text style={styles.emptyStateText}>
                Record a swing to see AI-powered analysis and coaching tips
              </Text>
              <TouchableOpacity 
                style={styles.recordButton}
                onPress={() => navigation.navigate('Record')}
              >
                <Ionicons name="videocam" size={20} color="#fff" />
                <Text style={styles.recordButtonText}>Record Swing</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.analysesList}>
              {analyses.map(renderAnalysisCard)}
            </View>
          )}
        </View>
      </ScrollView>

      {/* Swing Review Modal */}
      <Modal
        visible={showReview}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={() => {
          setShowReview(false);
          setSelectedAnalysis(null);
        }}
      >
        {selectedAnalysis && (
          <SwingReview
            videoUri={null} // Video URI would be fetched from backend
            analysisData={selectedAnalysis}
            isAnalyzing={false}
            onClose={() => {
              setShowReview(false);
              setSelectedAnalysis(null);
            }}
          />
        )}
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  scrollView: {
    flex: 1,
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
  header: {
    backgroundColor: '#34C759',
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
    color: '#B3FFB3',
    textAlign: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  emptyState: {
    backgroundColor: '#fff',
    padding: 40,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 20,
    marginBottom: 10,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 20,
  },
  recordButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
    marginTop: 10,
  },
  recordButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  analysesList: {
    paddingBottom: 20,
  },
  analysisCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  cardInfo: {
    flex: 1,
  },
  cardDate: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 4,
  },
  cardDetails: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardDetail: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  cardDivider: {
    fontSize: 16,
    color: '#C7C7CC',
    marginHorizontal: 8,
  },
  scoreCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  cardSummary: {
    fontSize: 14,
    color: '#3C3C43',
    lineHeight: 20,
    marginBottom: 12,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricsPreview: {
    flexDirection: 'row',
    gap: 16,
  },
  metricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metricValue: {
    fontSize: 14,
    color: '#8E8E93',
  },
});