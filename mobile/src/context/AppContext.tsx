import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AppContextType {
  serverUrl: string;
  isConfigured: boolean;
  loading: boolean;
  connectServer: (url: string) => Promise<{ success: boolean; error?: string }>;
  disconnectServer: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [serverUrl, setServerUrl] = useState<string>('');
  const [isConfigured, setIsConfigured] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadSavedServer();
  }, []);

  const loadSavedServer = async () => {
    try {
      const savedUrl = await AsyncStorage.getItem('warden_server_url');
      if (savedUrl && savedUrl.trim()) {
        setServerUrl(savedUrl.trim());
        setIsConfigured(true);
      }
    } catch (err) {
      console.error('[AppContext] Failed to load saved server URL:', err);
    } finally {
      setLoading(false);
    }
  };

  const normalizeUrl = (rawUrl: string): string => {
    let clean = rawUrl.trim();
    if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
      clean = 'http://' + clean;
    }
    // Remove trailing slashes
    clean = clean.replace(/\/+$/, '');

    // If no port specified and no path, check if it needs :22313
    try {
      const parsed = new URL(clean);
      if (!parsed.port && parsed.protocol === 'http:' && !parsed.hostname.includes(':')) {
        // If it's a domain/IP without custom port, default to 22313 unless 80/443
        if (parsed.hostname === 'localhost' || /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(parsed.hostname)) {
          parsed.port = '22313';
          clean = parsed.origin;
        }
      }
    } catch {
      // Fallback string check
      if (!clean.includes(':', 6)) {
        clean = `${clean}:22313`;
      }
    }

    return clean;
  };

  const connectServer = async (rawUrl: string): Promise<{ success: boolean; error?: string }> => {
    if (!rawUrl || !rawUrl.trim()) {
      return { success: false, error: 'Please enter a valid server IP or URL.' };
    }

    const cleanUrl = normalizeUrl(rawUrl);

    try {
      // Test connectivity with a 4-second timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const res = await fetch(`${cleanUrl}/api/v1/health`, {
        method: 'GET',
        signal: controller.signal,
      }).catch(async () => {
        // If /api/v1/health is blocked by auth/proxy, test root /
        return fetch(`${cleanUrl}/`, {
          method: 'GET',
          signal: controller.signal,
        });
      });

      clearTimeout(timeoutId);

      // Save to storage
      await AsyncStorage.setItem('warden_server_url', cleanUrl);
      setServerUrl(cleanUrl);
      setIsConfigured(true);

      return { success: true };
    } catch (err: any) {
      // Even if network ping fails, allow user to connect if they insist (e.g. adb reverse started right after)
      console.warn('[AppContext] Health check warning:', err.message);
      
      // Save anyway so the user can connect to localhost/LAN
      await AsyncStorage.setItem('warden_server_url', cleanUrl);
      setServerUrl(cleanUrl);
      setIsConfigured(true);

      return { success: true };
    }
  };

  const disconnectServer = async () => {
    try {
      await AsyncStorage.removeItem('warden_server_url');
      setServerUrl('');
      setIsConfigured(false);
    } catch (err) {
      console.error('[AppContext] Error clearing server:', err);
    }
  };

  return (
    <AppContext.Provider
      value={{
        serverUrl,
        isConfigured,
        loading,
        connectServer,
        disconnectServer,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
};
