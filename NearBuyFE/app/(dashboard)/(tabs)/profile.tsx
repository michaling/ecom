// app/(tabs)/profile.tsx

import { FontAwesome5, MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {
  ImageBackground,
  Keyboard,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Utils from '../../../utils/utils';

export default function ProfileScreen() {
  const [displayName, setDisplayName] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [tempName, setTempName] = useState(displayName);
  const [locationEnabled, setLocationEnabled] = useState(true);
  const router = useRouter();


  const handleEndEditing = () => {
    setIsEditing(false);
    handleSaveName();
  };


  const handleSaveName = async () => {
    setDisplayName(tempName);
    const token = await Utils.getValueFor('access_token');
    try {
      await axios.patch(`${Utils.currentPath}profile/display_name`, {
        display_name: tempName,
      }, {
        headers: { token },
      });
    } catch (err) {
      console.error('[SAVE NAME FAILED]', err);
    }
  };

  const handleLogout = async () => {
    try {
      await Utils.deleteValueFor('access_token');
      await Utils.deleteValueFor('user_id');
      router.replace('/login'); 
    } catch (err) {
      console.error('[LOGOUT FAILED]', err);
    }
  };


  
  useEffect(() => {
    const fetchProfile = async () => {
      const token = await Utils.getValueFor('access_token');
      try {
        const res = await axios.get(`${Utils.currentPath}profile`, {
          headers: { token },
        });
        setDisplayName(res.data.display_name || '');
        setTempName(res.data.display_name || '');
        setLocationEnabled(res.data.geo_alert ?? false);
      } catch (err) {
        console.error('[FETCH PROFILE FAILED]', err);
      }
    };
    fetchProfile();
  }, []);


  return (
    <ImageBackground source={require('../../../assets/images/profileBG.png')} resizeMode="cover" style={styles.image}>
    <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
      {isEditing ? (
                <TextInput
                value={tempName}
                onChangeText={setTempName}
                onBlur={handleEndEditing}
                autoFocus
                style={styles.input}
              />
            ) : (
        <TouchableOpacity onPress={() => setIsEditing(true)}>
            <View style={styles.nameRow}>
                
            <FontAwesome5 name="pencil-alt" size={19} color="#332F6E" style={{ marginRight: 5 }} />
                <Text style={styles.name}>{displayName}</Text>
            </View>
        </TouchableOpacity>)}
      </View>

      {/* Location Alert Switch */}
      <View style={styles.settingRow}>
        <Text style={styles.settingLabel}>Enable location-based notifications by default</Text>
        <Switch
          value={locationEnabled}
          trackColor={{ false: '#ccc', true: '#007AFF' }}
          onValueChange={async (val) => {
            if (val) {
              const granted = await Utils.ensureFullLocationPermissions();
              if (!granted) return; // Don’t allow enabling if permission denied
            }
          
            setLocationEnabled(val);
          
            const token = await Utils.getValueFor('access_token');
            try {
              await axios.patch(`${Utils.currentPath}profile/geo_alert`, {
                geo_alert: val,
              }, {
                headers: { token },
              });
            } catch (err) {
              console.error('[SAVE GEO FAILED]', err);
            }
          }}
        />
      </View>

      {/* Logout Button */}
      <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
      <View style={styles.nameRow}>
      <MaterialCommunityIcons name="logout-variant" size={24} color="red" />
        <Text style={styles.logoutText}>Log Out</Text>
        </View>
      </TouchableOpacity>
    </SafeAreaView>
    </TouchableWithoutFeedback>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
    container: {
      //flex: 1,
      padding: 24,
      marginHorizontal: 30,
      marginTop: 120,
      backgroundColor: '#FAFAFA',
      justifyContent: 'center',
      borderRadius: 15,
      shadowColor: 'gray',
      shadowRadius: 9,
      shadowOpacity: 0.5,
      elevation: 5,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 30,
    },
    name: {
      fontSize: 24,
      fontWeight: 'bold',
      marginLeft: 4,
      color: '#332F6E',
    },
    settingRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginVertical: 18,
      marginHorizontal: 5,
      marginRight: 50,
    },
    settingLabel: {
      fontSize: 15,
      color: '#332F6E',
    },
    logoutButton: {
      marginTop: 40,
      padding: 12,
      borderRadius: 8,
      alignItems: 'center',
    },
    logoutText: {
      color: 'red',
      fontWeight: 'bold',
      marginLeft: 6,
      fontSize: 15,
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
    nameRow: {
        flexDirection: 'row',
        alignItems: 'center',

    },
    image: {
        flex: 1,
    },
  });
  