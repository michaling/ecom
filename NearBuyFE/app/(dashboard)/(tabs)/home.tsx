import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useFocusEffect } from '@react-navigation/native';
import {
  View, Text, Pressable, StyleSheet, FlatList, Image, Modal, TouchableOpacity, TextInput, Switch, Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Utils from '../../../utils/utils';
import ListCard from '@/components/ListCard';
import { AntDesign, MaterialIcons } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { DateTimePickerAndroid } from '@react-native-community/datetimepicker';
import { Alert } from 'react-native';
import * as Notifications from 'expo-notifications';
import { I18nManager } from 'react-native';

// Ensure RTL support is disabled
//I18nManager.allowRTL(false);
//I18nManager.forceRTL(false);
const IMAGE_POOL = Array.from({ length: 11 }, (_, i) => `bg${i + 1}.png`);

const CARD_COLORS = [
  '#FFE3E3', '#FFCDB3', '#FFEABE',
  '#DAEDCE', '#C8E2FC', '#C8A2C8'
];

const getRandomPastelColor = () => {
  const hue = Math.floor(Math.random() * 360); // Random hue
  return `hsl(${hue}, 70%, 85%)`;              // Pastel shade
}; 

export default function HomeScreen() {
  const router = useRouter();
  const [lists, setLists] = useState<any[]>([]);
  const [isAddModalVisible, setAddModalVisible] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [isLocationEnabled, setLocationEnabled] = useState(false);
  const [deadline, setDeadline] = useState<Date | null>(null);
  const [isDeadlineEnabled, setIsDeadlineEnabled] = useState(false);
  const [isDatePickerVisible, setDatePickerVisible] = useState(false);
  const [defaultGeoAlert, setDefaultGeoAlert] = useState<boolean>(false);
  const [anyGeoEnabled, setAnyGeoEnabled] = useState(false);
  const [displayName, setDisplayName] = useState('');
  Utils.registerForPushNotificationsAsync();

  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldPlaySound: true,
      shouldSetBadge: false,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });
  
  const resetForm = () => {
    setNewListName('');
    setLocationEnabled(false);
    setDeadline(null);
    setIsDeadlineEnabled(false);
    setDatePickerVisible(false);
  };

  // fetch once each time Home gains focus
  const fetchLists = React.useCallback(async () => {
    try {
      console.log('[HOME] fetching lists …');
      const [user_id, token] = await Promise.all([
        Utils.getValueFor('user_id'),
        Utils.getValueFor('access_token'),
      ]);
      if (!token || !user_id) {
        console.warn('[HOME] no user or token'); return;
      }

      const res = await axios.get(Utils.currentPath + 'lists', {
        params: { user_id },
        headers: { token },
      });

      const rawLists = res.data.lists;
      setAnyGeoEnabled(res.data.any_geo_enabled ?? false);

      const listsWithColors = rawLists.map((it: any, idx: number) => ({
        ...it,
        color: CARD_COLORS[idx % CARD_COLORS.length],
      }));
      setLists(listsWithColors);
      
    } catch (err) {
      console.error('[HOME] fetch error', err);
    }
  }, []);

  const fetchProfile = React.useCallback(async () => {
    const token = await Utils.getValueFor('access_token');
    if (!token) return;
  
    try {
      const res = await axios.get(`${Utils.currentPath}profile`, { headers: { token } });
      setDefaultGeoAlert(res.data.geo_alert ?? false);
      setDisplayName(res.data.display_name || '');
    } catch (err) {
      console.error('[HOME] profile load failed', err);
    }
  }, []);

  const checkBackgroundPermissionIfNeeded = async () => {
    if (!anyGeoEnabled) return;
  
    const wasAsked = await Utils.wasAskedForBgPermission();
    if (wasAsked) return;
  
    Alert.alert(
      "Allow location access?",
      "To get alerts near stores, the app needs location access at all times. Update your settings?",
      [
        {
          text: "Cancel",
          style: "cancel",
          onPress: () => {
            Utils.markAskedForBgPermission();
          }
        },
        {
          text: "Allow",
          onPress: async () => {
            const granted = await Utils.requestBackgroundLocationPermission();
            await Utils.markAskedForBgPermission();
  
            if (!granted) {
              console.warn('User denied background permission');
            }
          }
        }
      ]
    );
  };

  useFocusEffect(
    React.useCallback(() => {
      const run = async () => {
        await fetchLists();
        await checkBackgroundPermissionIfNeeded();
        await fetchProfile();
      };
      run();
    }, [fetchLists, fetchProfile])
  );
  

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


  const renderItem = ({ item }: any) => <ListCard list={item} />;

  const sendTestNotification = async () => {
    console.log('[TEST] Sending notification');
    const perm = await Notifications.getPermissionsAsync();
    console.log('[PERM]', perm);
  
    await Notifications.scheduleNotificationAsync({
      content: {
        title: '🛒 Reminder!',
        body: 'This is your test NearBuy notification',
        sound: 'default',
      },
      trigger: {seconds : 1}, // fire immediately
    });
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <View style={styles.logoContainer}>
      <Image
        style={styles.logo}
        source={require('../../../assets/images/logo1.png')}/>
        <View style={{alignItems: 'center', justifyContent: 'center'}}> 
        <Text style={styles.logoText}>NearBuy</Text>
        <Text style={styles.logoSubtitle}>NEED IT. NEAR IT. GET IT.</Text>
        </View>
      </View>

      <View style={styles.header}> 
        <Text style={styles.text1}> Welcome back {displayName || 'User'}, </Text>
        <Text style={styles.text2}> What are you gonna buy today? </Text>
      </View>

      <View style={styles.toolsRow}>
        <TouchableOpacity style={styles.toolButton} onPress={sendTestNotification}>
          <Text style={styles.toolButtonText}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.toolButton} 
          onPress={() => {
            setLocationEnabled(defaultGeoAlert);
            setAddModalVisible(true);
          }}
          >
          <MaterialIcons name="format-list-bulleted-add" size={28} color="#5067B2" />
        </TouchableOpacity>

      </View>

      <FlatList
        data={lists}
        renderItem={renderItem}
        keyExtractor={(list) => list.id}
        numColumns={2}
        contentContainerStyle={styles.grid}
        columnWrapperStyle={styles.row}
        showsVerticalScrollIndicator={false}
      />

      <Modal
        visible={isAddModalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => setAddModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContainer}>
            <Text style={styles.modalTitle}>Create a New List</Text>

            {/* Input for list name */}
            <TextInput
              placeholder="List Name"
              value={newListName}
              onChangeText={setNewListName}
              style={styles.input}
            />

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

            {/* Action buttons */}
            <View style={styles.modalButtons}>
              <Pressable
                onPress={() => {
                  resetForm();
                  setAddModalVisible(false);
                }}
                style={styles.cancelButton}
              >
                <Text style={styles.cancelText}>Cancel</Text>
              </Pressable>

              <Pressable
                onPress={async () => {
                  try {
                    if (!newListName.trim()) {
                      Alert.alert('Missing Name', 'Please enter a name for your list.');
                      return;
                    }

                    if (isDeadlineEnabled && !deadline) {
                      Alert.alert('Incomplete Deadline', 'Please pick a deadline date and time');
                      return;
                    }

                    const token = await Utils.getValueFor('access_token');
                    const user_id = await Utils.getValueFor('user_id');
                    const listCount = lists.length;
                    const selectedImage = IMAGE_POOL[listCount % IMAGE_POOL.length];


                    await axios.post(`${Utils.currentPath}lists`, {
                      name: newListName,
                      geo_alert: isLocationEnabled,
                      deadline: isDeadlineEnabled && deadline
                      ? deadline.toLocaleString('sv-SE').replace('T', ' ')
                      : null,
                      pic_path: selectedImage,
                    }, {
                      params: { user_id },
                      headers: { token }
                    });

                    resetForm();
                    setAddModalVisible(false);
                    fetchLists(); // refresh
                  } catch (err) {
                    console.error('[CREATE LIST FAILED]', err);
                  }
                }}
                style={styles.saveButton}
              >
                <Text style={styles.saveText}>Save</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>


    </SafeAreaView>
  );
}

const CARD_WIDTH = '48%';
const COLORS = ['#FFE3E3', '#FFCDB3', '#FFEABE', '#DAEDCE', '#C8E2FC', '#C8A2C8'];


const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FBF8FF',
    //backgroundColor: '#FAFAFA',
    paddingHorizontal: 14,
    
  },
  grid: {
    paddingBottom: 100,
  },
  row: {
    justifyContent: 'space-between',
    marginBottom: 16,
    paddingHorizontal: 2,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
    marginTop: 10,
  },
  logoText: {
    fontSize: 27,
    fontWeight: 'bold',
    color: '#5067b2',
    marginLeft: 5,
    marginTop: 10,
  },
  logoSubtitle: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#F36D9A',
    
  },
  toolsRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 5,
    marginBottom: 8,
    marginTop: 10,
  },
  toolButton: {
    //backgroundColor: '#fff',
    //borderColor: '#444',
    //borderWidth: 1,
    //borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  toolButtonText: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#5067B2'
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
    minHeight: '70%',
    maxHeight: '90%',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    color: '#332F6E',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
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
    backgroundColor: '#B25FC3',
    padding: 10,
    borderRadius: 8,
  },
  saveText: {
    fontSize: 16,
    color: '#fff',
  },

  toggleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
    marginRight: 16,
  },

  toggleLabel: {
    fontSize: 16,
    marginLeft: 16,
  },

  logo: {
    width: 37,
    height: 60,
    marginBottom: 16,
  },
  text1: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#332F6E',
    marginBottom: 2,
  },
  text2: {
    fontSize: 16,
    //fontWeight: 'bold',
    color: '#332F6E',
    marginLeft: 30,
  },
  header: {
    justifyContent: 'center',
    marginBottom: 18,
    marginHorizontal: 30,
  },
});
