import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  BackHandler,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { WebView } from 'react-native-webview';
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

export const WardenWebViewScreen: React.FC = () => {
  const { serverUrl, disconnectServer } = useApp();
  const webViewRef = useRef<WebView>(null);
  const [canGoBack, setCanGoBack] = useState<boolean>(false);
  const [hasError, setHasError] = useState<boolean>(false);
  const [errorDesc, setErrorDesc] = useState<string>('');

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

  const handleReload = () => {
    setHasError(false);
    webViewRef.current?.reload();
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0d0e11" translucent={false} />

      {/* Embedded Fullscreen Responsive WebView */}
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
          mixedContentMode="always"
          onNavigationStateChange={(navState) => {
            setCanGoBack(navState.canGoBack);
          }}
          onError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
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

      {/* Error Fallback Screen if Connection Fails */}
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
                <Text style={styles.retryBtnText}>RETRY</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.switchBtn} onPress={disconnectServer} activeOpacity={0.8}>
                <Text style={styles.switchBtnText}>CHANGE SERVER IP</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}
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
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#232733',
    padding: 24,
    alignItems: 'center',
  },
  errorTitle: {
    fontFamily: 'Minecraft',
    fontSize: 14,
    color: '#ef4444',
    letterSpacing: 1,
    marginBottom: 8,
  },
  errorSub: {
    fontFamily: 'Minecraft',
    fontSize: 11,
    color: '#94a3b8',
    textAlign: 'center',
    lineHeight: 16,
    marginBottom: 10,
  },
  errorDetail: {
    fontFamily: 'Minecraft',
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
    backgroundColor: '#1bd96a',
    borderRadius: 6,
    paddingVertical: 12,
    alignItems: 'center',
  },
  retryBtnText: {
    fontFamily: 'Minecraft',
    fontSize: 12,
    color: '#0d0e11',
    letterSpacing: 0.5,
  },
  switchBtn: {
    backgroundColor: '#191c24',
    borderRadius: 6,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#232733',
  },
  switchBtnText: {
    fontFamily: 'Minecraft',
    fontSize: 11,
    color: '#cbd5e1',
    letterSpacing: 0.5,
  },
});
