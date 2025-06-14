import { Stack } from 'expo-router';
import { useEffect } from 'react';
import * as Location from 'expo-location';
import axios from 'axios';
import * as Utils from '../../utils/utils';

useEffect(() => {
  const sendLocation = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      console.warn('Location permission denied');
      return;
    }

    const location = await Location.getCurrentPositionAsync({});
    const token = await Utils.getValueFor('access_token');
    if (!token) return;

    await axios.post(`${Utils.currentPath}geo_alert/update_location`, {
      lat: location.coords.latitude,
      lng: location.coords.longitude,
    }, {
      headers: { token }
    });
  };

  const interval = setInterval(() => {
    sendLocation();
  }, 60000); // Every 60 seconds

  return () => clearInterval(interval);
}, []);