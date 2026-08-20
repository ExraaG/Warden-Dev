import React from 'react';
import { View, Image, StyleSheet, StatusBar } from 'react-native';
import { AppProvider, useApp } from './src/context/AppContext';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { WardenWebViewScreen } from './src/screens/WardenWebViewScreen';
import { WardenSpinner } from './src/components/ui/WardenSpinner';

function MainApp() {
  const { isConfigured, loading, serverUrl } = useApp();

  if (loading) {
    return (
      <View style={styles.splashContainer}>
        <StatusBar barStyle="light-content" backgroundColor="#0d0e11" />
        <Image
          source={require('./src/assets/warden_logo.png')}
          style={styles.splashLogo}
          resizeMode="contain"
        />
        <WardenSpinner size={20} color="#1bd96a" />
      </View>
    );
  }

  if (!isConfigured || !serverUrl) {
    return (
      <>
        <StatusBar barStyle="light-content" backgroundColor="#0d0e11" />
        <OnboardingScreen />
      </>
    );
  }

  return (
    <>
      <StatusBar barStyle="light-content" backgroundColor="#0d0e11" />
      <WardenWebViewScreen />
    </>
  );
}

export default function App() {
  return (
    <AppProvider>
      <MainApp />
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  splashContainer: {
    flex: 1,
    backgroundColor: '#0d0e11',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 16,
  },
  splashLogo: {
    width: 180,
    height: 32,
  },
});
