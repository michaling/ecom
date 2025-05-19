import React from 'react';
import { View, Text, ScrollView, Pressable, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';

const CATEGORY_DATA = [
  { id: '1', title: 'BIRTHDAY PARTY', color: '#FFE3E3' },
  { id: '2', title: 'MEDICINES', color: '#FFCDB3' },
  { id: '3', title: 'CLOTHES', color: '#FFEABE' },
  { id: '4', title: 'GROCERIES', color: '#DAEDCE' },
  { id: '5', title: 'TECH', color: '#C8E2FC' },
  { id: '6', title: 'GIFTS', color: '#C8A2C8' },  
];

const CARD_HEIGHT = 100;
const CARD_OVERLAP = 30;

export default function HomeScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      {/* Add New Category Button */}
      <Pressable style={styles.addButton} onPress={() => {}}>
        <Text style={styles.addButtonText}>＋</Text>
      </Pressable>

      <ScrollView contentContainerStyle={styles.scrollContainer}>
    {CATEGORY_DATA.map((item, index) => (
    <Pressable
      key={item.id}
      style={[
        styles.card,
        {
          backgroundColor: item.color,
          marginTop: index === 0 ? 0 : -CARD_OVERLAP, // overlap the previous card
        },
      ]}
      //onPress={() => router.push(`/category/${item.id}`)}
      >
      <Text style={styles.cardText}>{item.title}</Text>
    </Pressable>
  ))}
</ScrollView>

    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    paddingTop: 60,
    paddingHorizontal: 16,
  },
  scrollContainer: {
    paddingBottom: 200,
    paddingTop: 20,
  },
  
  card: {
    width: '100%',
    height: CARD_HEIGHT,
    borderRadius: 16,
    paddingHorizontal: 20,
    paddingTop: 16,
    justifyContent: 'flex-start',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 0.5,
    borderColor: '#ccc',
  },
  
  cardText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  
  addButton: {
    position: 'absolute',
    top: 20,
    right: 20,
    zIndex: 1000,
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: '#444',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
  },
  addButtonText: {
    fontSize: 22,
    fontWeight: 'bold',
  },
});
