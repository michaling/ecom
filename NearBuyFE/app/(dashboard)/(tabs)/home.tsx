import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useFocusEffect } from '@react-navigation/native';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  FlatList,
  ImageBackground,
  Modal,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Utils from '../../utils/utils';


const CARD_COLORS = [
  '#FFE3E3', '#FFCDB3', '#FFEABE',
  '#DAEDCE', '#C8E2FC', '#C8A2C8'
];

const getRandomPastelColor = () => {
  const hue = Math.floor(Math.random() * 360); // Random hue
  return `hsl(${hue}, 70%, 85%)`;              // Pastel shade
}; 

export default function HomeScreen() {
  const router = useRouter();
  const [lists, setLists] = useState<any[]>([]);

  // fetch once each time Home gains focus
  const fetchLists = React.useCallback(async () => {
    try {
      console.log('[HOME] fetching lists …');
      const [user_id, token] = await Promise.all([
        Utils.getValueFor('user_id'),
        Utils.getValueFor('access_token'),
      ]);
      if (!token || !user_id) {
        console.warn('[HOME] no user or token'); return;
      }

      const res = await axios.get(Utils.currentPath + 'lists', {
        params: { user_id },
        headers: { token },
      });

      const listsWithColors = res.data.map((it: any, idx: number) => ({
        ...it,
        color: CARD_COLORS[idx % CARD_COLORS.length],
      }));
      setLists(listsWithColors);
    } catch (err) {
      console.error('[HOME] fetch error', err);
    }
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      // call the async function but don’t return its Promise
      fetchLists();
    }, [fetchLists])
  );

  const renderItem = ({ item: list }: any) => (
    <Pressable
      style={styles.cardContainer}
      onPress={() =>
        router.push({
          pathname: '/(dashboard)/(list)/listScreen',
          params: {
            // Pass the list details to the list screen
            id:    list.id,
            title: list.name,
            color: list.color,
          },
        })
      }
    >
      <View style={styles.card}>
        <ImageBackground
          source={list.image ? { uri: list.image } : undefined}
          resizeMode="cover"
          style={[styles.imageBackground, { backgroundColor: list.color }]}
          imageStyle={styles.imageStyle}
        >
          <View style={styles.textContainer}>
            <Text style={styles.cardTitle}>{list.name}</Text>
            <Text style={styles.cardSubtitle}>
              {list.unchecked_count} items left
            </Text>
          </View>
        </ImageBackground>
      </View>
    </Pressable>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <View style={styles.logoContainer}>
        <Text style={styles.logoText}>NearBuy</Text>
      </View>

      <View style={styles.toolsRow}>
        <Pressable style={styles.toolButton} onPress={() => {}}>
          <Text style={styles.toolButtonText}>Edit</Text>
        </Pressable>
        <Pressable style={styles.toolButton} onPress={() => {}}>
          <Text style={styles.toolButtonText}>＋</Text>
        </Pressable>
      </View>

      <FlatList
        data={lists}
        renderItem={renderItem}
        keyExtractor={(list) => list.id}
        numColumns={2}
        contentContainerStyle={styles.grid}
        columnWrapperStyle={styles.row}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const CARD_WIDTH = '48%';
const COLORS = ['#FFE3E3', '#FFCDB3', '#FFEABE', '#DAEDCE', '#C8E2FC', '#C8A2C8'];


const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFA',
    paddingHorizontal: 12,
  },
  grid: {
    paddingBottom: 100,
  },
  row: {
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  cardContainer: {
    width: CARD_WIDTH,
    aspectRatio: 1.2,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 5,
    backgroundColor: '#fff',
  },
  card: {
    flex: 1,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#eee',
    position: 'relative',
  },
  imageBackground: {
    flex: 1,
    justifyContent: 'flex-end',
    padding: 12,
  },
  imageStyle: {
    resizeMode: 'cover',
  },
  textContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333333',
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#444',
    marginTop: 4,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 12,
  },
  logoText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
  },
  toolsRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    paddingHorizontal: 12,
    marginBottom: 12,
  },
  toolButton: {
    backgroundColor: '#fff',
    borderColor: '#444',
    borderWidth: 1.5,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  toolButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
});
