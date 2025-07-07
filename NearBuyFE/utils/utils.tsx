import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import * as Location from 'expo-location';
import { LocationObject } from 'expo-location';
import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';
import * as TaskManager from 'expo-task-manager';
import { TaskManagerTaskBody } from 'expo-task-manager';
import { Alert, Platform } from 'react-native';

const LOCATION_TASK_NAME = 'background-location-task';
const POLLING_INTERVAL_MS = 60_000; // 60 seconds
let lastTimestamp = 0; 

export const currentPath = 
          'http://192.168.56.1:8000/' // for android emulator
          //'http://10.0.0.49:8000/' // for phone via USB / expo go app (take ip from ipconfig)
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

  // Location permission functions
  export const requestForegroundLocationPermission = async () => {
    const { status } = await Location.getForegroundPermissionsAsync();
    if (status !== 'granted') {
      const { status: newStatus } = await Location.requestForegroundPermissionsAsync();
      if (newStatus !== 'granted') {
        console.log("Foreground location permission not granted");
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
        console.log("Backdround location permission not granted");
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

// Location polling task and functions

TaskManager.defineTask(LOCATION_TASK_NAME, async ({ data, error }: TaskManagerTaskBody) => {
  try {
    if (error) throw error;
    if (!(data as { locations?: LocationObject[] })?.locations?.length) return;

    const loc = ((data as { locations?: LocationObject[] }).locations || [])[0];
    if (!loc || loc.timestamp - lastTimestamp < 5_000) return;
    lastTimestamp = loc.timestamp;
    console.log(`[BG LOCATION]: ${loc.coords.latitude}, ${loc.coords.longitude}`);
    sendLocationToBackend(loc.coords.latitude, loc.coords.longitude)
      .catch(e => console.log('[location_update]', e?.response?.data || e));
      lastTimestamp = loc.timestamp;
    } catch (e) {
    console.log('[TASK ERROR]', e);
  }
});

  export const sendLocationToBackend = async (lat: number, lon: number) => {
    const user_id = await getValueFor('user_id');
    const access = await getValueFor('access_token');
    if (!user_id || !access) return;
  
    try {
      console.log(`[location_update] Sending location: ${lat}, ${lon}`);
      const res = await axios.post(
        `${currentPath}location_update`,
        {
          user_id,
          latitude: lat,
          longitude: lon,
          timestamp: new Date().toISOString(),
        },
        { headers: { token: access } }
      );
  
      const alerts = res.data?.alerts || [];
      for (const alert of alerts) {
        const shown = alert.items.slice(0, 3);
        const more = alert.items.length - shown.length;
        const body = `You’re near a store that may have: ${shown.join(', ')}${more > 0 ? ', and more from your shopping lists' : ''}`;
        await sendNotification(`${alert.store_name} has your items!`, body);
      }
  
    } catch (e: any) {
      console.log('[location_update] ', e?.response?.data || e);
    }
  };

export const startBackgroundLocation = async () => {
  const granted = await requestBackgroundLocationPermission();
  if (!granted) return;
  //console.log(await Location.isBackgroundLocationAvailableAsync())

  const hasStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (!hasStarted) {
    //console.log('[BG LOCATION] Starting...');
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
    //console.log('[BG LOCATIO/N] Started');
  }
};

export const stopBackgroundLocation = async () => {
  const hasStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (hasStarted) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK_NAME);
    //console.log('[BG LOCATION] Stopped');
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

  try {
    const expoTokenData = await Notifications.getExpoPushTokenAsync();
    token = expoTokenData.data;
    console.log('[PUSH TOKEN]', token);
  } catch (err) {
    console.error('[PUSH TOKEN] Could not fetch:', err);
    return null;
  }

  try {
    const accessToken = await getValueFor('access_token');
    if (accessToken && token) {
      await axios.post(`${currentPath}device_token`, {
        expo_push_token: token,
      }, {
        headers: { token: accessToken },
      });
    }
  } catch (err) {
    console.error('[REGISTER PUSH] Failed to send token to backend:', err);
  }

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

// Notification functions
export const sendNotification = async (title: string, body: string) => {
  try {
    const perm = await Notifications.getPermissionsAsync();
    if (perm.status !== 'granted') return;

    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        sound: 'default',
      },
      trigger: {
        seconds: 1,
      } as any,
    });
  } catch (err) {
    console.error('[sendNotification] Failed:', err);
  }
};
