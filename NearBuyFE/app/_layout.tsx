import { Stack } from 'expo-router';
import React, { useEffect } from 'react';
import { StyleSheet } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as Utils from '../utils/utils';

export default function RootLayout() {
  useEffect(() => {
    console.log('RootLayout mounted, starting background location...');
    Utils.startBackgroundLocation();
    console.log('Background location started');
  
    return () => {
      Utils.stopBackgroundLocation(); 
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