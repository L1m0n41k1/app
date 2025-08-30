import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../contexts/AuthContext';

export default function SettingsScreen() {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    Alert.alert(
      'Выход',
      'Вы уверены, что хотите выйти из аккаунта?',
      [
        {
          text: 'Отмена',
          style: 'cancel',
        },
        {
          text: 'Выйти',
          style: 'destructive',
          onPress: logout,
        },
      ]
    );
  };

  const SettingsItem = ({ icon, title, subtitle, onPress, color = '#FFFFFF' }: any) => (
    <TouchableOpacity style={styles.settingsItem} onPress={onPress}>
      <View style={styles.settingsItemLeft}>
        <Ionicons name={icon} size={24} color={color} />
        <View style={styles.settingsItemText}>
          <Text style={[styles.settingsItemTitle, { color }]}>{title}</Text>
          {subtitle && <Text style={styles.settingsItemSubtitle}>{subtitle}</Text>}
        </View>
      </View>
      <Ionicons name="chevron-forward" size={20} color="#8E8E93" />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.title}>Настройки</Text>
        </View>

        {/* Profile Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Профиль</Text>
          <View style={styles.profileCard}>
            <View style={styles.profileIcon}>
              <Text style={styles.profileInitial}>{user?.name?.[0]?.toUpperCase()}</Text>
            </View>
            <View style={styles.profileInfo}>
              <Text style={styles.profileName}>{user?.name}</Text>
              <Text style={styles.profileEmail}>{user?.email}</Text>
              <Text style={styles.profilePlan}>
                План: {user?.subscription_plan === 'free_trial' ? 'Пробный' : user?.subscription_plan}
              </Text>
            </View>
          </View>
        </View>

        {/* App Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Приложение</Text>
          <View style={styles.settingsGroup}>
            <SettingsItem
              icon="person-outline"
              title="Профиль"
              subtitle="Редактировать информацию"
              onPress={() => Alert.alert('В разработке', 'Функция будет доступна позже')}
            />
            <SettingsItem
              icon="card-outline"
              title="Подписка"
              subtitle="Управление планом"
              onPress={() => Alert.alert('В разработке', 'Функция будет доступна позже')}
            />
            <SettingsItem
              icon="notifications-outline"
              title="Уведомления"
              subtitle="Настройки уведомлений"
              onPress={() => Alert.alert('В разработке', 'Функция будет доступна позже')}
            />
          </View>
        </View>

        {/* Support */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Поддержка</Text>
          <View style={styles.settingsGroup}>
            <SettingsItem
              icon="help-circle-outline"
              title="Помощь"
              subtitle="FAQ и поддержка"
              onPress={() => Alert.alert('В разработке', 'Функция будет доступна позже')}
            />
            <SettingsItem
              icon="document-text-outline"
              title="Условия использования"
              onPress={() => Alert.alert('В разработке', 'Функция будет доступна позже')}
            />
            <SettingsItem
              icon="shield-checkmark-outline"
              title="Политика конфиденциальности"
              onPress={() => Alert.alert('В разработке', 'Функция будет доступна позже')}
            />
          </View>
        </View>

        {/* Logout */}
        <View style={styles.section}>
          <View style={styles.settingsGroup}>
            <SettingsItem
              icon="log-out-outline"
              title="Выйти"
              onPress={handleLogout}
              color="#FF3B30"
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 20,
    marginHorizontal: 20,
  },
  profileIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#25D366',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  profileInitial: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 16,
    color: '#8E8E93',
    marginBottom: 4,
  },
  profilePlan: {
    fontSize: 14,
    color: '#25D366',
    fontWeight: '600',
  },
  settingsGroup: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    marginHorizontal: 20,
  },
  settingsItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  settingsItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingsItemText: {
    marginLeft: 16,
    flex: 1,
  },
  settingsItemTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  settingsItemSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
  },
});