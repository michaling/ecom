import { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Pressable, Alert, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Switch } from 'react-native';
import * as SecureStore from 'expo-secure-store'; // For saving login state later
import axios, { AxiosError } from 'axios';
import * as Utils from '../../utils/utils';


export default function RegisterScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  //const [phoneNumber, setNumber] = useState(''); // Delete later
  const [userName, setUserName] = useState('');
  const [isLocationEnabled, setIsLocationEnabled] = useState(true); // default: ON

  //Email format check
  const isValidEmail = (email: string) => {
    return /\S+@\S+\.\S+/.test(email);
  };

  //Phone number format (digits only, 9–15 digits) // Delete later
  // const isValidPhone = (phone: string) => {
  //   return /^\d{9,15}$/.test(phone);
  // };


  // TODO: Strong password validation



  //check inputs validations
  const handleRegister = async () => {
    if (!email || !password || !confirmPassword || !userName) {
      Alert.alert('Error', 'Please fill out all fields.');
      return;
    }
  
    if (!isValidEmail(email)) {
      Alert.alert('Error', 'Please enter a valid email address.');
      return;
    }
  
    // Delete later
    // if (!isValidPhone(phoneNumber)) {
    //   Alert.alert('Error', 'Please enter a valid phone number.');
    //   return;
    // }
  
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match.');
      return;
    }
  
    try {
      const res = await axios.post(
         Utils.currentPath + 'auth/signup',
        {
          email,
          password,
          //phone: phoneNumber, // Delete later
          display_name: userName,
          geo_alert: isLocationEnabled,
        }
      );
      console.log('[SIGNUP SUCCESS]', res.data);
      await Utils.save('user_id', res.data.user_id); // Save user ID to secure storage
      await Utils.save('access_token', res.data.access_token); // Save access token to secure storage
      router.push('/(dashboard)/(tabs)/home');
  
    } catch (err) {
      const error = err as AxiosError<{ detail: string }>;
      console.log(error);
      console.log(err);
      console.log('[SIGNUP ERROR]', error.response?.data?.detail || 'Unknown error');
      Alert.alert('Signup failed', error.response?.data?.detail || 'Unknown error');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Create Account</Text>
      <TextInput
        placeholder="Name"
        style={styles.input}
        keyboardType="default" //capitalize first letter of names
        autoCapitalize="words"
        value={userName}
        onChangeText={setUserName}
      />
      <TextInput
        placeholder="Email"
        style={styles.input}
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      {/* Delete later */}
      {/* <TextInput
        placeholder="Phone number"
        keyboardType="phone-pad"
        style={styles.input}
        value={phoneNumber}
        onChangeText={setNumber}
      /> */}
      <TextInput
        placeholder="Password"
        secureTextEntry
        style={styles.input}
        value={password}
        onChangeText={setPassword}
      />
      <TextInput
        placeholder="Confirm Password"
        secureTextEntry
        style={styles.input}
        value={confirmPassword}
        onChangeText={setConfirmPassword}
      />

      <View style={styles.toggleContainer}>
        <Text style={styles.toggleLabel}>Want to turn on location-based notifications by default?</Text>
        <Switch
          value={isLocationEnabled}
          onValueChange={setIsLocationEnabled}
          trackColor={{ false: '#ccc', true: '#4CAF50' }}
          thumbColor={isLocationEnabled ? '#fff' : '#f4f3f4'}
        />
      </View>

      <View style={styles.underToggle}> 
        <Text style={styles.smallerToggleLabel}>Don't worry - you can always turn this off later</Text>
      </View>

      <TouchableOpacity style={styles.button} onPress={handleRegister}>
        <Text style={styles.buttonText}>REGISTER</Text>
      </TouchableOpacity>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Already have an account?</Text>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.footerLink}> Login</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1,
    justifyContent: 'center', 
    padding: 24, 
    backgroundColor: '#FAFAFA'
  },
  title: { 
    fontSize: 28, 
    fontWeight: 'bold', 
    textAlign: 'center', 
    marginBottom: 24, 
    color: '#333' 
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#D1F0E5', // 🔁 Change to your preferred color
    borderRadius: 50,           // Fully rounded
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    margin: 10,
  
    // Shadow for iOS
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
  
    // Shadow for Android
    elevation: 5,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: { 
    flexDirection: 'row', 
    justifyContent: 'center', 
    marginTop: 16 
  },
  footerText: { 
    fontSize: 14, 
    color: '#555' 
  },
  footerLink: { 
    fontSize: 14, 
    color: '#007AFF', 
    fontWeight: '500' 
  },

  toggleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
    marginRight: 60,
    marginLeft: 16,
  },
  
  toggleLabel: {
    fontSize: 14,
    color: '#333',
  },
  underToggle: { 
    flexDirection: 'row', 
    justifyContent: 'center',
    marginBottom: 12,
  },
  smallerToggleLabel: {
    fontSize: 12,
    color: '#333',
  },
});
