import requests

base_url = "http://127.0.0.1:8000/auth"

# Password too short
r = requests.post(f"{base_url}/signup", json={
    "email": "tester123@gmail.com",
    "password": "1"})
if r.status_code == 200:
    print(r.json())
else:
    print(f"{r.status_code}: {r.text}")

# Already exists
r = requests.post(f"{base_url}/signup", json={
    "email": "tester@gmail.com",
    "password": "123456789"})
if r.status_code == 200:
    print(r.json())
else:
    print(f"{r.status_code}: {r.text}")

# Should work
r = requests.post(f"{base_url}/signup", json={
    "email": "tester3@gmail.com",
    "password": "123456789"})
if r.status_code == 200:
    print(r.json())
else:
    print(f"{r.status_code}: {r.text}")

# User doesn't exist
r = requests.post(f"{base_url}/signin", json={
    "email": "whoami@gmail.com",
    "password": "MySecurePass123"})
if r.status_code == 200:
    print(r.json())
else:
    print(f"{r.status_code}: {r.text}")


# Wrong password
r = requests.post(f"{base_url}/signin", json={
    "email": "tester3@gmail.com",
    "password": "123456788"})
if r.status_code == 200:
    print(r.json())
else:
    print(f"{r.status_code}: {r.text}")

# Should work
r = requests.post(f"{base_url}/signin", json={
    "email": "tester3@gmail.com",
    "password": "123456789"})
if r.status_code == 200:
    print(r.json())
else:
    print(f"{r.status_code}: {r.text}")
