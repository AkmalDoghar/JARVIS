# 🏍️ JARVIS Mobile Companion — Bike & Travel Edition

A hands-free, voice-controlled Android companion for **Muhammad Akmal ([@AkmalDoghar](https://github.com/AkmalDoghar))** designed specifically for bike rides, travel, and on-the-go lifestyle with Bluetooth helmet/earphone controls.

---

## ⚡ Key Capabilities

### 1. 🎵 Phone Storage Music Player
* **Storage Scan:** Automatically detects audio tracks stored in `/Music`, `/Download`, and phone storage.
* **Favorite Tracks:** Quick-access playlist for your top riding beats.
* **Hands-Free Playback:** Background audio service keeps music playing while phone is in pocket or mounted.

### 2. 📞 Voice Dialing & Phone Calls
* **Phonebook Integration:** Automatically syncs contacts and resolves spoken names (e.g. *"Ali ko call milao"*, *"Bhai ko phone karo"*).
* **Direct Dialing:** Initiates calls immediately without looking at the screen.
* **Call Disconnect:** Voice command to dismiss/end call (*"Call band kr do"*).

### 3. 💬 WhatsApp Integration
* **Voice Messages:** *"WhatsApp message Ali Salam kahan ho"*
* **Voice Calls:** *"WhatsApp call Ali"*

### 4. 🚀 Quick App Launchers
* **Gallery:** *"Gallery kholo"*
* **Camera:** *"Camera on karo"*
* **Maps / Navigation:** *"Maps kholo"*

---

## 🎙️ Supported Voice Commands (Roman Urdu & English)

| Intent | Spoken Voice Command Examples |
|---|---|
| **Play Favorites** | *"Mere favourite songs play kro"*, *"Gana chalao"*, *"Music play karo"* |
| **Next Track** | *"Next kro"*, *"Agla gana"*, *"Skip song"* |
| **Previous Track** | *"Pichay kro"*, *"Pichla gana"*, *"Previous song"* |
| **Stop / Pause** | *"Stop kro"*, *"Pause karo"*, *"Gana roko"* |
| **Fast Forward** | *"Forword kro"*, *"15 second aage karo"* |
| **Rewind** | *"Backward kro"*, *"Peeche karo"* |
| **Make Call** | *"Ali ko call milao"*, *"Call Papa"*, *"Bhai ko phone karo"* |
| **End Call** | *"Call band kr do"*, *"Call kato"*, *"Disconnect call"* |
| **WhatsApp Call** | *"WhatsApp call Ali"*, *"WhatsApp per Ali ko call karo"* |
| **WhatsApp Msg** | *"WhatsApp message Ali"*, *"WhatsApp pe message bhejo"* |
| **Gallery** | *"Gallery kholo"*, *"Photos dikhao"* |
| **Camera** | *"Camera on karo"*, *"Photo khincho"* |
| **Maps** | *"Maps kholo"*, *"Navigation chalao"* |
| **Status Check** | *"JARVIS status"*, *"Battery check"*, *"Time kya hua hai"* |

---

## 🚀 How to Run on Your Phone

### Step 1: Start the Companion Server
Double-click:
```bash
start_jarvis_mobile.bat
```
*(Or in terminal: `cd mobile && npx expo start`)*

### Step 2: Open on Android Phone
1. Install **Expo Go** from Google Play Store on your phone.
2. Ensure phone and PC are connected to the same Wi-Fi.
3. Open Expo Go and scan the QR code displayed in the terminal.
4. JARVIS Mobile will load directly onto your phone!

### Step 3: Build Standalone APK (Optional)
To create a standalone `.apk` installable file on Android:
```bash
cd mobile
npx eas-cli build -p android --profile preview
```
