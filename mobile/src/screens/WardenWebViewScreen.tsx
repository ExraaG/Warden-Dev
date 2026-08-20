import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  BackHandler,
  SafeAreaView,
  StatusBar,
  Alert,
} from 'react-native';
import { WebView } from 'react-native-webview';
import Svg, { Path, Rect, Circle } from 'react-native-svg';
import { useApp } from '../context/AppContext';

const INJECTED_ZOOM_LOCK_JS = `
(function() {
  var meta = document.querySelector('meta[name="viewport"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.name = 'viewport';
    document.getElementsByTagName('head')[0].appendChild(meta);
  }
  meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';

  // Disable pinch-to-zoom gestures
  document.addEventListener('gesturestart', function(e) {
    e.preventDefault();
  }, { passive: false });

  document.addEventListener('dblclick', function(e) {
    e.preventDefault();
  }, { passive: false });

  true;
})();
`;

const IconServerSwitch = () => (
  <Svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <Rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
    <Rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
    <Circle cx="6" cy="6" r="1" fill="#34d399" />
    <Circle cx="6" cy="18" r="1" fill="#34d399" />
  </Svg>
);

export const WardenWebViewScreen: React.FC = () => {
  const { serverUrl, disconnectServer } = useApp();
  const webViewRef = useRef<WebView>(null);
  const [canGoBack, setCanGoBack] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [hasError, setHasError] = useState<boolean>(false);
  const [errorDesc, setErrorDesc] = useState<string>('');

  // Handle Android hardware back button
  useEffect(() => {
    const onBackPress = () => {
      if (canGoBack && webViewRef.current) {
        webViewRef.current.goBack();
        return true;
      }
      return false;
    };

    const sub = BackHandler.addEventListener('hardwareBackPress', onBackPress);
    return () => sub.remove();
  }, [canGoBack]);

  const handleDisconnectPrompt = () => {
    Alert.alert(
      'Switch Server',
      `Currently connected to:\n${serverUrl}\n\nDo you want to disconnect and enter a different IP?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Disconnect',
          style: 'destructive',
          onPress: () => disconnectServer(),
        },
      ]
    );
  };

  const handleReload = () => {
    setHasError(false);
    setIsLoading(true);
    webViewRef.current?.reload();
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0d0e11" />

      {/* Embedded Fullscreen WebView */}
      {!hasError && (
        <WebView
          ref={webViewRef}
          source={{ uri: serverUrl }}
          style={styles.webView}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          injectedJavaScript={INJECTED_ZOOM_LOCK_JS}
          scalesPageToFit={false}
          setBuiltInZoomControls={false}
          setSupportZoom={false}
          textZoom={100}
          overScrollMode="never"
          bounces={false}
          showsHorizontalScrollIndicator={false}
          showsVerticalScrollIndicator={false}
          allowsBackForwardNavigationGestures={true}
          startInLoadingState={true}
          onNavigationStateChange={(navState) => {
            setCanGoBack(navState.canGoBack);
          }}
          onLoadStart={() => setIsLoading(true)}
          onLoadEnd={() => setIsLoading(false)}
          onError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            setIsLoading(false);
            setHasError(true);
            setErrorDesc(nativeEvent.description || 'Could not connect to server.');
          }}
          onHttpError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            if (nativeEvent.statusCode >= 500) {
              setHasError(true);
              setErrorDesc(`HTTP ${nativeEvent.statusCode} Server Error`);
            }
          }}
        />
      )}

      {/* Loading Overlay */}
      {isLoading && !hasError && (
        <View style={styles.loadingOverlay} pointerEvents="none">
          <ActivityIndicator size="large" color="#34d399" />
          <Text style={styles.loadingText}>CONNECTING TO WARDEN...</Text>
        </View>
      )}

      {/* Error Fallback Screen */}
      {hasError && (
        <View style={styles.errorContainer}>
          <View style={styles.errorCard}>
            <Text style={styles.errorTitle}>CONNECTION FAILED</Text>
            <Text style={styles.errorSub}>
              Could not reach Warden at {serverUrl}
            </Text>
            {errorDesc ? <Text style={styles.errorDetail}>{errorDesc}</Text> : null}

            <View style={styles.errorActions}>
              <TouchableOpacity style={styles.retryBtn} onPress={handleReload} activeOpacity={0.8}>
                <Text style={styles.retryBtnText}>RETRY CONNECTION</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.switchBtn} onPress={disconnectServer} activeOpacity={0.8}>
                <Text style={styles.switchBtnText}>CHANGE SERVER IP</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}

      {/* Subtle Bottom Switcher Bar */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.serverPill}
          onPress={handleDisconnectPrompt}
          activeOpacity={0.7}
        >
          <IconServerSwitch />
          <Text style={styles.serverPillText} numberOfLines={1}>
            {serverUrl.replace(/^https?:\/\//, '')}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0d0e11',
  },
  webView: {
    flex: 1,
    backgroundColor: '#0d0e11',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#0d0e11',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    zIndex: 10,
  },
  loadingText: {
    fontFamily: 'monospace',
    fontSize: 11,
    fontWeight: 'bold',
    color: '#64748b',
    letterSpacing: 1,
  },
  errorContainer: {
    flex: 1,
    backgroundColor: '#0d0e11',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  errorCard: {
    width: '100%',
    maxWidth: 380,
    backgroundColor: '#13161c',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#222734',
    padding: 24,
    alignItems: 'center',
  },
  errorTitle: {
    fontFamily: 'monospace',
    fontSize: 16,
    fontWeight: '900',
    color: '#ef4444',
    letterSpacing: 1,
    marginBottom: 8,
  },
  errorSub: {
    fontFamily: 'monospace',
    fontSize: 12,
    color: '#94a3b8',
    textAlign: 'center',
    lineHeight: 16,
    marginBottom: 10,
  },
  errorDetail: {
    fontFamily: 'monospace',
    fontSize: 10,
    color: '#f87171',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    padding: 8,
    borderRadius: 6,
    marginBottom: 16,
    width: '100%',
    textAlign: 'center',
  },
  errorActions: {
    width: '100%',
    gap: 10,
    marginTop: 8,
  },
  retryBtn: {
    backgroundColor: '#10b981',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  retryBtnText: {
    fontFamily: 'monospace',
    fontSize: 12,
    fontWeight: '900',
    color: '#090d16',
    letterSpacing: 0.5,
  },
  switchBtn: {
    backgroundColor: '#1e293b',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  switchBtnText: {
    fontFamily: 'monospace',
    fontSize: 11,
    fontWeight: 'bold',
    color: '#cbd5e1',
    letterSpacing: 0.5,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 4,
    right: 12,
    zIndex: 20,
  },
  serverPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(19, 22, 28, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(34, 39, 52, 0.9)',
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.4,
    shadowRadius: 4,
    elevation: 3,
  },
  serverPillText: {
    fontFamily: 'monospace',
    fontSize: 9,
    fontWeight: 'bold',
    color: '#94a3b8',
    maxWidth: 160,
  },
});
