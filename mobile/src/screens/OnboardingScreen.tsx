import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';
import { useApp } from '../context/AppContext';

const WardenLogoSvg = ({ size = 48, color = '#34d399' }: { size?: number; color?: string }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <Rect x="3" y="5" width="18" height="14" rx="3" />
    <Path d="M7 10h2v4H7z" fill={color} />
    <Path d="M15 10h2v4h-2z" fill={color} />
    <Path d="M10 14h4" />
    <Path d="M2 10v4" />
    <Path d="M22 10v4" />
  </Svg>
);

export const OnboardingScreen: React.FC = () => {
  const { connectServer } = useApp();
  const [url, setUrl] = useState<string>('http://localhost:22313');
  const [connecting, setConnecting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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

  const handleApplyPreset = (presetUrl: string) => {
    setUrl(presetUrl);
    setErrorMsg(null);
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        {/* Header Branding (Matches Web AuthView) */}
        <View style={styles.headerContainer}>
          <View style={styles.iconBox}>
            <WardenLogoSvg size={36} color="#34d399" />
          </View>
          <Text style={styles.brandTitle}>WARDEN</Text>
          <Text style={styles.brandSubtitle}>MINECRAFT SERVER ORCHESTRATOR</Text>
          <View style={styles.versionBadge}>
            <Text style={styles.versionBadgeText}>STANDALONE CLIENT</Text>
          </View>
        </View>

        {/* Main Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>SERVER CONNECTION</Text>
            <Text style={styles.cardSubtitle}>
              Enter your Warden server endpoint or host IP address to launch.
            </Text>
          </View>

          {errorMsg && (
            <View style={styles.errorBox}>
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
              placeholderTextColor="#475569"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />

            {/* Presets */}
            <View style={styles.presetContainer}>
              <TouchableOpacity
                style={[styles.presetChip, url === 'http://localhost:22313' && styles.presetChipActive]}
                onPress={() => handleApplyPreset('http://localhost:22313')}
                activeOpacity={0.7}
              >
                <Text style={[styles.presetText, url === 'http://localhost:22313' && styles.presetTextActive]}>
                  Localhost (USB)
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.presetChip, url === 'http://10.0.2.2:22313' && styles.presetChipActive]}
                onPress={() => handleApplyPreset('http://10.0.2.2:22313')}
                activeOpacity={0.7}
              >
                <Text style={[styles.presetText, url === 'http://10.0.2.2:22313' && styles.presetTextActive]}>
                  Emulator (10.0.2.2)
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.presetChip, url.includes('192.168.') && styles.presetChipActive]}
                onPress={() => handleApplyPreset('http://192.168.1.231:22313')}
                activeOpacity={0.7}
              >
                <Text style={[styles.presetText, url.includes('192.168.') && styles.presetTextActive]}>
                  LAN Host (:22313)
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <TouchableOpacity
            style={[styles.submitBtn, connecting && styles.submitBtnDisabled]}
            onPress={handleConnect}
            disabled={connecting}
            activeOpacity={0.8}
          >
            {connecting ? (
              <ActivityIndicator size="small" color="#090d16" />
            ) : (
              <Text style={styles.submitBtnText}>CONNECT &amp; LAUNCH</Text>
            )}
          </TouchableOpacity>

          <View style={styles.cardFooter}>
            <Text style={styles.footerNote}>
              Warden opens directly inside the app with full live console, modpacks, players, and 2FA authentication.
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
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
    padding: 20,
    paddingVertical: 36,
  },
  headerContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  iconBox: {
    width: 64,
    height: 64,
    borderRadius: 16,
    backgroundColor: 'rgba(52, 211, 153, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(52, 211, 153, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  brandTitle: {
    fontFamily: 'monospace',
    fontSize: 24,
    fontWeight: '900',
    color: '#f8fafc',
    letterSpacing: 2,
  },
  brandSubtitle: {
    fontFamily: 'monospace',
    fontSize: 10,
    color: '#34d399',
    letterSpacing: 1.2,
    marginTop: 4,
    fontWeight: 'bold',
  },
  versionBadge: {
    marginTop: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: '#13161c',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#222734',
  },
  versionBadgeText: {
    fontFamily: 'monospace',
    fontSize: 9,
    color: '#64748b',
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  card: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: '#13161c',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#222734',
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  cardHeader: {
    marginBottom: 20,
  },
  cardTitle: {
    fontFamily: 'monospace',
    fontSize: 14,
    fontWeight: '900',
    color: '#f8fafc',
    letterSpacing: 1,
  },
  cardSubtitle: {
    fontFamily: 'monospace',
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 4,
    lineHeight: 16,
  },
  errorBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.4)',
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
  },
  errorText: {
    fontFamily: 'monospace',
    fontSize: 11,
    color: '#fca5a5',
    lineHeight: 15,
  },
  formGroup: {
    marginBottom: 20,
  },
  label: {
    fontFamily: 'monospace',
    fontSize: 11,
    fontWeight: 'bold',
    color: '#cbd5e1',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#222734',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontFamily: 'monospace',
    fontSize: 13,
    color: '#f8fafc',
  },
  presetContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  presetChip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: '#090d16',
    borderWidth: 1,
    borderColor: '#222734',
  },
  presetChipActive: {
    backgroundColor: 'rgba(52, 211, 153, 0.12)',
    borderColor: '#34d399',
  },
  presetText: {
    fontFamily: 'monospace',
    fontSize: 10,
    color: '#64748b',
    fontWeight: 'bold',
  },
  presetTextActive: {
    color: '#34d399',
  },
  submitBtn: {
    backgroundColor: '#10b981',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#10b981',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 4,
  },
  submitBtnDisabled: {
    opacity: 0.7,
  },
  submitBtnText: {
    fontFamily: 'monospace',
    fontSize: 13,
    fontWeight: '900',
    color: '#090d16',
    letterSpacing: 1,
  },
  cardFooter: {
    marginTop: 18,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  footerNote: {
    fontFamily: 'monospace',
    fontSize: 10,
    color: '#64748b',
    lineHeight: 14,
    textAlign: 'center',
  },
});
