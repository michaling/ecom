import React, { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet, Modal, Switch, TouchableOpacity, Platform } from 'react-native';
import { Ionicons, Feather, MaterialIcons } from '@expo/vector-icons';
import Swipeable from 'react-native-gesture-handler/Swipeable';
import DateTimePicker from '@react-native-community/datetimepicker';
import { DateTimePickerAndroid } from '@react-native-community/datetimepicker';
import axios from 'axios';
import * as Utils from '../utils/utils';


interface ShoppingItemProps {
  item_id: string;
  list_id: string;
  name: string;
  isChecked: boolean;
  onToggle: () => void;
  onNameChange: (newName: string) => void;
  onDelete: () => void;
  deadline?: string | null;
  geo_alert?: boolean;
}

export default function ShoppingItem({ item_id, list_id, name, isChecked, onToggle, onNameChange, onDelete, deadline, geo_alert }: ShoppingItemProps) {

  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState(name);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [showDeadlineModal, setShowDeadlineModal] = useState(false);
  const [locationAlert, setLocationAlert] = useState(geo_alert ?? false);
  const [deadlineDate, setDeadlineDate] = useState<Date | null>(deadline ? new Date(deadline) : null);
  const [deadlineAlert, setDeadlineAlert] = useState(!!deadline);
  const [tempLocationAlert, setTempLocationAlert] = useState(locationAlert);
  const [tempDeadlineAlert, setTempDeadlineAlert] = useState(deadlineAlert);
  const [tempDeadline, setTempDeadline] = useState<Date | null>(
    deadline ? new Date(deadline) : null
  );
  

  
  const handleEndEditing = () => {
    setIsEditing(false);
    onNameChange(editedName);
  };

  const showAndroidDateTimePicker = () => {
    DateTimePickerAndroid.open({
      value: typeof tempDeadline === 'string' ? new Date(tempDeadline) : tempDeadline || new Date(),
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
                setTempDeadline(finalDate);
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

  const openDeadlineModal = () => {
    setTempDeadlineAlert(deadlineAlert);
    setTempDeadline(deadline ? new Date(deadline) : null);

    setShowDeadlineModal(true);
  };

  return (
    <Swipeable renderRightActions={renderRightActions}>
      <View style={styles.container}>
        <Pressable onPress={onToggle}>
          <Ionicons
            name={isChecked ? 'checkbox' : 'square-outline'}
            size={28}
            color={isChecked ? '#B25FC3' : 'gray'}
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

      {!isEditing && !isChecked && (
        <View style={{ flexDirection: 'row', gap: 12, marginLeft: 10 }}>
          <TouchableOpacity onPress={() => openDeadlineModal()}>
            <Ionicons
              name={deadlineAlert ? "calendar-number" : "calendar-number-outline"}
              size={22}
              color={deadlineAlert ? '#007AFF' : '#c2c2c2'}
            />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => {
            setTempLocationAlert(locationAlert);
            setShowLocationModal(true);
          }}>
            <Ionicons
              name={locationAlert ? "location" : "location-outline"}
              size={22}
              color={locationAlert ? '#007AFF' : '#c2c2c2'}
            />
          </TouchableOpacity>
      </View>
      )}
      </View>

      {/* Location Modal */}
      <Modal
        visible={showLocationModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowLocationModal(false)}
      >
        <View style={styles.modalOverlayLocation}>
          <View style={styles.modalContainerLocation}>
            <Text style={styles.modalTitle}>{name}</Text>

            <View style={styles.toggleContainer}>
              <Text style={styles.toggleLabel}>Enable Location Alerts</Text>
              <Switch
                value={tempLocationAlert}
                onValueChange={setTempLocationAlert}
                trackColor={{ false: '#ccc', true: '#007AFF' }}
                thumbColor={tempLocationAlert ? '#fff' : '#f4f3f4'}
              />
            </View>

            <View style={styles.modalButtons}>
              <Pressable onPress={() => setShowLocationModal(false)} style={styles.cancelButton}>
                <Text style={styles.cancelText}>Cancel</Text>
              </Pressable>
              <Pressable  
                onPress={async () => {
                  setLocationAlert(tempLocationAlert);
                  setShowLocationModal(false);
                
                  const token = await Utils.getValueFor('access_token');
                  try {
                    await axios.patch(`${Utils.currentPath}items/${item_id}/geo`, {
                      geo_alert: tempLocationAlert,
                      list_id: list_id,
                    }, {
                      headers: { token },
                    });
                  } catch (err) {
                    console.error('[UPDATE ITEM GEO ALERT FAILED]', err);
                  }
                }}
              style={styles.saveButton}>
                <Text style={styles.saveText}>Save</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      {/* Deadline Modal */}
      <Modal
        visible={showDeadlineModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowDeadlineModal(false)}
      >
        <View style={styles.modalOverlayDeadline}>
          <View style={styles.modalContainerDeadline}>
            <Text style={styles.modalTitle}>{name}</Text>
            <View style={styles.toggleContainer}>
              <Text style={styles.toggleLabel}>Enable Deadline Alerts</Text>
              <Switch
                value={tempDeadlineAlert}
                onValueChange={(val) => {
                  setTempDeadlineAlert(val);
                  if (!val) setTempDeadline(null);
                }}
                trackColor={{ false: '#ccc', true: '#007AFF' }}
                thumbColor={tempDeadlineAlert ? '#fff' : '#f4f3f4'}
              />
            </View>

            {tempDeadlineAlert && (
              <>
                <Text style={styles.toggleLabel}>Deadline:</Text>

                {Platform.OS === 'ios' && (
                  <DateTimePicker
                    value={tempDeadline || new Date()}
                    mode="datetime"
                    display="spinner"
                    onChange={(event, selectedDate) => {
                      if (selectedDate) setTempDeadline(selectedDate);
                    }}
                    style={{ backgroundColor: '#fff' }}
                  />
                )}

                {Platform.OS === 'android' && (
                  <Pressable onPress={showAndroidDateTimePicker} style={styles.deadlineButton}>
                    <Text style={styles.deadlineText}>
                      {tempDeadline ? tempDeadline.toLocaleString() : 'Pick date & time'}
                    </Text>
                  </Pressable>
                )}

                {Platform.OS === 'web' && (
                  <>
                    <TextInput
                      placeholder="YYYY-MM-DD HH:MM"
                      value={tempDeadline ? tempDeadline.toLocaleString() : ''}
                      onChangeText={(text) => {
                        const parsed = new Date(text);
                        if (!isNaN(parsed.getTime())) setTempDeadline(parsed);
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

            <View style={styles.modalButtons}>
              <Pressable onPress={() => setShowDeadlineModal(false)} style={styles.cancelButton}>
                <Text style={styles.cancelText}>Cancel</Text>
              </Pressable>
              <Pressable 
              onPress={async () => {
                setDeadlineAlert(tempDeadlineAlert);
                setDeadlineDate(tempDeadline);
                setShowDeadlineModal(false);
              
                const token = await Utils.getValueFor('access_token');
                try {
                  await axios.patch(`${Utils.currentPath}items/${item_id}/deadline`, {
                    deadline: tempDeadline
                      ? tempDeadline.toLocaleString('sv-SE').replace('T', ' ')
                      : null,
                      list_id: list_id,
                  }, {
                    headers: { token },
                  });
                } catch (err) {
                  console.error('[UPDATE ITEM DEADLINE FAILED]', err);
                }
              }}
              style={styles.saveButton}>
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
  modalOverlayLocation: {
    flex: 1,
    justifyContent: 'center', // במקום 'flex-end'
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  modalContainerLocation: {
    width: '80%',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 16,
    elevation: 5, // לאנדרואיד
    shadowColor: '#000', // לאייפון
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
  },

  modalOverlayDeadline: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end', // שינוי קריטי — במקום 'center'
  },
  modalContainerDeadline: {
    backgroundColor: '#fff',
    padding: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    width: '100%', // פריסה רוחבית מלאה
    minHeight: '40%', // גובה נוח לחלק תחתון
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
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