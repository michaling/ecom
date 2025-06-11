// components/Item.tsx

import React, { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet, Modal, Switch, TouchableOpacity, Platform } from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import Swipeable from 'react-native-gesture-handler/Swipeable';
import DateTimePicker from '@react-native-community/datetimepicker';
import { DateTimePickerAndroid } from '@react-native-community/datetimepicker';

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
  const [showSettings, setShowSettings] = useState(false);
  const [locationAlert, setLocationAlert] = useState(false);
  const [deadlineAlert, setDeadlineAlert] = useState(false);
  const [deadline, setDeadline] = useState<Date | null>(null);


  const handleEndEditing = () => {
    setIsEditing(false);
    onNameChange(editedName);
  };

  const showAndroidDateTimePicker = () => {
    DateTimePickerAndroid.open({
      value: deadline || new Date(),
      mode: 'date',
      is24Hour: true,
      onChange: (event, selectedDate) => {
        if (event.type === 'set' && selectedDate) {
          DateTimePickerAndroid.open({
            value: selectedDate,
            mode: 'time',
            is24Hour: true,
            onChange: (event2, selectedTime) => {
              if (event2.type === 'set' && selectedTime) {
                const finalDate = new Date(selectedDate);
                finalDate.setHours(selectedTime.getHours());
                finalDate.setMinutes(selectedTime.getMinutes());
                setDeadline(finalDate);
              }
            },
          });
        }
      },
    });
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

      {!isEditing && (
        <Pressable onPress={() => setShowSettings(true)} style={{ marginLeft: 10 }}>
          <Feather name="info" size={24} color="#c2c2c2" />
        </Pressable>
      )}
      </View>

      {/* Settings Modal */}
      <Modal
        visible={showSettings}
        animationType="slide"
        transparent
        onRequestClose={() => setShowSettings(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}> {name} </Text>

            {/* Location toggle */}
            <View style={styles.toggleContainer}>
              <Text style={styles.toggleLabel}>Location Alerts</Text>
              <Switch
                value={locationAlert}
                onValueChange={setLocationAlert}
                trackColor={{ false: '#ccc', true: '#007AFF' }}
                thumbColor={locationAlert ? '#fff' : '#f4f3f4'}
              />
            </View>

            {/* Deadline toggle */}
            <View style={styles.toggleContainer}>
              <Text style={styles.toggleLabel}>Deadline Alerts</Text>
              <Switch
                value={deadlineAlert}
                onValueChange={(val) => {
                  setDeadlineAlert(val);
                  if (!val) setDeadline(null);
                }}
                trackColor={{ false: '#ccc', true: '#007AFF' }}
                thumbColor={deadlineAlert ? '#fff' : '#f4f3f4'}
              />
            </View>

            {/* Deadline Picker */}
            {deadlineAlert && (
              <>
                <Text style={styles.toggleLabel}>Deadline:</Text>

                {Platform.OS === 'ios' && (
                  <DateTimePicker
                    value={deadline || new Date()}
                    mode="datetime"
                    display="spinner"
                    onChange={(event, selectedDate) => {
                      if (selectedDate) setDeadline(selectedDate);
                    }}
                    style={{ backgroundColor: '#fff' }}
                  />
                )}

                {Platform.OS === 'android' && (
                  <Pressable onPress={showAndroidDateTimePicker} style={styles.deadlineButton}>
                    <Text style={styles.deadlineText}>
                      {deadline ? deadline.toLocaleString() : 'Pick date & time'}
                    </Text>
                  </Pressable>
                )}

                {Platform.OS === 'web' && (
                  <>
                    <TextInput
                      placeholder="YYYY-MM-DD HH:MM"
                      value={deadline ? deadline.toLocaleString() : ''}
                      onChangeText={(text) => {
                        const parsed = new Date(text);
                        if (!isNaN(parsed.getTime())) setDeadline(parsed);
                      }}
                      style={styles.input}
                    />
                    <Text style={{ fontSize: 12, color: '#888', marginTop: -8, marginBottom: 8 }}>
                      Format: YYYY-MM-DD HH:MM
                    </Text>
                  </>
                )}
              </>
            )}

            {/* Action buttons */}
            <View style={styles.modalButtons}>
              <Pressable onPress={() => setShowSettings(false)} style={styles.cancelButton}>
                <Text style={styles.cancelText}>Cancel</Text>
              </Pressable>

              <Pressable onPress={() => setShowSettings(false)} style={styles.saveButton}>
                <Text style={styles.saveText}>Save</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </Swipeable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
  },
  icon: {
    marginRight: 10,
  },
  text: {
    fontSize: 18,
  },
  checked: {
    textDecorationLine: 'line-through',
    color: 'gray',
  },
  input: {
    fontSize: 18,
    borderBottomWidth: 1,
    flex: 1,
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    minHeight: '60%',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  toggleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  toggleLabel: {
    fontSize: 16,
  },
  deadlineButton: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  deadlineText: {
    fontSize: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
    paddingHorizontal: 20,
  },
  cancelButton: {
    padding: 10,
  },
  cancelText: {
    fontSize: 16,
    color: '#888',
  },
  saveButton: {
    backgroundColor: '#007AFF',
    padding: 10,
    borderRadius: 8,
  },
  saveText: {
    fontSize: 16,
    color: '#fff',
  },
});