import { Platform, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import * as Location from 'expo-location';
import { LocationObject } from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { TaskManagerTaskBody } from 'expo-task-manager';

const LOCATION_TASK_NAME = 'background-location-task';
const POLLING_INTERVAL_MS = 60_000; // 60 seconds
//let locationPollingInterval: number | null = null;

export const currentPath = 
          //'http://10.0.2.2:8000/' // for android emulator
          'http://192.168.1.172:8000/' // for phone via USB / expo go app
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

export const startBackgroundLocation = async () => {
  const granted = await requestBackgroundLocationPermission();
  if (!granted) return;

  const hasStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (!hasStarted) {
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
  
// export const startLocationPolling = () => {
//   console.log('[STARTING LOCATION POLLING]');
//   if (locationPollingInterval) return;

//   locationPollingInterval = setInterval(async () => {
//     try {
//       const { status } = await Location.getBackgroundPermissionsAsync();
//       if (status !== 'granted') return;

//       const loc = await Location.getCurrentPositionAsync({});
//       console.log('[POLLING] Location:', loc.coords);

//       // You can send this to the backend here (POST request)

//     } catch (err) {
//       console.error('[POLLING ERROR]', err);
//     }
//   }, POLLING_INTERVAL_MS);
// };

// export const stopLocationPolling = () => {
//   if (locationPollingInterval !== null) {
//     clearInterval(locationPollingInterval);
//     locationPollingInterval = null;
//   }
// };