/**
 * Safe Native Module Loader
 * Prevents Expo Go from crashing if a native binary module is missing.
 */

let AudioModule: any = null;
let MediaLibraryModule: any = null;
let ContactsModule: any = null;
let SpeechModule: any = null;
let IntentLauncherModule: any = null;
let KeepAwakeModule: any = null;
let HapticsModule: any = null;

// Safe load Audio (expo-av)
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const av = require('expo-av');
  AudioModule = av.Audio;
} catch (e) {
  console.warn('[JARVIS Core] ExponentAV native module not present in this Expo Go runtime. Falling back gracefully.');
}

// Safe load MediaLibrary (expo-media-library)
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  MediaLibraryModule = require('expo-media-library');
} catch (e) {
  console.warn('[JARVIS Core] MediaLibrary native module not present.');
}

// Safe load Contacts (expo-contacts)
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  ContactsModule = require('expo-contacts');
} catch (e) {
  console.warn('[JARVIS Core] Contacts native module not present.');
}

// Safe load Speech (expo-speech)
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  SpeechModule = require('expo-speech');
} catch (e) {
  console.warn('[JARVIS Core] Speech native module not present.');
}

// Safe load IntentLauncher (expo-intent-launcher)
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  IntentLauncherModule = require('expo-intent-launcher');
} catch (e) {
  console.warn('[JARVIS Core] IntentLauncher native module not present.');
}

// Safe load KeepAwake (expo-keep-awake)
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  KeepAwakeModule = require('expo-keep-awake');
} catch (e) {
  console.warn('[JARVIS Core] KeepAwake native module not present.');
}

// Safe load Haptics (expo-haptics)
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  HapticsModule = require('expo-haptics');
} catch (e) {
  console.warn('[JARVIS Core] Haptics native module not present.');
}

export const SafeNative = {
  get Audio() {
    return AudioModule;
  },
  get MediaLibrary() {
    return MediaLibraryModule;
  },
  get Contacts() {
    return ContactsModule;
  },
  get Speech() {
    return SpeechModule;
  },
  get IntentLauncher() {
    return IntentLauncherModule;
  },
  get KeepAwake() {
    return KeepAwakeModule;
  },
  get Haptics() {
    return HapticsModule;
  },
};
