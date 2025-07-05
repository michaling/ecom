import axios from 'axios';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import * as Utils from '../utils/utils';

export default function IndexRedirect() {
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const token = await Utils.getValueFor('access_token');
      const userId = await Utils.getValueFor('user_id');

      if (token && userId) {
        console.log('Token found, checking profile...');
        try {
          await axios.get(`${Utils.currentPath}profile`, {
            headers: { token },
          });
          router.replace('/home');
        } catch (err) {
          console.log('Token invalid or expired', err);
          router.replace('/login');
        }
      } else {
        router.replace('/login');
      }
    };
    checkAuth(); 
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#007AFF" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
});