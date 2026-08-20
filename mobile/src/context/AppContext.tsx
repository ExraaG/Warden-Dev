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
  const [serverUrl, setServerUrl] = useState<string>('http://localhost:22313');
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
      }
    } catch (err) {
      console.error('[AppContext] Error loading saved server URL:', err);
    } finally {
      setLoading(false);
    }
  };

  const normalizeUrl = (rawUrl: string): string => {
    let clean = rawUrl.trim();
    if (!clean) return 'http://localhost:22313';

    // Remove any trailing slashes
    clean = clean.replace(/\/+$/, '');

    // If no protocol, default to http://
    const hasProtocol = clean.startsWith('http://') || clean.startsWith('https://');
    if (!hasProtocol) {
      clean = 'http://' + clean;
    }

    // Check if port is specified
    const match = clean.match(/^(https?:\/\/)(.*)$/);
    if (match) {
      const proto = match[1];
      let hostPart = match[2];

      // If hostPart does not contain a port (e.g. 192.168.1.230 or localhost)
      if (!hostPart.includes(':')) {
        hostPart = `${hostPart}:22313`;
      }
      clean = `${proto}${hostPart}`;
    }

    return clean;
  };

  const connectServer = async (rawUrl: string): Promise<{ success: boolean; error?: string }> => {
    if (!rawUrl || !rawUrl.trim()) {
      return { success: false, error: 'Please enter a valid server IP or URL.' };
    }

    const cleanUrl = normalizeUrl(rawUrl);

    try {
      await AsyncStorage.setItem('warden_server_url', cleanUrl);
      setServerUrl(cleanUrl);
      setIsConfigured(true);
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to save server URL.' };
    }
  };

  const disconnectServer = async () => {
    setIsConfigured(false);
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
