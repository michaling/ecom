import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import Checklist from '@/components/Checklist';
import * as Utils from '../../utils/utils';
import axios from 'axios';

interface Item {
  id: string;
  name: string;
  isChecked: boolean;
}

export default function ListScreen() {
    /* ────────── navigation params ────────── */
    const { id, title, color } = useLocalSearchParams<{
    id: string;
    title: string;
    color?: string | string[];
  }>();

  const background = Array.isArray(color) ? color[0] : color;

    /* ────────── component state ────────── */
    const [items, setItems] = useState<Item[]>([]);
    const [recommended, setRecommended] = useState<string[]>([]); // we’ll need it soon
    const [loading, setLoading] = useState(true);


    /* ────────── helper: fetch list from BE ────────── */
  const loadList = useCallback(async () => {
    try {
      setLoading(true);
      const token = await Utils.getValueFor('access_token');
      if (!token) {
        console.warn('[LIST] no token – probably logged-out');
        return;
      }

      const res = await axios.get(
        `${Utils.currentPath}lists/${id}`,
        { headers: { token } },
      );

      //  { items: [...], suggested_items: [...] }
      const formatted: Item[] = res.data.items.map((it: any) => ({
        id: it.item_id,
        name: it.name,
        isChecked: it.is_checked,
      }));

      setItems(formatted);
      setRecommended(res.data.suggested_items?.map((s: any) => s.name) ?? []);
    } catch (err) {
      console.error('[LIST] load failed:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);
    
  /* load once on mount */
  useEffect(() => {
    loadList(); // here we just invoke it, not return it
  }, [loadList]);

  /* reload every time the screen gains focus */
  useFocusEffect(
    React.useCallback(() => {
      loadList();
    }, [loadList]),
  );
    

  const toggleItem = async (id: string) => {
    const updatedItems = items.map((item) =>
      item.id === id ? { ...item, isChecked: !item.isChecked } : item
    );
    setItems(updatedItems);
  
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.patch(`${Utils.currentPath}items/${id}/check`, {
        is_checked: !items.find(item => item.id === id)?.isChecked,
      }, {
        headers: { token },
      });
    } catch (err) {
      console.error('[TOGGLE FAILED]', err);
    }
  };

  
  const changeItemName = async (itemId: string, newName: string) => {
    setItems(prev =>
      prev.map(item => item.id === itemId ? { ...item, name: newName } : item)
    );
  
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.patch(
        `${Utils.currentPath}items/${itemId}/name`,
        { name: newName },
        { headers: { token } }
      );
    } catch (err) {
      console.error('[RENAME FAILED]', err);
    }
  };
  
  const deleteItem = async (itemId: string) => {
    setItems(prev => prev.filter(item => item.id !== itemId));
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.delete(
        `${Utils.currentPath}items/${itemId}`,
        { headers: { token } }
      );
    } catch (err) {
      console.error('[DELETE FAILED]', err);
    }
  };

  
  const total = items.length;
  const left  = items.filter(i => !i.isChecked).length;


  return (
    <View style={styles.container}>
      <View style={[styles.header, { backgroundColor: background || '#E6E6FA' }]}>
        <Text style={styles.title}>{title} </Text>
        <Text style={styles.subtitle}>
          {`${total} items, ${left} remaining`}
        </Text>
      </View>
  
      <View style={styles.content}>
        <Checklist
          items={items}
          onToggle={toggleItem}
          onNameChange={changeItemName}
          onDelete={deleteItem}
        />
      </View>
    </View>
  );
  
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 20,
    paddingTop: 120,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
  },
  
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 6,
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    paddingBottom: 10,
    paddingLeft: 8,
  },

  content: {
    flex: 1,
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    marginTop: -15, // כדי ל"עלות" קצת על ה-header
    padding: 16,
  
    // Shadow (iOS)
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  
    // Shadow (Android)
    elevation: 10,
  },
  
});
