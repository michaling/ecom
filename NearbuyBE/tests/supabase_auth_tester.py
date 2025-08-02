import os
from dotenv import load_dotenv
from auth.logic import sign_up

load_dotenv()

try:
    print("➡️ Attempting signup via logic.py...")
    user = sign_up("tester3@gmail.com", "12345678!")
    print(f"ID: {user.id}")
    print(f"Email: {user.email}")
    print("✅ Signup successful:")
except Exception as e:
    print("❌ Signup failed:", e)
