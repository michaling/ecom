import { Platform, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import * as Location from 'expo-location';
import { LocationObject } from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { TaskManagerTaskBody } from 'expo-task-manager';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';

const LOCATION_TASK_NAME = 'background-location-task';
const POLLING_INTERVAL_MS = 1_000; // 60 seconds
//let locationPollingInterval: number | null = null;

export const currentPath = 
          //'http://10.0.2.2:8000/' // for android emulator
          'http://10.0.0.49:8000/' // for phone via USB / expo go app (take ip from ipconfig)
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


  TaskManager.defineTask(LOCATION_TASK_NAME, async (taskBody: TaskManagerTaskBody) => {
    console.log('[BG LOCATION TASK] running...');
    const { data, error } = taskBody;
  
    if (error) {
      console.error('[TASK ERROR]', error);
      return;
    }
  
    if (data && Array.isArray((data as any).locations)) {
      const locations = (data as any).locations as LocationObject[];
      const loc = locations[0];
      if (loc) {
        console.log(`[BG LOCATION]: ${loc.coords.latitude}, ${loc.coords.longitude}`);
        // Send to backend here
      }
    }
  });
  console.log('[TASK] Background-location task has been defined'); 

export const startBackgroundLocation = async () => {
  const granted = await requestBackgroundLocationPermission();
  if (!granted) return;
  //console.log(await Location.isBackgroundLocationAvailableAsync())

  const hasStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (!hasStarted) {
    console.log('[BG LOCATION] Starting...');
    await Location.startLocationUpdatesAsync(LOCATION_TASK_NAME, {
      accuracy: Location.Accuracy.Highest,
      timeInterval: POLLING_INTERVAL_MS, // Minimum time between updates in ms
      distanceInterval: 0, // Minimum distance between updates in meters
      showsBackgroundLocationIndicator: true,
      foregroundService: {
        notificationTitle: 'NearBuy is running',
        notificationBody: 'Tracking your location for geo alerts',
        notificationColor: '#007AFF',
      },
    });
    console.log('[BG LOCATION] Started');
  }
};

export const stopBackgroundLocation = async () => {
  const hasStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (hasStarted) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK_NAME);
    console.log('[BG LOCATION] Stopped');
  }
};
  
export async function registerForPushNotificationsAsync(): Promise<string | null> {
  let token: string | null = null;

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    Alert.alert('Permission denied', 'Enable push notifications in settings to receive alerts.');
    return null;
  }

  token = (await Notifications.getExpoPushTokenAsync()).data;
  console.log('[PUSH TOKEN]', token);

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  return token;
}