import React from 'react';
import { View, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';

// Import screens
import AuthScreen from './auth';
import DashboardScreen from './dashboard';
import AccountsScreen from './accounts';
import TemplatesScreen from './templates';
import RecipientsScreen from './recipients';
import JobsScreen from './jobs';
import SettingsScreen from './settings';

// Auth context
import { AuthProvider, useAuth } from '../contexts/AuthContext';

// Tab Navigator
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Tab = createBottomTabNavigator();

// Main Tab Navigator
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          if (route.name === 'Dashboard') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Accounts') {
            iconName = focused ? 'person' : 'person-outline';
          } else if (route.name === 'Templates') {
            iconName = focused ? 'document-text' : 'document-text-outline';
          } else if (route.name === 'Recipients') {
            iconName = focused ? 'people' : 'people-outline';
          } else if (route.name === 'Jobs') {
            iconName = focused ? 'send' : 'send-outline';
          } else if (route.name === 'Settings') {
            iconName = focused ? 'settings' : 'settings-outline';
          } else {
            iconName = 'help-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#25D366',
        tabBarInactiveTintColor: '#8E8E93',
        tabBarStyle: {
          backgroundColor: '#1C1C1E',
          borderTopColor: '#2C2C2E',
        },
        headerStyle: {
          backgroundColor: '#1C1C1E',
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'Главная' }} />
      <Tab.Screen name="Accounts" component={AccountsScreen} options={{ title: 'Аккаунты' }} />
      <Tab.Screen name="Templates" component={TemplatesScreen} options={{ title: 'Шаблоны' }} />
      <Tab.Screen name="Recipients" component={RecipientsScreen} options={{ title: 'Получатели' }} />
      <Tab.Screen name="Jobs" component={JobsScreen} options={{ title: 'Рассылки' }} />
      <Tab.Screen name="Settings" component={SettingsScreen} options={{ title: 'Настройки' }} />
    </Tab.Navigator>
  );
}

// App Navigator
function AppNavigator() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        {/* Loading spinner can be added here */}
      </View>
    );
  }

  if (isAuthenticated) {
    return <MainTabs />;
  } else {
    return <AuthScreen />;
  }
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <View style={styles.container}>
          <StatusBar style="light" backgroundColor="#000000" />
          <AppNavigator />
        </View>
      </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
});