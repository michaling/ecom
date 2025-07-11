
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
const POLLING_INTERVAL_MS = 120_000; // every 2 minutes
let lastTimestamp = 0;

export const currentPath =
  'http://192.168.1.185:8000/' // for android emulator
  // 'http://10.0.0.49:8000/' // for phone via USB / expo go app
  // 'http://localhost:8000/' // for web
  ;


// ───────────────────────── Platform-aware save/get/delete functions ─────────────────────────

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

export const deleteValueFor = async (key: string) => {
  try {
    await SecureStore.deleteItemAsync(key);
  } catch (error) {
    console.error('SecureStore deletion error:', error);
  }
};

// ───────────────────────── Location permission helpers ─────────────────────────
export const requestForegroundLocationPermission = async (): Promise<boolean> => {
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

export const requestBackgroundLocationPermission = async (): Promise<boolean> => {
  const { status } = await Location.getBackgroundPermissionsAsync();
  console.log('Background location permission status:', status);
  if (status !== 'granted') {
    const { status: newStatus } = await Location.requestBackgroundPermissionsAsync();
    if (newStatus !== 'granted') {
      Alert.alert(
        "Permission required",
        "Background location permission is required for geo alerts."
      );
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


export const ensureFullLocationPermissions = async (): Promise<boolean> => {
  const fgStatus = await Location.getForegroundPermissionsAsync();
  const bgStatus = await Location.getBackgroundPermissionsAsync();

  if (fgStatus.status === 'granted' && bgStatus.status === 'granted') {
    return true;
  }

  const fgGranted = await requestForegroundLocationPermission();
  if (!fgGranted) {
    console.warn("User denied foreground permission");
    return false;
  }

  const bgGranted = await requestBackgroundLocationPermission();
  if (!bgGranted) {
    console.warn("User denied background permission");
    return false;
  }

  return true;
};

// ───────────────────────── Background Location Task ─────────────────────────
TaskManager.defineTask(
  LOCATION_TASK_NAME,
  async ({ data, error }: TaskManagerTaskBody) => {
    try {
      if (error) throw error;
      const locs = (data as { locations?: LocationObject[] })?.locations;
      if (!locs?.length) return;
      const loc = locs[0];
      if (!loc || loc.timestamp - lastTimestamp < 5_000) return;
      lastTimestamp = loc.timestamp;
      console.log(`[BG LOCATION]: ${loc.coords.latitude}, ${loc.coords.longitude}`);
      await sendLocationToBackend(loc.coords.latitude, loc.coords.longitude);
    } catch (e) {
      console.log('[TASK ERROR]', e);
    }
  }
);

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
    console.log('[location_update] Success');
  } catch (e: any) {
    console.log('[location_update] ', e?.response?.data || e);
  }
};

export const startBackgroundLocation = async () => {
  const granted = await requestBackgroundLocationPermission();
  if (!granted) return;

  const hasStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (!hasStarted) {
    await Location.startLocationUpdatesAsync(LOCATION_TASK_NAME, {
      accuracy: Location.Accuracy.Highest,
      timeInterval: POLLING_INTERVAL_MS,
      distanceInterval: 0,
      showsBackgroundLocationIndicator: true,
      foregroundService: {
        notificationTitle: 'NearBuy is running',
        notificationBody: 'Tracking your location for geo alerts',
        notificationColor: '#007AFF',
      },
    });
  }
};

export const stopBackgroundLocation = async () => {
  const hasStarted = await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK_NAME);
  if (hasStarted) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK_NAME);
  }
};

// ───────────────────────── FCM-V1 Push Registration ─────────────────────────

export async function registerForPushNotificationsAsync(): Promise<string | null> {
  // 1) Ask permissions
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') {
    Alert.alert('Permission denied', 'Enable push notifications in settings.');
    return null;
  }

  // 2) Get the *FCM* device token instead of Expo token
  let token: string | null = null;
  try {
    const deviceTokenData = await Notifications.getDevicePushTokenAsync();
    token = deviceTokenData.data;
  } catch (err) {
    return null;
  }

  // 3) Send it to your backend
  try {
    const accessToken = await getValueFor('access_token');
    if (accessToken && token) {
      await axios.post(
        `${currentPath}device_token`,
        { expo_push_token: token },
        { headers: { token: accessToken } }
      );
    }
  } catch (err) {
    console.log('[REGISTER PUSH] Failed to send token to backend:', err);
  }

  // 4) Create Android channel if needed
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

// Local notifications
export const sendNotification = async (title: string, body: string) => {
  try {
    const perm = await Notifications.getPermissionsAsync();
    if (perm.status !== 'granted') return;

    await Notifications.scheduleNotificationAsync({
      content: { title, body, sound: 'default' },
      trigger: { seconds: 1 } as any,
    });
  } catch (err) {
    console.log('[sendNotification] Failed:', err);
  }
};
