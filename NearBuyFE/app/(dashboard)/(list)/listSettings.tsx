import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useFocusEffect } from '@react-navigation/native';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  FlatList,
  ImageBackground,
  Modal,
  TouchableOpacity,
  TextInput,
  Switch,
  Platform,
  TouchableWithoutFeedback,
  Keyboard,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Utils from '../../../utils/utils';
import DateTimePicker from '@react-native-community/datetimepicker';
import { DateTimePickerAndroid } from '@react-native-community/datetimepicker';
import Ionicons from '@expo/vector-icons/Ionicons';



export default function ListSettingsScreen() {
  const { list_id, list_name, list_color } = useLocalSearchParams();
  const [listName, setListName] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isLocationEnabled, setLocationEnabled] = useState(false);
  const [deadline, setDeadline] = useState<Date | null>(null);
  const [isDeadlineEnabled, setIsDeadlineEnabled] = useState(false);
  const [showIOSPicker, setShowIOSPicker] = useState(false);


  const router = useRouter();


  const handleEndEditing = () => {
    setIsEditing(false);

  };

  const showAndroidDateTimePicker = () => {
    // First: pick date
    DateTimePickerAndroid.open({
      value: deadline || new Date(),
      mode: 'date', 
      is24Hour: true,
      onChange: (event, selectedDate) => {
        if (event.type === 'set' && selectedDate) {
          // Second: pick time
          DateTimePickerAndroid.open({
            value: selectedDate,
            mode: 'time', 
            is24Hour: true,
            onChange: (event2, selectedTime) => {
              if (event2.type === 'set' && selectedTime) {
                // Combine date + time
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

  return (   
    <>
     <View style={styles.headerRow}>
    <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
    <Ionicons name="chevron-back-outline" size={24} color="#007AFF" />
        <Text style={styles.backText}>Back</Text>
    </TouchableOpacity>
    </View>
    
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        


    <View style={[styles.container]}>
        <View>
        <Text style={styles.title}>Settings</Text>
        {isEditing ? (
            <TextInput
                value={listName}
                onChangeText={setListName}
                onBlur={handleEndEditing}
                autoFocus
                style={styles.input}
            />
            ) : (
            <TouchableOpacity onPress={() => setIsEditing(true)}>
                <Text style = {styles.subtitle}> {listName? listName : "List Name"}</Text>
            </TouchableOpacity>
            )}
        </View>
        {/* Location-based toggle */}
        <View style={styles.toggleContainer}>
              <Text style={styles.toggleLabel}> Location Alerts </Text>
              <Switch
                value={isLocationEnabled}
                onValueChange={() => setLocationEnabled(!isLocationEnabled)}
                trackColor={{ false: '#ccc', true: '#007AFF' }}
                thumbColor={isLocationEnabled ? '#fff' : '#f4f3f4'}
              />
            </View>
            {/* Deadline picker */}
            <View style={{ marginBottom: 12 }}>
              <View style={styles.toggleContainer}>
                <Text style={styles.toggleLabel}> Deadline Alerts </Text>
                <Switch
                  value={isDeadlineEnabled}
                  onValueChange={(val) => {
                    setIsDeadlineEnabled(val);
                    if (!val) setDeadline(null); // Clear if disabled
                  }}
                  trackColor={{ false: '#ccc', true: '#007AFF' }}
                  thumbColor={isDeadlineEnabled ? '#fff' : '#f4f3f4'}
                />
              </View>

              {isDeadlineEnabled && (
              <>
                

                {Platform.OS === 'ios' && (
                <>
                    <TouchableOpacity onPress={() => setShowIOSPicker(!showIOSPicker)} style={styles.deadlineButton}>
                        <Text style={styles.deadlineText}>
                            {deadline ? deadline.toLocaleString('en-GB', { dateStyle: 'full', timeStyle:'short'}) : 'Pick date & time'}
                        </Text>
                    </TouchableOpacity>

                    {showIOSPicker && (
                    <>
                        <DateTimePicker
                        value={deadline || new Date()}
                        mode="datetime"
                        display="spinner"
                        onChange={(event, selectedDate) => {
                            if (selectedDate) setDeadline(selectedDate);
                        }}
                        
                        />
                        <TouchableOpacity onPress={() => setShowIOSPicker(false)} style={styles.doneButton}>
                        <Text style={styles.doneButtonText}>Done</Text>
                        </TouchableOpacity>
                    </>
                    )}
                </>
                )}



                {Platform.OS === 'android' && (
                  <Pressable onPress={showAndroidDateTimePicker} style={styles.deadlineButton}>
                    <Text style={styles.deadlineText}>
                      {deadline ? deadline.toLocaleString('en-GB', { dateStyle: 'full', timeStyle:'short'}) : 'Pick date & time'}
                    </Text>
                  </Pressable>
                )}


                {Platform.OS === 'web' && (
                  <>
                  <TextInput
                    placeholder="YYYY-MM-DD HH:MM"
                    value={deadline ? deadline.toLocaleString('en-GB', { dateStyle: 'full', timeStyle:'short'}) : ''}
                    onChangeText={(text) => {
                      const parsed = new Date(text);
                      if (!isNaN(parsed.getTime())) {
                        setDeadline(parsed);
                      }
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
            </View>
            <TouchableOpacity onPress={() => ('//TODO: delete list')}>
                <Text style = {styles.deleteText}> Delete List </Text>
            </TouchableOpacity>
            
          </View>
          
          </TouchableWithoutFeedback>
          </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 100,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 35,
    fontWeight: 'bold',
    marginBottom: 40,
    marginLeft: 10,
  },
  subtitle: {
    fontSize: 20,
    textAlign: 'center',
    fontWeight: 'bold',
    marginBottom: 30,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    fontSize: 18,
    padding: 10,
    marginBottom: 12,
  },
    deadlineButton: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
  },

  deadlineText: {
    fontSize: 16,
    textAlign: 'center',
    padding: 10,
    color: '#007AFF'
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
    paddingHorizontal: 20,
  },

  toggleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
    marginRight: 16,
  },

  toggleLabel: {
    fontSize: 18,
    marginLeft: 16,
  },

  deleteText: {
    fontSize: 18,
    marginLeft: 16,
    color: 'red',
  },
  doneButton: {
    marginTop: 10,
    alignSelf: 'center',
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 10,
  },
  
  doneButtonText: {
    color: 'green',
    fontSize: 16,
    fontWeight: 'bold',
  },
  
  headerRow: {
    position: 'absolute',
    top: 50,
    left: 15,
    zIndex: 10,
  },
  
  backButton: {
    padding: 6,
    flexDirection: 'row',
    alignItems: 'center',
  },
  
  backText: {
    fontSize: 18,
    color: '#007AFF',
    fontWeight: '500',
  }
  
});