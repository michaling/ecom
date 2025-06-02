// components/RecommendationItem.tsx
import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  name: string;
  onAdd: () => void;
}

export default function RecommendationItem({ name, onAdd }: Props) {
  return (
    <View style={styles.row}>
      <Pressable onPress={onAdd} style={styles.button}>
        <Ionicons name="add-circle-outline" size={26} color="#4CAF50" />
      </Pressable>
      <Text style={styles.text}>{name}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
    paddingHorizontal: 8,
  },
  text: {
    fontSize: 17,
    flex: 1,
    marginLeft: 5,
  },
  button: {
    padding: 4,
  },
});
