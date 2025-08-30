import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface MessagingAccount {
  id: string;
  platform: 'whatsapp' | 'telegram';
  display_name: string;
  is_active: boolean;
  created_at: string;
}

export default function AccountsScreen() {
  const [accounts, setAccounts] = useState<MessagingAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) return;

      const response = await fetch(`${API_URL}/api/accounts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAccounts(data);
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddAccount = () => {
    Alert.alert(
      'Добавить аккаунт',
      'Выберите платформу',
      [
        {
          text: 'WhatsApp',
          onPress: () => addAccount('whatsapp'),
        },
        {
          text: 'Telegram',
          onPress: () => addAccount('telegram'),
        },
        {
          text: 'Отмена',
          style: 'cancel',
        },
      ]
    );
  };

  const addAccount = (platform: 'whatsapp' | 'telegram') => {
    // TODO: Implement WebView for account registration
    Alert.alert('В разработке', `Добавление аккаунта ${platform} будет реализовано позже`);
  };

  const renderAccount = ({ item }: { item: MessagingAccount }) => (
    <View style={styles.accountItem}>
      <View style={styles.accountIcon}>
        <Ionicons 
          name={item.platform === 'whatsapp' ? 'logo-whatsapp' : 'send'} 
          size={24} 
          color={item.platform === 'whatsapp' ? '#25D366' : '#0088cc'} 
        />
      </View>
      <View style={styles.accountInfo}>
        <Text style={styles.accountName}>{item.display_name}</Text>
        <Text style={styles.accountPlatform}>
          {item.platform === 'whatsapp' ? 'WhatsApp' : 'Telegram'}
        </Text>
      </View>
      <View style={styles.accountStatus}>
        <View style={[styles.statusIndicator, { backgroundColor: item.is_active ? '#25D366' : '#8E8E93' }]} />
        <Text style={styles.statusText}>
          {item.is_active ? 'Активен' : 'Неактивен'}
        </Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Мои аккаунты</Text>
        <TouchableOpacity style={styles.addButton} onPress={handleAddAccount}>
          <Ionicons name="add" size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {accounts.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="person-add-outline" size={64} color="#8E8E93" />
          <Text style={styles.emptyStateTitle}>Нет аккаунтов</Text>
          <Text style={styles.emptyStateText}>
            Добавьте аккаунт WhatsApp или Telegram для начала работы
          </Text>
          <TouchableOpacity style={styles.addAccountButton} onPress={handleAddAccount}>
            <Text style={styles.addAccountButtonText}>Добавить аккаунт</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={accounts}
          renderItem={renderAccount}
          keyExtractor={(item) => item.id}
          style={styles.accountsList}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  addButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#25D366',
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyStateTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 24,
    marginBottom: 12,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  addAccountButton: {
    backgroundColor: '#25D366',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 25,
  },
  addAccountButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  accountsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  accountItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  accountIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#2C2C2E',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  accountInfo: {
    flex: 1,
  },
  accountName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  accountPlatform: {
    fontSize: 14,
    color: '#8E8E93',
  },
  accountStatus: {
    alignItems: 'center',
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginBottom: 4,
  },
  statusText: {
    fontSize: 12,
    color: '#8E8E93',
  },
});