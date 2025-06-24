// app/_layout.tsx

import { Stack } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import React from 'react';
import { useEffect } from 'react';
import { StyleSheet } from 'react-native';
import * as Utils from '../utils/utils'; 

export default function RootLayout() {
  useEffect(() => {
    Utils.startBackgroundLocation();
  
    return () => {
      Utils.stopBackgroundLocation(); // optional cleanup
    };
  }, []);

  return (
    <GestureHandlerRootView style={styles.container}>
      <SafeAreaProvider>
        <Stack screenOptions={{ headerShown: false }} />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});