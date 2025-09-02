import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface AccountWebViewProps {
  visible: boolean;
  platform: 'whatsapp' | 'telegram';
  onClose: () => void;
  onAccountCreated: (account: any) => void;
}

export default function AccountWebView({ visible, platform, onClose, onAccountCreated }: AccountWebViewProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isRegistered, setIsRegistered] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const webViewRef = useRef<WebView>(null);

  const getInitialURL = () => {
    return platform === 'whatsapp' 
      ? 'https://web.whatsapp.com'
      : 'https://web.telegram.org/k/';
  };

  const getUserAgent = () => {
    // Desktop Chrome User Agent для имитации ПК
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
  };

  const checkIfRegistered = (url: string) => {
    // Проверяем успешность регистрации по URL
    if (platform === 'whatsapp') {
      // Если нет QR кода в URL и мы на главной странице WhatsApp
      return url.includes('web.whatsapp.com') && !url.includes('qr');
    } else {
      // Для Telegram проверяем, что мы не на странице авторизации
      return url.includes('web.telegram.org/k/') && !url.includes('login');
    }
  };

  const handleNavigationStateChange = (navState: any) => {
    const { url } = navState;
    
    // Проверяем успешную регистрацию
    if (checkIfRegistered(url) && !isRegistered) {
      // Дополнительная проверка через JavaScript
      const checkScript = platform === 'whatsapp' 
        ? `
          // WhatsApp: проверяем наличие чатов или поискового поля
          const searchBox = document.querySelector('[data-testid="chat-list-search"]');
          const chatList = document.querySelector('[data-testid="chat-list"]');
          const qrCode = document.querySelector('[data-testid="qrcode"]');
          
          if ((searchBox || chatList) && !qrCode) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'registration_success',
              platform: 'whatsapp'
            }));
          }
        `
        : `
          // Telegram: проверяем наличие элементов интерфейса
          const chatList = document.querySelector('.chat-list');
          const searchInput = document.querySelector('.input-search');
          const loginForm = document.querySelector('.login-form');
          
          if ((chatList || searchInput) && !loginForm) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'registration_success', 
              platform: 'telegram'
            }));
          }
        `;

      webViewRef.current?.injectJavaScript(checkScript);
    }
  };

  const handleMessage = (event: any) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      
      if (data.type === 'registration_success') {
        setIsRegistered(true);
        setIsLoading(false);
        
        Alert.alert(
          'Успешно!',
          `Аккаунт ${platform === 'whatsapp' ? 'WhatsApp' : 'Telegram'} успешно зарегистрирован. Введите название для этого аккаунта.`,
          [
            {
              text: 'OK',
              onPress: () => promptForDisplayName(),
            },
          ]
        );
      }
    } catch (error) {
      console.error('Error parsing WebView message:', error);
    }
  };

  const promptForDisplayName = () => {
    Alert.prompt(
      'Название аккаунта',
      'Введите название для этого аккаунта:',
      [
        {
          text: 'Отмена',
          style: 'cancel',
          onPress: onClose,
        },
        {
          text: 'Сохранить',
          onPress: (name) => name && saveAccount(name),
        },
      ],
      'plain-text',
      `${platform === 'whatsapp' ? 'WhatsApp' : 'Telegram'} аккаунт`
    );
  };

  const saveAccount = async (name: string) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) return;

      // Получаем данные сессии из WebView
      const sessionScript = `
        JSON.stringify({
          cookies: document.cookie,
          localStorage: JSON.stringify(localStorage),
          sessionStorage: JSON.stringify(sessionStorage),
          url: window.location.href
        })
      `;

      webViewRef.current?.injectJavaScript(`
        window.ReactNativeWebView.postMessage(${sessionScript});
      `);

      // Сохраняем аккаунт в базе данных
      const response = await fetch(`${API_URL}/api/accounts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          platform: platform,
          display_name: name,
          session_data: {
            registered_at: new Date().toISOString(),
            platform: platform,
          },
        }),
      });

      if (response.ok) {
        const account = await response.json();
        onAccountCreated(account);
        Alert.alert('Успех', 'Аккаунт успешно сохранен!');
        onClose();
      } else {
        Alert.alert('Ошибка', 'Не удалось сохранить аккаунт');
      }
    } catch (error) {
      console.error('Error saving account:', error);
      Alert.alert('Ошибка', 'Произошла ошибка при сохранении аккаунта');
    }
  };

  const handleClose = () => {
    Alert.alert(
      'Закрыть регистрацию?',
      'Вы уверены, что хотите закрыть окно регистрации? Аккаунт не будет сохранен.',
      [
        {
          text: 'Отмена',
          style: 'cancel',
        },
        {
          text: 'Закрыть',
          style: 'destructive',
          onPress: onClose,
        },
      ]
    );
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color="#FFFFFF" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>
            Добавить {platform === 'whatsapp' ? 'WhatsApp' : 'Telegram'} аккаунт
          </Text>
          <View style={styles.placeholder} />
        </View>

        {/* Instructions */}
        <View style={styles.instructions}>
          <Text style={styles.instructionText}>
            {platform === 'whatsapp' 
              ? 'Отсканируйте QR-код или войдите через номер телефона в WhatsApp Web'
              : 'Войдите в свой аккаунт Telegram Web'
            }
          </Text>
        </View>

        {/* WebView */}
        <WebView
          ref={webViewRef}
          source={{ uri: getInitialURL() }}
          userAgent={getUserAgent()}
          style={styles.webView}
          onLoadStart={() => setIsLoading(true)}
          onLoadEnd={() => setIsLoading(false)}
          onNavigationStateChange={handleNavigationStateChange}
          onMessage={handleMessage}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          startInLoadingState={true}
          scalesPageToFit={true}
          mixedContentMode="compatibility"
          allowsInlineMediaPlayback={true}
          mediaPlaybackRequiresUserAction={false}
        />

        {/* Loading overlay */}
        {isLoading && (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator size="large" color="#25D366" />
            <Text style={styles.loadingText}>Загружается...</Text>
          </View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 50,
    paddingBottom: 16,
    backgroundColor: '#1C1C1E',
  },
  closeButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  placeholder: {
    width: 40,
  },
  instructions: {
    padding: 16,
    backgroundColor: '#1C1C1E',
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  instructionText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  webView: {
    flex: 1,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#FFFFFF',
    marginTop: 16,
    fontSize: 16,
  },
});