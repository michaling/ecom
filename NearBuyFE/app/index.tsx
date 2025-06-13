import { useEffect, useState } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import * as Utils from '../utils/utils';

export default function IndexRedirect() {
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const token = await Utils.getValueFor('access_token');
      const userId = await Utils.getValueFor('user_id');

      if (token && userId) {
        router.replace('/home');
      } else {
        router.replace('/login');
      }
    };

    checkAuth(); // no need to delay it
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