import React from 'react';
import { View, Text, Pressable, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  name: string;
  onAdd: () => void;
  onHide: () => void;
}

export default function RecommendationItem({ name, onAdd, onHide }: Props) {
  return (
    <View style={styles.row}>
      <Pressable onPress={onAdd} style={styles.button}>
        <Ionicons name="add-circle-outline" size={26} color="#4CAF50" />
      </Pressable>
      <Text style={styles.text}>{name}</Text>

      <TouchableOpacity onPress={onHide}>
        <Text style={styles.hideText}>hide</Text>
      </TouchableOpacity>

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
  hideText: {
    color: '#c2c2c2',
    fontSize: 14,
    padding: 8,
  },
});
