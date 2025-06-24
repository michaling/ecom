import React from 'react';
import { View, Text, Pressable, StyleSheet, ImageBackground, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import imageMap from '@/utils/imageMap';

export default function ListCard({ list }: { list: any }) {
  const router = useRouter();
  const imageSource = imageMap[list.pic_path] || require('@/assets/images/default-bg.png');

  return (
    <TouchableOpacity activeOpacity={.6}
      style={styles.cardContainer}
      onPress={() =>
        router.push({
          pathname: '/(dashboard)/(list)/listScreen',
          params: {
            // Pass the list details to the list screen
            list_id:    list.id,
            list_name: list.name,
            list_color: list.color,
          },
        })
      }
    >
      <View style={styles.card}>
        <ImageBackground
          source={imageSource}
          resizeMode="cover"
          style={styles.imageBackground}
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
    </TouchableOpacity>
  );
}


const styles = StyleSheet.create({
  cardContainer: {
    width: '48%',
    aspectRatio: 1.2,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
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
    //resizeMode: 'cover',
    borderRadius: 16,
    paddingBottom: 30,
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
    fontSize: 14,
    fontWeight: '600',
    color: '#2A294B',
  },
  cardSubtitle: {
    fontSize: 13,
    color: '#444',
    marginTop: 4,
  },
});
