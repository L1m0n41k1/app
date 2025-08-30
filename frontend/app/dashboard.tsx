import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { useAuth } from '../contexts/AuthContext';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface DashboardStats {
  active_accounts: number;
  messages_today: {
    successful: number;
    failed: number;
  };
  active_jobs: number;
  recent_jobs: any[];
}

export default function DashboardScreen() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    active_accounts: 0,
    messages_today: { successful: 0, failed: 0 },
    active_jobs: 0,
    recent_jobs: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) return;

      const response = await fetch(`${API_URL}/api/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        Alert.alert('Ошибка', 'Не удалось загрузить данные');
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      Alert.alert('Ошибка', 'Произошла ошибка при загрузке данных');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
  };

  const StatCard = ({ title, value, subtitle, icon, color }: any) => (
    <View style={styles.statCard}>
      <View style={styles.statHeader}>
        <Text style={styles.statTitle}>{title}</Text>
        <Ionicons name={icon} size={24} color={color} />
      </View>
      <Text style={styles.statValue}>{value}</Text>
      {subtitle && <Text style={styles.statSubtitle}>{subtitle}</Text>}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#25D366" />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Добро пожаловать, {user?.name}!</Text>
            <Text style={styles.subGreeting}>Панель управления рассылками</Text>
          </View>
          <TouchableOpacity style={styles.newJobButton}>
            <Ionicons name="add" size={20} color="#FFFFFF" />
            <Text style={styles.newJobButtonText}>Новая рассылка</Text>
          </TouchableOpacity>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <StatCard
            title="Активные аккаунты"
            value={stats.active_accounts}
            subtitle={`из ${stats.active_accounts} всего`}
            icon="person-circle-outline"
            color="#25D366"
          />
          <StatCard
            title="Сообщений сегодня"
            value={stats.messages_today.successful}
            subtitle={
              stats.messages_today.failed > 0
                ? `${stats.messages_today.failed} неуспешных`
                : 'Все успешно'
            }
            icon="send-outline"
            color="#25D366"
          />
          <StatCard
            title="Активные задания"
            value={stats.active_jobs}
            subtitle="в процессе выполнения"
            icon="time-outline"
            color="#FF9500"
          />
        </View>

        {/* Recent Jobs */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Недавние рассылки</Text>
            <TouchableOpacity>
              <Ionicons name="refresh" size={20} color="#8E8E93" />
            </TouchableOpacity>
          </View>

          {stats.recent_jobs.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="send-outline" size={48} color="#8E8E93" />
              <Text style={styles.emptyStateText}>Рассылок пока нет</Text>
              <Text style={styles.emptyStateSubtext}>
                Создайте первую рассылку, чтобы увидеть её здесь
              </Text>
            </View>
          ) : (
            <View style={styles.jobsList}>
              {stats.recent_jobs.map((job: any, index: number) => (
                <View key={job.id || index} style={styles.jobItem}>
                  <View style={styles.jobInfo}>
                    <Text style={styles.jobName}>{job.name}</Text>
                    <Text style={styles.jobDetails}>
                      {job.platform} • {job.total_recipients} получателей
                    </Text>
                  </View>
                  <View style={styles.jobStatus}>
                    <Text style={[styles.jobStatusText, { color: getStatusColor(job.status) }]}>
                      {getStatusText(job.status)}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return '#25D366';
    case 'running':
      return '#FF9500';
    case 'failed':
      return '#FF3B30';
    case 'pending':
      return '#8E8E93';
    default:
      return '#8E8E93';
  }
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed':
      return 'Завершено';
    case 'running':
      return 'Выполняется';
    case 'failed':
      return 'Ошибка';
    case 'pending':
      return 'Ожидание';
    default:
      return 'Неизвестно';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 24,
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  subGreeting: {
    fontSize: 16,
    color: '#8E8E93',
  },
  newJobButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#25D366',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  newJobButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    marginLeft: 6,
    fontSize: 14,
  },
  statsGrid: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  statCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  statHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  statTitle: {
    fontSize: 16,
    color: '#8E8E93',
    fontWeight: '500',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  statSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
  },
  section: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  jobsList: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 4,
  },
  jobItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  jobInfo: {
    flex: 1,
  },
  jobName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  jobDetails: {
    fontSize: 14,
    color: '#8E8E93',
  },
  jobStatus: {
    alignItems: 'flex-end',
  },
  jobStatusText: {
    fontSize: 14,
    fontWeight: '600',
  },
});