import { FontAwesome5 } from '@expo/vector-icons';
import Ionicons from '@expo/vector-icons/Ionicons';
import DateTimePicker, { DateTimePickerAndroid } from '@react-native-community/datetimepicker';
import axios from 'axios';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {ImageBackground, Keyboard, Platform, Pressable, StyleSheet, Switch, Text, TextInput, TouchableOpacity, TouchableWithoutFeedback, View} from 'react-native';
import * as Utils from '../../../utils/utils';



export default function ListSettingsScreen() {
  const { list_id, list_name, list_color } = useLocalSearchParams();
  const [listName, setListName] = useState(typeof list_name === 'string' ? list_name : '');
  const [isEditing, setIsEditing] = useState(false);
  const [isLocationEnabled, setLocationEnabled] = useState(false);
  const [deadline, setDeadline] = useState<Date | null>(null);
  const [isDeadlineEnabled, setIsDeadlineEnabled] = useState(false);
  const [showIOSPicker, setShowIOSPicker] = useState(false);
  const router = useRouter();


  const handleEndEditing = async () => {
    setIsEditing(false);
  
    if (!listName.trim() || listName === list_name) return;
  
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.patch(
        `${Utils.currentPath}lists/${list_id}/name`,
        { name: listName },
        { headers: { token } }
      );
    } catch (err) {
      console.error('[LIST NAME RENAME FAILED]', err);
    }
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
                updateDeadline(finalDate);
              }
            },
          });
        }
      },
    });
  };

  const updateDeadline = async (newDate: Date | null) => {
    const token = await Utils.getValueFor('access_token');
    const formatted = newDate
      ? newDate.toLocaleString('sv-SE').replace('T', ' ')
      : null;
  
    try {
      await axios.patch(`${Utils.currentPath}lists/${list_id}/deadline`, {
        deadline: formatted,
      }, {
        headers: { token },
      });
    } catch (err) {
      console.error('[UPDATE DEADLINE FAILED]', err);
    }
  };

  const deleteList = async () => {
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.delete(`${Utils.currentPath}lists/${list_id}`, {
        headers: { token },
      });
      router.replace('/home');
    } catch (err) {
      console.error('[DELETE LIST FAILED]', err);
    }
  };

  useEffect(() => {
    const fetchListSettings = async () => {
      const token = await Utils.getValueFor('access_token');
      if (!token) return;
  
      try {
        const res = await axios.get(`${Utils.currentPath}lists/${list_id}`, {
          headers: { token },
        });
  
        setListName(res.data.name);
        setLocationEnabled(res.data.geo_alert ?? false);
        if (res.data.deadline) {
          setDeadline(new Date(res.data.deadline));
          setIsDeadlineEnabled(true);
        }
  
      } catch (err) {
        console.error('[FETCH SETTINGS FAILED]', err);
      }
    };
  
    fetchListSettings();
  }, []);
  
  return (   
    <>
    <ImageBackground source={require('../../../assets/images/loginBG.png')} resizeMode="cover" style={styles.image}>

     <View style={styles.headerRow}>
    <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
    <Ionicons name="chevron-back-outline" size={24} color="#007AFF" />
        <Text style={styles.backText}>Back</Text>
    </TouchableOpacity>
    </View>
    
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>

    <View style={[styles.container]}>
        <View style={[{alignItems: 'center'}]}>
        <Text style={styles.title}>List Settings</Text>
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
              <View style={styles.nameRow}>
              <FontAwesome5 name="pencil-alt" size={19} color="#332F6E" style={{ marginRight: 5 }} />
                <Text style = {styles.subtitle}> {listName? listName : "List Name"}</Text>
                </View>
            </TouchableOpacity>
            
            )}
        </View>
        {/* Location-based toggle */}
        <View style={styles.toggleContainer}>
          <Text style={styles.toggleLabel}>Location Alerts</Text>
          <Switch
            value={isLocationEnabled}
            onValueChange={async (newValue) => {
              setLocationEnabled(newValue);

              const token = await Utils.getValueFor('access_token');
              try {
                await axios.patch(
                  `${Utils.currentPath}lists/${list_id}/geo`,
                  { geo_alert: newValue },
                  { headers: { token } }
                );
              } catch (err) {
                console.error('[UPDATE GEO ALERT FAILED]', err);
              }
            }}
            trackColor={{ false: '#ccc', true: '#007AFF' }}
            thumbColor={isLocationEnabled ? '#fff' : '#f4f3f4'}
          />
        </View>
            {/* Deadline picker */}
            <View style={{ marginBottom: 12 }}>
              <View style={styles.toggleContainer}>
                <Text style={styles.toggleLabel}>Deadline Alerts </Text>
                <Switch
                  value={isDeadlineEnabled}
                  onValueChange={async (val) => {
                    setIsDeadlineEnabled(val);
                  
                    if (val) {
                      if (Platform.OS === 'android') {
                        showAndroidDateTimePicker();
                      } else {
                        setShowIOSPicker(true);
                      }
                    } else {
                      setDeadline(null);
                      await updateDeadline(null);
                    }
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
                        minimumDate={new Date()}
                        onChange={(event, selectedDate) => {
                          if (selectedDate) {
                            setDeadline(selectedDate);
                            updateDeadline(selectedDate);
                          }
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
                        updateDeadline(parsed);
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
            <TouchableOpacity onPress={deleteList}>
              <Text style={styles.deleteText}>Delete List</Text>
            </TouchableOpacity>        
          </View>        
          </TouchableWithoutFeedback>
          </ImageBackground>
          </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 100,
    paddingHorizontal: 20
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 40,
    marginTop: 25,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#332F6E',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    fontSize: 18,
    padding: 10,
    marginBottom: 12,
    width: 220,
    textAlign: 'center',
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
    color: '#007AFF',
    marginTop: 10,
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
    marginBottom: 20,
    marginRight: 16,
  },
  toggleLabel: {
    fontSize: 18,
    marginLeft: 16,
  },
  deleteText: {
    fontSize: 18,
    textAlign: 'center',
    color: 'red',
    marginTop: 40,
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
  },
  image: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 50,
  },
});