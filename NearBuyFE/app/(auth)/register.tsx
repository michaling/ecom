import { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Pressable, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store'; // For saving login state later

export default function RegisterScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [phoneNumber, setNumber] = useState('');

  const handleRegister = async () => {
    if (!email || !password || !confirmPassword || !phoneNumber) {
      Alert.alert('Error', 'Please fill out all fields.');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match.');
      return;
    }

    // 💡 This is where you'd usually call your backend API to create the user.
    // For now, we simulate success and store a fake token.
    //await SecureStore.setItemAsync('userToken', 'dummy_token');

    // Navigate to home screen after "successful" registration
    router.replace('/home');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Create Account</Text>
      <TextInput
        placeholder="Email"
        style={styles.input}
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        placeholder="Phone number"
        secureTextEntry
        style={styles.input}
        value={phoneNumber}
        onChangeText={setNumber}
      />
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

      <Pressable style={styles.button} onPress={() => { /* handle register */ }}>
        <Text style={styles.buttonText}>REGISTER</Text>
      </Pressable>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Already have an account?</Text>
        <Pressable onPress={() => router.push('/login')}>
          <Text style={styles.footerLink}> Login</Text>
        </Pressable>
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
    backgroundColor: '#a8dadc', // 🔁 Change to your preferred color
    borderRadius: 50,           // Fully rounded
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
});
