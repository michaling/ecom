import NotificationCard from '@/components/NotificationCard';
import axios from 'axios';
import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, RefreshControl, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Utils from '../../../utils/utils';

interface AlertCard {
  alert_id: string;
  type: 'geo_alert' | 'deadline_alert';
  timestamp: string;
  storeName?: string;
  date?: string;
  itemsByList: { listName: string; items: string[] }[];
}

export default function NotificationsScreen() {
  const [alerts, setAlerts] = useState<AlertCard[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAlerts = async () => {
    try {
      const token = await Utils.getValueFor('access_token');
      if (!token) return;

      const res = await axios.get(`${Utils.currentPath}alerts_tab`, {
        headers: { token },
      });

      setAlerts(res.data);
    } catch (error) {
      console.error('[fetchAlerts]', error);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchAlerts().finally(() => setRefreshing(false));
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <FlatList
        data={alerts}
        keyExtractor={(item) => item.alert_id}
        contentContainerStyle={styles.contentContainer}
        renderItem={({ item }) => <NotificationCard {...item} />}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#E6E6FA',
  },
  contentContainer: {
    paddingVertical: 16,
  },
});