import React from 'react';
import { View, Image, StyleSheet, StatusBar } from 'react-native';
import { AppProvider, useApp } from './src/context/AppContext';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { WardenWebViewScreen } from './src/screens/WardenWebViewScreen';

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
        <View style={styles.spinner} />
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
  },
  splashLogo: {
    width: 180,
    height: 32,
    marginBottom: 16,
  },
  spinner: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#1bd96a',
    borderTopColor: 'transparent',
  },
});
