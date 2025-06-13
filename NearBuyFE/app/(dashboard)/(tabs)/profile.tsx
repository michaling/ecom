// app/(tabs)/profile.tsx

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Switch,
  TouchableOpacity,
  TextInput,
  Modal,
  TouchableWithoutFeedback,
  Keyboard,
  ImageBackground,
} from 'react-native';
import { MaterialCommunityIcons, FontAwesome5 } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import axios from 'axios';
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

  const handleLogout = () => {
    // TODO: Add your logout logic here
    //router.replace('../login'); // Example navigation to login screen
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
                
            <FontAwesome5 name="pencil-alt" size={18} color="gray" style={{ marginLeft: 8 }} />
                <Text style={styles.name}>{displayName ? displayName : "User Name"}</Text>
            </View>
        </TouchableOpacity>)}
      </View>

      {/* Location Alert Switch */}
      <View style={styles.settingRow}>
        <Text style={styles.settingLabel}>Enable location-based notifications by default</Text>
        <Switch
          value={locationEnabled}
          onValueChange={async (val) => {
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
      <MaterialCommunityIcons name="logout-variant" size={24} color="gray" />
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
      marginTop: 100,
      backgroundColor: '#FAFAFA',
      justifyContent: 'center',
      borderRadius: 15,
      shadowColor: 'gray',
      shadowRadius: 9,
      shadowOpacity: 0.5,
      
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
      marginLeft: 13,
      
    },
    settingRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginVertical: 18,
      marginHorizontal: 5,
      marginRight:40,
    },
    settingLabel: {
      fontSize: 17,
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
      marginLeft: 12,
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
      },
    nameRow: {
        flexDirection: 'row',
        alignItems: 'center',

    },
    image: {
        flex: 1,
    },
  });
  