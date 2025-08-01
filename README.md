# NearBuy

NearBuy is a location-based shopping recommendation app that helps you discover items on your lists when you’re near stores where they’re available. The system consists of three main components:

1. **Model Service**: A machine learning API that recommends product and predicts item availability based on store data.
2. **Backend Service**: A FastAPI application handling user lists, notifications, and integrating with Supabase.
3. **Frontend App**: A React Native (Expo) client for users to manage lists and receive location alerts.

---

## Architecture Overview

```plaintext
+------------+        +-------------+        +-------------+
|  Frontend  | <--->  |   Backend   | <--->  |  Model API  |
|  (Expo)    |        |  (FastAPI)  |        | (uvicorn)   |
+------------+        +-------------+        +-------------+
        |                    |                      |
        v                    v                      v
    Expo Go / Dev        Supabase DB           Model Weights
```

* The **Frontend** communicates with the **Backend** over HTTP.
* The **Backend** stores data in **Supabase** and calls the **Model API** for recommendations.
* The **Model API** loads a trained model and serves predictions.

---

## Prerequisites

* **Node.js** (v14+)
* **Expo CLI**: `npm install -g expo-cli`
* **Python** (v3.10+)
* **pip** or **pipenv** (for Python dependencies)

---

## Getting Started
Navigate to the project’s root

# Install dependencies
pip install -r requirements.txt

### 1. Local URL for Emulator / Device

Pick the correct backend URL for your environment in NearBuyFE.utils and leave only that line active:
   - Android emulator
   - Physical Android device via USB

at:   
export const currentPath =
    'http://10.0.2.2:8001/' // for Android emulator (replace with your IP)
    'http://10.0.0.49:8001/' // for phone via USB / expo go app
    'http://localhost:8001/' // for web


### 2. Configure Environment Variables

Paste the `.env` file in the root directory.

## Model Service

This service loads the ML model and exposes endpoints for predicting item availability.

```bash

# Start the API
uvicorn ml_component.api.model_fastapi_server:app --reload --port 8000
```

## Backend Service

The FastAPI backend handles list management, user profiles, and notifications.

```bash

# Start the app
uvicorn NearbuyBE.app.main:app --reload --port 8001
```

## Frontend App

The React Native app built with Expo.

Notifications are currently available only in Expo Dev on Android due to cost restrictions.

```bash
# Navigate to frontend folder
cd NearBuyFE

# Install dependencies
npm install
# or yarn install

# Start Expo
npx expo run android
```

* Scan the QR code for phisical mobile or press `a` to open in an emulator.
* Ensure the **Backend** (`localhost:8001`) and **Model API** (`localhost:8000`) are running.

---

## Running the Full Stack

1. **Model Service** (port 8000)
2. **Backend Service** (port 8001)
3. **Expo Frontend** (Expo CLI)

In separate terminals or via a process manager (e.g., `tmux`, `Docker`, or `pm2`), start each component in order. Then open the Expo app and log in or sign up to begin.
