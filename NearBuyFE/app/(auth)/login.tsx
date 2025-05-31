import React, { useState } from 'react';
import { View, Text, TextInput, Pressable, StyleSheet, Alert } from 'react-native';
import axios, { AxiosError } from 'axios';
import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Please fill in both fields');
      return;
    }
  
    try {
      //const res = await axios.post('http://10.0.2.2:8000/auth/signin', { email, password }); // for Android emulator
      const res = await axios.post('http://10.0.0.49:8000/auth/signin', { email, password }); // for Android live via USB - change to your machine's IP (ipconfig -> IPv4 Address)
      //const res = await axios.post('http://localhost:8000/auth/signin', { email, password }); // for web or iOS simulator

      console.log('[LOGIN SUCCESS]', res.data);
      await SecureStore.setItemAsync('user_id', res.data.user_id);  // Save user ID to secure storage
      await SecureStore.setItemAsync('access_token', res.data.access_token); // Save access token to secure storage
      router.push('/home');
    } catch (err) {
      const error = err as AxiosError;
      const detail = (error.response?.data as { detail?: string })?.detail;
      Alert.alert('Login failed', detail || 'Unknown error');
      //Alert.alert('Login failed', error.response?.data?.detail || 'Unknown error');
      //console.log('Login failed: ', error.response?.data?.detail || 'Unknown error');
      console.log('Login failed: ', detail || 'Unknown error');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to NearBuy </Text>
      <Text style={styles.subtitle}>Login to your account</Text>

      <TextInput
        placeholder="Email"
        style={styles.input}
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      <TextInput
        placeholder="Password"
        secureTextEntry
        style={styles.input}
        value={password}
        onChangeText={setPassword}
      />

      <Pressable style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>LOGIN</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    backgroundColor: '#FAFAFA',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 24,
    color: '#666',
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
    backgroundColor: '#C8A2C8',
    borderRadius: 50,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
  
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
    marginTop: 20
  },
  footerText: {
    fontSize: 14,
    color: '#555',
  },
  footerLink: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '500',
  },
});
