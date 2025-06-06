import { View, Text, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import React, { useCallback, useEffect, useState } from 'react';
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import Checklist from '@/components/Checklist';
import RecommendationItem from '@/components/RecommendationItem';
import { AntDesign, Ionicons } from '@expo/vector-icons';
import * as Utils from '../../../utils/utils';
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
    const [isAdding, setIsAdding] = useState(false);
    const [newItemName, setNewItemName] = useState('');


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

  const addNewItem = () => {
    // TODO: Insert new item to BE
    // if (newItemName.trim() === '') return;
    // const newItem = {
    //   id: Date.now().toString(), // TODO: replace with actual ID from BE
    //   name: newItemName,
    //   isChecked: false,
    // };
    // setItems(prev => [...prev, newItem]);
    // setNewItemName('');
    // setIsAdding(false);
  };


  const handleAddRecommendation = (name: string) => {
    const newItem = {
      id: Date.now().toString(),
      name,
      isChecked: false,
    };
    setItems((prev) => [...prev, newItem]);
    setRecommended((prev) => prev.filter((r) => r !== name));
  };

  return (
    <View style={styles.container}>

      <View style={[styles.header, { backgroundColor: background || '#E6E6FA' }]}>
        <Text style={styles.title}>{title} </Text>
        <Text style={styles.subtitle}>
          {`${total} items, ${left} remaining`}
        </Text>
      </View>
  
      <View style={styles.content}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={{ flex: 1 }}
        >
        <View style={styles.topContent}>
          <View style={{ flexGrow: 0 }}>
            <Checklist
              items={items}
              onToggle={toggleItem}
              onNameChange={changeItemName}
              onDelete={deleteItem}
            />
          </View>
          <View style={styles.addContainer}>
            {!isAdding && (
              <TouchableOpacity style={styles.addButton}
                onPress={() => setIsAdding(true)}
              >
                <AntDesign name="plus" size={33} color="purple" />
                {/*<Text style={styles.addButtonText}>Add Item</Text> */}
              </TouchableOpacity>
            )}
            {isAdding && (
              <TextInput
                style={styles.input}
                value={newItemName}
                onChangeText={setNewItemName}
                placeholder="Enter item name"
                onSubmitEditing={addNewItem}
                onBlur={addNewItem}
                autoFocus
              />
            )}
          </View>
      </View>
      </KeyboardAvoidingView>
      {recommended.length > 0 && (
          <View style={styles.recommendations}>
            <Text style={styles.recommendTitle}>Recommended for you</Text>
            {recommended.slice(0, 3).map((rec) => (
              <RecommendationItem
                key={rec}
                name={rec}
                onAdd={() => handleAddRecommendation(rec)}
              />
            ))}
          </View>
        )}

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
    backgroundColor: '#FAFAFA',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    marginTop: -15,
    padding: 16,
  
    // Shadow (iOS)
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  
    // Shadow (Android)
    elevation: 10,
  },
  topContent: {
    flexGrow: 1,
  },

  addContainer: {
    alignItems: 'center',
    marginTop: 16,
  },

  addButton: {
    borderWidth: 1,
    borderColor: "purple",
    padding: 12,
    marginTop: 12,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addButtonText: {
    fontSize: 12,
    color: '#333',
    marginTop: 4,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 10,
    padding: 10,
    marginTop: 10,
    fontSize: 16,
  },

  recommendationsBox: {
    borderTopWidth: 1,
    borderTopColor: '#ddd',
    paddingTop: 12,
  },

  recommendations: {
    marginTop: 24,
    marginBottom: 50,
  },
  recommendTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    paddingLeft: 4,
  },

});
