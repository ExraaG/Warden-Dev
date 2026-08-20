import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Image,
  StatusBar,
} from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { useApp } from '../context/AppContext';
import { WardenSpinner } from '../components/ui/WardenSpinner';

const IconCheck = ({ size = 14, color = '#0d0e11' }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <Path d="M20 6L9 17l-5-5" />
  </Svg>
);

const IconAlert = ({ size = 16, color = '#f87171' }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <Path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <Path d="M12 9v4" />
    <Path d="M12 17h.01" />
  </Svg>
);

export const OnboardingScreen: React.FC = () => {
  const { serverUrl, connectServer } = useApp();
  const [url, setUrl] = useState<string>(serverUrl || 'http://localhost:22313');
  const [connecting, setConnecting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (serverUrl) {
      setUrl(serverUrl);
    }
  }, [serverUrl]);

  const handleConnect = async () => {
    if (!url.trim()) {
      setErrorMsg('Please enter your Warden Server URL or IP address.');
      return;
    }

    setErrorMsg(null);
    setConnecting(true);
    const result = await connectServer(url.trim());
    setConnecting(false);

    if (!result.success && result.error) {
      setErrorMsg(result.error);
    }
  };

  return (
    <View style={styles.flex}>
      <StatusBar barStyle="light-content" backgroundColor="#0d0e11" translucent={false} />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
          {/* Official Warden Logo */}
          <View style={styles.logoContainer}>
            <Image
              source={require('../assets/warden_logo.png')}
              style={styles.logoImage}
              resizeMode="contain"
            />
          </View>

          {/* Card Container */}
          <View style={styles.card}>
            {errorMsg && (
              <View style={styles.errorBox}>
                <IconAlert size={16} color="#f87171" />
                <Text style={styles.errorText}>{errorMsg}</Text>
              </View>
            )}

            <View style={styles.formGroup}>
              <Text style={styles.label}>SERVER ENDPOINT / IP</Text>
              <TextInput
                style={styles.input}
                value={url}
                onChangeText={(text) => {
                  setUrl(text);
                  if (errorMsg) setErrorMsg(null);
                }}
                placeholder="http://localhost:22313"
                placeholderTextColor="#64748b"
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="url"
              />
            </View>

            {/* Primary Action Button */}
            <TouchableOpacity
              style={[styles.primaryButton, connecting && styles.buttonDisabled]}
              onPress={handleConnect}
              disabled={connecting}
              activeOpacity={0.85}
            >
              {connecting ? (
                <WardenSpinner size={16} color="#0d0e11" />
              ) : (
                <>
                  <IconCheck size={14} color="#0d0e11" />
                  <Text style={styles.buttonText}>CONNECT &amp; LAUNCH</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
};

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: '#0d0e11',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 28,
  },
  logoImage: {
    width: 220,
    height: 36,
  },
  card: {
    width: '100%',
    maxWidth: 425,
    backgroundColor: '#13161c',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#232733',
    padding: 24,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: 'rgba(69, 10, 10, 0.5)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.5)',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 16,
  },
  errorText: {
    flex: 1,
    fontFamily: 'Minecraft',
    fontSize: 11,
    color: '#fca5a5',
    lineHeight: 15,
  },
  formGroup: {
    marginBottom: 20,
  },
  label: {
    fontFamily: 'Minecraft',
    fontSize: 11,
    color: '#cbd5e1',
    marginBottom: 6,
    letterSpacing: 0.5,
  },
  input: {
    width: '100%',
    height: 40,
    backgroundColor: '#0d0e11',
    borderWidth: 1,
    borderColor: '#232733',
    borderRadius: 6,
    paddingHorizontal: 12,
    fontFamily: 'Minecraft',
    fontSize: 13,
    color: '#f8fafc',
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    width: '100%',
    height: 40,
    backgroundColor: '#1bd96a',
    borderRadius: 6,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    fontFamily: 'Minecraft',
    fontSize: 12,
    color: '#0d0e11',
    letterSpacing: 0.5,
  },
});
