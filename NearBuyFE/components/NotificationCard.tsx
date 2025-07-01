import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

type AlertType = 'geo_alert' | 'deadline_alert';

interface Props {
  type: AlertType;
  timestamp: string;
  storeName?: string;
  date?: string;
  itemsByList: { listName: string; items: string[] }[];
}

export default function NotificationCard({
  type,
  timestamp,
  storeName,
  date,
  itemsByList,
}: Props) {
  const isGeo = type === 'geo_alert';

  const iconName = isGeo ? 'location-outline' : 'time-outline';
  const title = isGeo
    ? `Location Alert: ${storeName ?? ''}`
    : `Deadline Alert: ${date ? dayjs(date).format('MMMM D') : ''}`;
  const message = isGeo
    ? `You have some items you can buy in ${storeName ?? 'this store'}!`
    : `You have upcoming deadlines for items needed by ${date ? dayjs(date).format('MMMM D') : 'a deadline'}.`;

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Ionicons name={iconName} size={20} color="#F36D9A" style={styles.icon} />
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.timestamp}>{dayjs(timestamp).fromNow()}</Text>
      </View>

      <Text style={styles.message}>{message}</Text>

      {itemsByList.map(({ listName, items }, index) => (
        <View key={index} style={styles.listSection}>
          <Text style={styles.listName}>{listName}</Text>
          {items.map((item, i) => (
            <Text key={i} style={styles.item}>• {item}</Text>
          ))}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginVertical: 10,
    marginHorizontal: 16,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  icon: {
    marginRight: 8,
  },
  title: {
    fontWeight: 'bold',
    fontSize: 16,
    flex: 1,
  },
  timestamp: {
    fontSize: 12,
    color: '#888',
  },
  message: {
    fontSize: 14,
    marginBottom: 8,
    color: '#333',
  },
  listSection: {
    marginTop: 8,
  },
  listName: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    marginBottom: 2,
  },
  item: {
    fontSize: 13,
    color: '#444',
    marginLeft: 8,
  },
});