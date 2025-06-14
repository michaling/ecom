import { Platform, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import * as Location from 'expo-location';


export const currentPath = 
          //'http://10.0.2.2:8000/' // for android emulator
          'http://10.0.0.49:8000/' // for phone via USB / expo go app
          //'http://localhost:8000/' // for web
          ;

// Platform-aware save function
export const save = async (key: string, value: string) => {
    try {
      if (Platform.OS === 'web') {
        await AsyncStorage.setItem(key, value);
      } else {
        await SecureStore.setItemAsync(key, value);
      }
    } catch (error) {
      console.error("Storage error:", error);
    }
  };
  
  // Platform-aware get function
  export const getValueFor = async (key: string): Promise<string | null> => {
    try {
      if (Platform.OS === 'web') {
        return await AsyncStorage.getItem(key);
      } else {
        return await SecureStore.getItemAsync(key);
      }
    } catch (error) {
      console.error("Error retrieving data:", error);
      return null;
    }
  };

  export async function deleteValueFor(key: string) {
    try {
      await SecureStore.deleteItemAsync(key);
    } catch (error) {
      console.error('SecureStore deletion error:', error);
    }
  }

  export const requestForegroundLocationPermission = async () => {
    const { status } = await Location.getForegroundPermissionsAsync();
    if (status !== 'granted') {
      const { status: newStatus } = await Location.requestForegroundPermissionsAsync();
      if (newStatus !== 'granted') {
        Alert.alert("Location permission is required for geo alerts.");
        return false;
      }
    }
    return true;
  };

  export const requestBackgroundLocationPermission = async () => {
    const { status } = await Location.getBackgroundPermissionsAsync();
    if (status !== 'granted') {
      const { status: newStatus } = await Location.requestBackgroundPermissionsAsync();
      if (newStatus !== 'granted') {
        Alert.alert("Location permission is required for geo alerts.");
        return false;
      }
    }
    return true;
  };

  export const wasAskedForBgPermission = async (): Promise<boolean> => {
    const val = await getValueFor('asked_bg_perm');
    return val === 'true';
  };
  
  export const markAskedForBgPermission = async (): Promise<void> => {
    await save('asked_bg_perm', 'true');
  };