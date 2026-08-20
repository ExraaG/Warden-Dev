import React from 'react';
import { View, Text, StyleSheet, StatusBar, ActivityIndicator } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';
import { AppProvider, useApp } from './src/context/AppContext';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { WardenWebViewScreen } from './src/screens/WardenWebViewScreen';

const WardenLogoSvg = ({ size = 44, color = '#34d399' }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <Rect x="3" y="5" width="18" height="14" rx="3" />
    <Path d="M7 10h2v4H7z" fill={color} />
    <Path d="M15 10h2v4h-2z" fill={color} />
    <Path d="M10 14h4" />
    <Path d="M2 10v4" />
    <Path d="M22 10v4" />
  </Svg>
);

function MainApp() {
  const { isConfigured, loading, serverUrl } = useApp();

  if (loading) {
    return (
      <View style={styles.splashContainer}>
        <StatusBar barStyle="light-content" backgroundColor="#0d0e11" />
        <View style={styles.splashIconBox}>
          <WardenLogoSvg size={44} color="#34d399" />
        </View>
        <Text style={styles.splashTitle}>WARDEN</Text>
        <Text style={styles.splashSub}>MINECRAFT SERVER ORCHESTRATOR</Text>
        <ActivityIndicator size="small" color="#34d399" style={styles.loader} />
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
  splashIconBox: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: 'rgba(52, 211, 153, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(52, 211, 153, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  splashTitle: {
    fontFamily: 'monospace',
    fontSize: 26,
    fontWeight: '900',
    color: '#f8fafc',
    letterSpacing: 2,
  },
  splashSub: {
    fontFamily: 'monospace',
    fontSize: 10,
    color: '#34d399',
    letterSpacing: 1.2,
    marginTop: 4,
    fontWeight: 'bold',
  },
  loader: {
    marginTop: 24,
  },
});
