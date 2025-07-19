import { View, Text, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, ImageBackground } from 'react-native';
import React, { useCallback, useEffect, useState } from 'react';
import { useLocalSearchParams, useFocusEffect, router } from 'expo-router';
import Checklist from '@/components/Checklist';
import RecommendationItem from '@/components/RecommendationItem';
import { AntDesign, Feather, Ionicons } from '@expo/vector-icons';
import * as Utils from '../../../utils/utils';
import axios from 'axios';
import imageMap from '@/utils/imageMap';
import { ScrollView } from 'react-native';

interface Item {
  id: string;
  name: string;
  isChecked: boolean;
  deadline?: string | null;
  geo_alert?: boolean;
}

interface Suggestion {
  suggestion_id: string;
  name: string;
}

export default function ListScreen() {
    /* ────────── navigation params ────────── */
    const { list_id, list_name, list_color } = useLocalSearchParams<{
    list_id: string;
    list_name: string;
    list_color?: string | string[];
  }>();
  

  const background = Array.isArray(list_color) ? list_color[0] : list_color;

    /* ────────── component state ────────── */
    const [items, setItems] = useState<Item[]>([]);
    const [recommended, setRecommended] = useState<Suggestion[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [newItemName, setNewItemName] = useState('');
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [editedTitle, setEditedTitle] = useState(list_name);
    const [listGeoAlert, setListGeoAlert] = useState<boolean>(false);
    const [listDeadline, setListDeadline] = useState<string | null>(null);
    const [picPath, setPicPath] = useState<string | null>(null);

    //const imageSource = imageMap[picPath ?? ''] || require('@/assets/images/default-bg.png');
    const imageSource = picPath ? imageMap[picPath] : undefined;
    
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
        `${Utils.currentPath}lists/${list_id}`,
        { headers: { token } },
      );
      
      setEditedTitle(res.data.name); 

      setPicPath(res.data.pic_path ?? null);

      const formatted: Item[] = res.data.items.map((it: any) => ({
        id: it.item_id,
        name: it.name,
        isChecked: it.is_checked,
        deadline: it.deadline,
        geo_alert: it.geo_alert,
      }));

      setItems(formatted);
      setListGeoAlert(res.data.geo_alert ?? false);
      setListDeadline(res.data.deadline ?? null);
      setRecommended(
        res.data.suggestions?.map((s: any) => ({
          suggestion_id: s.suggestion_id,
          name: s.name,
        })) ?? []
      );

    } catch (err) {
      console.error('[LIST] load failed:', err);
    } finally {
      setLoading(false);
    }
  }, [list_id]);

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
        list_id: list_id,
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
        { name: newName, list_id: list_id, },
        { headers: { token } }
      );
    } catch (err) {
      console.error('[RENAME FAILED]', err);
    }
  };
  
  const changeListName = async (newName: string) => {
    setIsEditingTitle(false);
    if (newName.trim() === '' || newName === list_name) return;
  
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.patch(`${Utils.currentPath}lists/${list_id}/name`, {
        name: newName,
      }, {
        headers: { token },
      });
      setEditedTitle(newName);
    } catch (err) {
      console.error('[RENAME LIST FAILED]', err);
    }
  };

  const deleteItem = async (itemId: string) => {
    setItems(prev => prev.filter(item => item.id !== itemId));
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.delete(
        `${Utils.currentPath}items/${itemId}`,
        {
          headers: { token },
          data: { list_id: list_id },
        }
      );
    } catch (err) {
      console.error('[DELETE FAILED]', err);
    }
  };


  const total = items.length;
  const left  = items.filter(i => !i.isChecked).length;


  const addNewItem = async () => {
    if (newItemName.trim() === '') {
      setIsAdding(false);
      return;
    } 
    const token = await Utils.getValueFor('access_token');
    try {
      const res = await axios.post(
        `${Utils.currentPath}lists/${list_id}/items`,
        {
          item_name: newItemName,
          geo_alert: listGeoAlert,
          deadline: listDeadline,
        },
        {headers: { token },}
      );
  
      const newItem = {
        id: res.data.item_id,
        name: res.data.name,
        isChecked: false,
        geo_alert: listGeoAlert,
        deadline: listDeadline,
      };
  
      setItems(prev => [...prev, newItem]);
      setNewItemName('');
      setIsAdding(false);
    } catch (err) {
      console.error('[ADD ITEM FAILED]', err);
    }
  };


  const handleAddRecommendation = async (suggestion: Suggestion) => {
    const token = await Utils.getValueFor('access_token');
    try {
      const res = await axios.post(
        `${Utils.currentPath}lists/${list_id}/suggestions/${suggestion.suggestion_id}/accept`,
        {
          item_name: suggestion.name,
          geo_alert: listGeoAlert,
          deadline: listDeadline,
        },
        { headers: { token } }
      );
  
      const newItem = {
        id: res.data.item_id,
        name: suggestion.name,
        isChecked: false,
        geo_alert: listGeoAlert,
        deadline: listDeadline,
      };
  
      setItems(prev => [...prev, newItem]);
      setRecommended(prev => prev.filter(r => r.suggestion_id !== suggestion.suggestion_id));
    } catch (err) {
      console.error('[ADD SUGGESTION FAILED]', err);
    }
  };

  const handleHideRecommendation = async (s: Suggestion) => {
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.post(
        `${Utils.currentPath}lists/${list_id}/suggestions/${s.suggestion_id}/reject`,
        {},
        { headers: { token } }
      );
      setRecommended((prev) =>
        prev.filter((r) => r.suggestion_id !== s.suggestion_id)
      );
    } catch (err) {
      console.error('[REJECT SUGGESTION FAILED]', err);
    }
  };

  return (
    <View style={styles.container}>
  <ImageBackground
          source={imageSource}
          resizeMode="cover"
          //style={styles.imageBackground}
          style={[styles.imageBackground, { backgroundColor: 'white' }]}
          imageStyle={styles.imageStyle}
        >
      <View style={styles.header}>
    
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back-outline" size={24} color="#007AFF" />
              <Text style={styles.backText}>Back</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={{ position: 'absolute', top: 55, right: 20 }}
          onPress={() => {
            router.push({
              pathname: '../listSettings',
              params: {
                list_id,
                list_name,
                list_color: background,
              },
            });
          }}
        >
          <Feather name="settings" size={24} color="#007AFF" />
        </TouchableOpacity>
        {isEditingTitle ? (
        <TextInput
          style={styles.title}
          value={editedTitle}
          onChangeText={setEditedTitle}
          onBlur={() => changeListName(editedTitle)}
          onSubmitEditing={() => changeListName(editedTitle)}
          autoFocus
        />
      ) : (
        <TouchableOpacity onPress={() => setIsEditingTitle(true)}>
          <Text style={styles.title}>{editedTitle}</Text>
        </TouchableOpacity>
      )}
        <Text style={styles.subtitle}>
          {`${total} items, ${left} remaining`}
        </Text>

        <View style={styles.alertRow}>
          {listDeadline && (
            <View style={styles.alertItem}>
              <Ionicons name="calendar-number-outline" size={16} color="#333" style={{ marginRight: 4 }} />
              <Text style={styles.alertText}>Due to {new Date(listDeadline).toLocaleDateString()}</Text>
            </View>
          )}
          {listGeoAlert && (
            <View style={styles.alertItem}>
              <Ionicons name="location-outline" size={16} color="#333" style={{ marginRight: 4 }} />
              <Text style={styles.alertText}>Location Alerts On</Text>
            </View>
          )}
        </View>
       
      </View>
      </ImageBackground>

      <View style={styles.content}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={{ flex: 1 }}
        >
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.topContent}>
          <View style={{ flexGrow: 0, justifyContent: 'space-between' }}>
            <Checklist
              items={items}
              onToggle={toggleItem}
              onNameChange={changeItemName}
              onDelete={deleteItem}
              listId={list_id}
            />
          </View>
          <View style={styles.addContainer}>
            {!isAdding && (
              <TouchableOpacity style={styles.addButton}
                onPress={() => setIsAdding(true)}
              >
                <AntDesign name="plus" size={30} color="#B25FC3" />
                {/*<Text style={styles.addButtonText}>Add Item</Text> */}
              </TouchableOpacity>
            )}
            {isAdding && (
              <TextInput
                style={styles.input}
                value={newItemName}
                onChangeText={setNewItemName}
                placeholder="Enter item name"
                //onSubmitEditing={addNewItem}
                onBlur={addNewItem}
                autoFocus
              />
            )}
          </View>
      </View>

      {recommended.length > 0 && (
          <View style={styles.recommendations}>
            <Text style={styles.recommendTitle}>Recommended for you</Text>
            {recommended.slice(0, 3).map((rec) => (
              <RecommendationItem
                key={rec.suggestion_id}
                name={rec.name}
                onAdd={() => handleAddRecommendation(rec)}
                onHide={() => handleHideRecommendation(rec)}
              />
            ))}
          </View>
        )}
        </ScrollView>
      </KeyboardAvoidingView>
      
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
    paddingTop: 105,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
  },
  
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    marginBottom: 6,
    color: 'black',
    shadowColor: 'white',
    shadowRadius: 0.2,
    shadowOffset: {
      width: 1.5,
      height: 1.3,
    },
    shadowOpacity: 1,

  },
  subtitle: {
    fontSize: 15,
    color: 'black',
    paddingBottom: 8,
    paddingLeft: 2,
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
  },

  addButton: {
    borderWidth: 1.5,
    borderColor: "#B25FC3",
    padding: 10,
    //marginTop: 12,
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
    width: 250,
  },
  recommendations: {
    marginTop: 50,
  },
  recommendTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    paddingLeft: 4,
  },

  backButton: {
    padding: 6,
    flexDirection: 'row',
    alignItems: 'center',
    position: 'absolute', top: 45, left: 7,
  },
  
  backText: {
    fontSize: 18,
    color: '#007AFF',
    fontWeight: '500',
  },
  imageBackground: {
    justifyContent: 'flex-end',
    padding: 12,
  },
  imageStyle: {
    opacity: 0.7,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'space-between',
    backgroundColor: '#FAFAFA',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  alertRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 4,
    flexWrap: 'wrap',
  },
  
  alertItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(248, 248, 255, .6)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    //opacity: 0.7, 
  },
  
  alertText: {
    fontSize: 12,
    color: '#333',
  },
  
});
