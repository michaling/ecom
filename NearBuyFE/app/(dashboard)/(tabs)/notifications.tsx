// app/(tabs)/notifications.tsx

import React from 'react';
import { FlatList, StyleSheet } from 'react-native';
import NotificationCard from '@/components/NotificationCard';
import { SafeAreaView } from 'react-native-safe-area-context';

const dummyData = [
    {
      type: 'location' as const,
      timestamp: '5 min ago',
      storeName: 'SuperMart',
      itemsByList: [
        { listName: 'Groceries', items: ['Milk', 'Bread'] },
        { listName: 'Weekend Trip', items: ['Eggs'] },
      ],
    },
    {
      type: 'deadline' as const,
      timestamp: '2 hours ago',
      date: 'June 30',
      itemsByList: [
        { listName: 'Birthday Party', items: ['Cake', 'Gift Bag'] },
      ],
    },
  ];
  
  

export default function NotificationsScreen() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <FlatList
        data={dummyData}
        keyExtractor={(_, index) => index.toString()}
        contentContainerStyle={styles.contentContainer}
        renderItem={({ item }) => <NotificationCard {...item} />}
        showsVerticalScrollIndicator={false}
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
