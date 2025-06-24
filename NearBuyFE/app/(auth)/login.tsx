import React, { useState } from 'react';
import { Image, View, Text, TextInput, Pressable, StyleSheet, Alert, Platform, TouchableOpacity, ImageBackground } from 'react-native';
import axios, { AxiosError } from 'axios';
import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Utils from '../../utils/utils';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();
  const image = {};
  

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Please fill in both fields');
      return;
    }
  
    try {
      const res = await axios.post(Utils.currentPath + 'auth/signin', { email, password });

      console.log('[LOGIN SUCCESS]');
      await Utils.save('user_id', res.data.user_id); // Save user ID to secure storage
      await Utils.save('access_token', res.data.access_token); // Save access token to secure storage
      router.push('/(dashboard)/(tabs)/home');
    } catch (err) {
      const error = err as AxiosError;
      const detail = (error.response?.data as { detail?: string })?.detail;
      Alert.alert('Login failed', detail || 'Unknown error');
      console.log(err);
      console.log('Login failed: ', detail || 'Unknown error');
    }
  };

  return (
    <ImageBackground source={require('../../assets/images/loginBG.png')} resizeMode="cover" style={styles.image}>

    <View style={styles.container}>
    <View style={{alignItems: 'center'}}> 
      <Image
        style={styles.logo}
        source={require('../../assets/images/logo1.png')}/>
        </View>
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

      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>LOGIN</Text>
      </TouchableOpacity>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Don't have an account yet?</Text>
        <TouchableOpacity onPress={() => router.push('/register')}>
          <Text style={styles.footerLink}> Register</Text>
        </TouchableOpacity>
      </View>
    </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    
    //backgroundColor: '#FAFAFA',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
    color: '#5067b2',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 24,
    color: '#666',
    fontWeight: 'bold',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 16,
    backgroundColor: '#FAFAFA',
  },
  button: {
    backgroundColor: '#B25FC3',
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
  image: {
    flex: 1,
  },
  logo: {
    width: 64,
    height: 104,
    marginBottom: 16,
  },
});
