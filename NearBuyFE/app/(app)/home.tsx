import React from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  FlatList,
  ImageBackground,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

const CATEGORY_DATA = [
  { id: '1', title: 'BIRTHDAY PARTY', color: '#FFE3E3', image: null },
  { id: '2', title: 'MEDICINES', color: '#FFCDB3', image: null },
  { id: '3', title: 'CLOTHES', color: '#FFEABE', image: null },
  { id: '4', title: 'GROCERIES', color: '#DAEDCE', image: null },
  { id: '5', title: 'TECH', color: '#C8E2FC', image: null },
  { id: '6', title: 'GIFTS', color: '#C8A2C8', image: null },
];

export default function HomeScreen() {
  const router = useRouter();

  const renderItem = ({ item }: any) => (
    <Pressable style={styles.cardContainer} onPress={() => {}}>
      <View style={styles.card}>
        <ImageBackground
          source={item.image ? { uri: item.image } : undefined}
          resizeMode="cover"
          style={[styles.imageBackground, { backgroundColor: item.color }]}
          imageStyle={styles.imageStyle}
        >
          <View style={styles.textContainer}>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text style={styles.cardSubtitle}>0 items</Text>
          </View>
        </ImageBackground>
      </View>
    </Pressable>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>

    <View style={styles.logoContainer}>
      {/* In the future you can add an <Image source={...} /> here */}
      <Text style={styles.logoText}>NearBuy</Text>
    </View>
        {/* Tool Buttons (Add/Edit) */}
    <View style={styles.toolsRow}>
      <Pressable style={styles.toolButton} onPress={() => {}}>
        <Text style={styles.toolButtonText}>Edit</Text>
      </Pressable>
      <Pressable style={styles.toolButton} onPress={() => {}}>
        <Text style={styles.toolButtonText}>＋</Text>
      </Pressable>
    </View>
      <FlatList
        data={CATEGORY_DATA}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        numColumns={2}
        contentContainerStyle={styles.grid}
        columnWrapperStyle={styles.row}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
}

const CARD_WIDTH = '48%';

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
  addButton: {
    position: 'absolute',
    top: 20,
    right: 20,
    zIndex: 10,
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: '#333333',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
  },
  addButtonText: {
    fontSize: 22,
    fontWeight: 'bold',
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
