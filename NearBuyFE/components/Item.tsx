// components/ShoppingItem.tsx

import React, { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Swipeable from 'react-native-gesture-handler/Swipeable';


interface ShoppingItemProps {
  name: string;
  isChecked: boolean;
  onToggle: () => void;
  onNameChange: (newName: string) => void;
  onDelete: () => void;
}

export default function ShoppingItem({ name, isChecked, onToggle, onNameChange, onDelete }: ShoppingItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(name);

  const handleEndEditing = () => {
    setIsEditing(false);
    onNameChange(editedName);
  };

  const renderRightActions = () => {
    return (
      <Pressable style={styles.deleteButton} onPress={onDelete}>
        <Ionicons name="trash-outline" size={22} color="white" />
        <Text style={styles.deleteText}>Delete</Text>
      </Pressable>
    );
  };

  return (
    <Swipeable renderRightActions={renderRightActions}>
    <View style={styles.container}>
      <Pressable onPress={onToggle}>
        <Ionicons
          name={isChecked ? 'checkbox' : 'square-outline'}
          size={28}
          color={isChecked ? 'purple' : 'gray'}
          style={styles.icon}
        />
      </Pressable>

      {isEditing ? (
        <TextInput
          value={editedName}
          onChangeText={setEditedName}
          onBlur={handleEndEditing}
          autoFocus
          style={styles.input}
        />
      ) : (
        <Pressable onPress={() => setIsEditing(true)} style={{ flex: 1 }}>
          <Text style={[styles.text, isChecked && styles.checked]}>{name}</Text>
        </Pressable>
      )}
    </View>
    </Swipeable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row', // כדי שהאייקון והטקסט יהיו בשורה
    alignItems: 'center', // מרכז אנכית
    padding: 15, // ריווח פנימי
  },
  icon: {
    marginRight: 10, // ריווח בין האייקון לטקסט
  },
  text: {
    fontSize: 18,
  },
  checked: {
    textDecorationLine: 'line-through', // קו על טקסט מסומן
    color: 'gray',
  },
  input: {
    fontSize: 18,
    borderBottomWidth: 1,
    flex: 1, // שיתפוס את כל הרוחב הפנוי
  },

  deleteButton: {
    backgroundColor: 'red',
    justifyContent: 'center',
    alignItems: 'center',
    width: 80,
  },
  deleteText: {
    color: 'white',
    fontSize: 11,
    marginTop: 4,
  },
  
});
