import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, Pressable, TextInput } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

interface Item {
  id: string;
  name: string;
  isBought: boolean;
}

export default function ListScreen() {
  const { title, color, id } = useLocalSearchParams();
  const [items, setItems] = useState<Item[]>([]);
  const [recommended, setRecommended] = useState<string[]>([]);
  const [newItem, setNewItem] = useState('');

  useEffect(() => {
    // Mocked DB items per category
    setItems([
      { id: '1', name: 'balloons', isBought: false },
      { id: '2', name: 'plates', isBought: false },
      { id: '3', name: 'drinks', isBought: false },
    ]);
    setRecommended(['snacks', 'presents', 'cups']);
  }, [id]);

  const toggleItem = (id: string) => {
    setItems(prev => prev.map(i => i.id === id ? { ...i, isBought: !i.isBought } : i));
  };

  const renderItem = ({ item }: { item: Item }) => (
    <View style={styles.itemBox}>
      <Pressable onPress={() => toggleItem(item.id)} style={styles.checkbox}>
        {item.isBought && <Text style={styles.checkmark}>✓</Text>}
      </Pressable>
      <Text style={styles.itemText}>{item.name}</Text>
      <Ionicons name="information-circle-outline" size={24} color="#333" style={styles.infoIcon} />
    </View>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: '#FCE8D5' }]}>
      <Text style={styles.title}>{title}</Text>

      <FlatList
        data={items}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
      />

      <View style={styles.newItemBox}>
        <Pressable style={styles.checkbox}>
          {/* empty checkbox for new item */}
        </Pressable>
        <TextInput
          value={newItem}
          onChangeText={setNewItem}
          placeholder="Add new item..."
          style={styles.input}
        />
      </View>

      <Text style={styles.recommendedTitle}>Recommended for you</Text>
      {recommended.map((rec) => (
        <View style={styles.recommendationRow} key={rec}>
          <Text style={styles.plus}>＋</Text>
          <Text style={styles.recommendationText}>{rec}</Text>
        </View>
      ))}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  list: {
    paddingBottom: 16,
  },
  itemBox: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
    borderRadius: 16,
    paddingVertical: 10,
    paddingHorizontal: 12,
    marginBottom: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#333',
    borderRadius: 4,
    marginRight: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmark: {
    fontSize: 16,
    color: '#333',
  },
  itemText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
  },
  infoIcon: {
    marginLeft: 8,
  },
  newItemBox: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#bbb',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 24,
  },
  input: {
    flex: 1,
    fontSize: 16,
  },
  recommendedTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  recommendationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  plus: {
    fontSize: 20,
    marginRight: 8,
  },
  recommendationText: {
    fontSize: 16,
  },
});
