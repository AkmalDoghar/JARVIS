export interface Track {
  id: string;
  title: string;
  artist: string;
  uri: string;
  duration: number; // in seconds
  filename: string;
  isFavorite?: boolean;
}

export interface ContactItem {
  id: string;
  name: string;
  phoneNumbers: Array<{ number: string; label?: string }>;
  primaryNumber: string;
}

export type VoiceCommandType =
  | 'PLAY_MUSIC'
  | 'PAUSE_MUSIC'
  | 'RESUME_MUSIC'
  | 'NEXT_TRACK'
  | 'PREV_TRACK'
  | 'STOP_MUSIC'
  | 'SEEK_FORWARD'
  | 'SEEK_BACKWARD'
  | 'CALL_CONTACT'
  | 'END_CALL'
  | 'WHATSAPP_CALL'
  | 'WHATSAPP_MESSAGE'
  | 'OPEN_GALLERY'
  | 'OPEN_CAMERA'
  | 'OPEN_MAPS'
  | 'OPEN_APP'
  | 'BATTERY_STATUS'
  | 'TIME_CHECK'
  | 'JARVIS_STATUS'
  | 'UNKNOWN';

export interface ParsedCommand {
  type: VoiceCommandType;
  target?: string;
  message?: string;
  rawText: string;
  confidence?: number;
}

export type AssistantState =
  | 'IDLE'
  | 'LISTENING'
  | 'THINKING'
  | 'SPEAKING'
  | 'CALLING'
  | 'PLAYING';

export interface LogEntry {
  id: string;
  timestamp: string;
  sender: 'JARVIS' | 'AKMAL_SIR' | 'SYSTEM';
  text: string;
  level?: 'info' | 'success' | 'warn' | 'error';
}

export interface BikeTelemetry {
  speedKmh: number;
  batteryLevel: number;
  bluetoothConnected: boolean;
  headsetDeviceName: string;
  currentTime: string;
  isBikeModeActive: boolean;
}

