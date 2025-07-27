import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

// Get API base URL from environment
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function HomeScreen({ navigation }) {
  const [backendStatus, setBackendStatus] = useState('Checking...');
  const [isConnected, setIsConnected] = useState(false);
  const [apiUrl, setApiUrl] = useState('');
  const [errorDetails, setErrorDetails] = useState('');

  useEffect(() => {
    testBackendConnection();
  }, []);

  const testBackendConnection = async () => {
    // Use the API service to get the proper base URL
    const baseUrl = API_BASE_URL || 'http://localhost:8000/api/v1';
    const healthUrl = baseUrl.replace('/api/v1', '/health');
    setApiUrl(healthUrl);
    
    try {
      console.log('Testing connection to:', healthUrl);
      const response = await fetch(healthUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setBackendStatus(`Connected`);
        setIsConnected(true);
        setErrorDetails('');
      } else {
        setBackendStatus('Backend error');
        setIsConnected(false);
        setErrorDetails(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Connection error:', error);
      setBackendStatus('Backend unavailable');
      setIsConnected(false);
      setErrorDetails(error.message || 'Network error');
    }
  };

  const navigateToRecord = () => {
    navigation.navigate('Record');
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>FutureGolf</Text>
        <Text style={styles.subtitle}>AI-Powered Golf Swing Analysis</Text>
      </View>

      <View style={styles.statusCard}>
        <View style={styles.statusHeader}>
          <Ionicons 
            name={isConnected ? 'checkmark-circle' : 'warning'} 
            size={20} 
            color={isConnected ? '#34C759' : '#FF9500'} 
          />
          <Text style={styles.statusTitle}>System Status</Text>
        </View>
        <Text style={styles.statusText}>{backendStatus}</Text>
        <Text style={styles.apiUrlText}>API: {apiUrl}</Text>
        {errorDetails ? <Text style={styles.errorText}>Error: {errorDetails}</Text> : null}
        <TouchableOpacity style={styles.refreshButton} onPress={testBackendConnection}>
          <Text style={styles.refreshButtonText}>Refresh</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.quickActions}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        
        <TouchableOpacity style={styles.actionCard} onPress={navigateToRecord}>
          <View style={styles.actionIcon}>
            <Ionicons name="videocam" size={30} color="#007AFF" />
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>Record Swing</Text>
            <Text style={styles.actionDescription}>
              Record your golf swing for AI analysis
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionCard} onPress={() => navigation.navigate('Analysis')}>
          <View style={styles.actionIcon}>
            <Ionicons name="analytics" size={30} color="#34C759" />
          </View>
          <View style={styles.actionContent}>
            <Text style={styles.actionTitle}>View Analysis</Text>
            <Text style={styles.actionDescription}>
              Review your swing analysis and coaching tips
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
        </TouchableOpacity>
      </View>

      <View style={styles.recentActivity}>
        <Text style={styles.sectionTitle}>Recent Activity</Text>
        <View style={styles.emptyState}>
          <Ionicons name="golf" size={50} color="#C7C7CC" />
          <Text style={styles.emptyStateText}>No recent swings</Text>
          <Text style={styles.emptyStateSubtext}>
            Record your first swing to get started
          </Text>
        </View>
      </View>
    </ScrollView>
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
    color: '#B3D9FF',
    textAlign: 'center',
  },
  statusCard: {
    backgroundColor: '#fff',
    margin: 20,
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  statusTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 8,
  },
  statusText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  apiUrlText: {
    fontSize: 12,
    color: '#999',
    marginBottom: 5,
    fontFamily: 'Menlo',
  },
  errorText: {
    fontSize: 12,
    color: '#FF3B30',
    marginBottom: 10,
  },
  refreshButton: {
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  refreshButtonText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '500',
  },
  quickActions: {
    paddingHorizontal: 20,
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 15,
    color: '#1C1C1E',
  },
  actionCard: {
    backgroundColor: '#fff',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    borderRadius: 12,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  actionIcon: {
    width: 50,
    height: 50,
    backgroundColor: '#F2F2F7',
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 2,
  },
  actionDescription: {
    fontSize: 14,
    color: '#666',
  },
  recentActivity: {
    paddingHorizontal: 20,
    marginBottom: 30,
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
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 15,
    marginBottom: 5,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});