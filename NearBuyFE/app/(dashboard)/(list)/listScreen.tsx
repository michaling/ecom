import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import Checklist from '@/components/Checklist';
import RecommendationItem from '@/components/RecommendationItem';

export default function ListScreen() {
  const { id, title, color, items: listItems, suggestions: rawSuggestions } = useLocalSearchParams();
  const background = Array.isArray(color) ? color[0] : color;

  const [items, setItems] = useState<any[]>([]);
  const [recommended, setRecommended] = useState<string[]>([]);
  
  useEffect(() => {
    if (listItems) {
      const parsed = JSON.parse(listItems as string);
      const formatted = parsed.map((item: any) => ({
        id: item.item_id,
        name: item.name,
        isChecked: item.is_checked,
      }));
      setItems(formatted);
    }
  
    if (rawSuggestions) {
      const parsed = JSON.parse(rawSuggestions as string);
      const namesOnly = parsed.map((s: any) => s.name);
      setRecommended(namesOnly);
      console.log('[Suggestions Loaded]', namesOnly); 
    }
  }, [listItems, rawSuggestions]);

  const totalItems = items.length;
  const checkedItems = items.filter((item) => item.isChecked).length;

  const toggleItem = (id: string) => {
    setItems(prev =>
      prev.map(item => item.id === id ? { ...item, isChecked: !item.isChecked } : item)
    );
  };
  
  const changeItemName = (id: string, newName: string) => {
    setItems(prev =>
      prev.map(item => item.id === id ? { ...item, name: newName } : item)
    );
  };
  
  const deleteItem = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
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
          {`${totalItems} items, ${totalItems - checkedItems} remaining`}
        </Text>
      </View>
  
      <View style={styles.content}>
        <Checklist
          items={items}
          onToggle={toggleItem}
          onNameChange={changeItemName}
          onDelete={deleteItem}
        />
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
    backgroundColor: '#fff',
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
