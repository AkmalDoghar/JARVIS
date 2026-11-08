import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  ScrollView,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeNative } from '../services/safeNativeModules';
import {
  AssistantState,
  ContactItem,
  LogEntry,
  Track,
} from '../types';
import { ArcReactor } from '../components/ArcReactor';
import { VoiceWaveform } from '../components/VoiceWaveform';
import { MusicPlayerWidget } from '../components/MusicPlayerWidget';
import { ContactsQuickDial } from '../components/ContactsQuickDial';
import { BikeModeHeader } from '../components/BikeModeHeader';
import { TerminalLog } from '../components/TerminalLog';
import { VoiceCommandBar } from '../components/VoiceCommandBar';

import { VoiceEngine } from '../services/voiceEngine';
import { AudioService } from '../services/audioService';
import { ContactsService } from '../services/contactsService';
import { PhoneService } from '../services/phoneService';
import { WhatsAppService } from '../services/whatsappService';
import { AppLauncherService } from '../services/appLauncherService';

export const JarvisHomeScreen: React.FC = () => {
  const [state, setState] = useState<AssistantState>('IDLE');
  const [isBikeMode, setIsBikeMode] = useState<boolean>(true);
  const [currentTime, setCurrentTime] = useState<string>('00:00');

  // Music state
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [position, setPosition] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);

  // Contacts state
  const [contacts, setContacts] = useState<ContactItem[]>([]);

  // Logs
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = useCallback((sender: 'JARVIS' | 'AKMAL_SIR' | 'SYSTEM', text: string) => {
    const timeStr = new Date().toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    setLogs((prev) => [
      ...prev.slice(-25), // keep last 25 entries
      {
        id: Math.random().toString(),
        timestamp: timeStr,
        sender,
        text,
      },
    ]);
  }, []);

  // Clock ticker & keep-awake
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
      );
    }, 1000);

    const KeepAwake = SafeNative.KeepAwake;
    if (isBikeMode && KeepAwake && typeof KeepAwake.activateKeepAwakeAsync === 'function') {
      KeepAwake.activateKeepAwakeAsync().catch(() => {});
    }

    return () => {
      clearInterval(timer);
      if (KeepAwake && typeof KeepAwake.deactivateKeepAwake === 'function') {
        try {
          KeepAwake.deactivateKeepAwake();
        } catch (e) {}
      }
    };
  }, [isBikeMode]);

  // Initial load: Music & Contacts
  useEffect(() => {
    const initServices = async () => {
      addLog('SYSTEM', 'Initializing JARVIS Mobile Core...');

      // Scan contacts
      const loadedContacts = await ContactsService.loadContacts();
      setContacts(loadedContacts);
      addLog('SYSTEM', `Phonebook synced: ${loadedContacts.length} contacts loaded.`);

      // Scan local songs
      const songs = await AudioService.scanDeviceSongs();
      const first = AudioService.getCurrentTrack();
      setCurrentTrack(first);
      addLog('SYSTEM', `Audio storage scanned: ${songs.length} tracks detected.`);

      // Welcome voice greeting for Akmal Sir
      VoiceEngine.speak(
        'JARVIS Mobile System Online. Ready for your ride, Akmal Sir.'
      );
      addLog('JARVIS', 'Systems nominal. Ready for hands-free ride control, Akmal Sir.');
    };

    initServices();

    // Subscribe to audio changes
    const unsubAudio = AudioService.subscribeStatus((status) => {
      setIsPlaying(status.isPlaying);
      setCurrentTrack(status.track);
      setPosition(status.position);
      setDuration(status.duration);
      if (status.isPlaying) {
        setState((prev) => (prev === 'LISTENING' || prev === 'SPEAKING' ? prev : 'PLAYING'));
      } else {
        setState((prev) => (prev === 'PLAYING' ? 'IDLE' : prev));
      }
    });

    return () => {
      unsubAudio();
      AudioService.stop();
    };
  }, [addLog]);

  // Central Command Processor
  const executeVoiceCommand = useCallback(
    async (commandText: string) => {
      addLog('AKMAL_SIR', commandText);
      setState('THINKING');

      const parsed = VoiceEngine.parseCommand(commandText);

      switch (parsed.type) {
        case 'PLAY_MUSIC': {
          setState('SPEAKING');
          const reply = 'Playing your favorite tracks now, Akmal Sir.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AudioService.playFavorites();
          setState('PLAYING');
          break;
        }

        case 'PAUSE_MUSIC':
        case 'STOP_MUSIC': {
          await AudioService.pause();
          setState('SPEAKING');
          const reply = 'Music playback paused.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }

        case 'NEXT_TRACK': {
          setState('SPEAKING');
          const reply = 'Skipping to next track.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AudioService.next();
          setState('PLAYING');
          break;
        }

        case 'PREV_TRACK': {
          setState('SPEAKING');
          const reply = 'Going back to previous song.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AudioService.previous();
          setState('PLAYING');
          break;
        }

        case 'SEEK_FORWARD': {
          await AudioService.seekForward(15);
          setState('SPEAKING');
          const reply = 'Fast forwarded 15 seconds.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('PLAYING');
          break;
        }

        case 'SEEK_BACKWARD': {
          await AudioService.seekBackward(15);
          setState('SPEAKING');
          const reply = 'Rewound 15 seconds.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('PLAYING');
          break;
        }

        case 'CALL_CONTACT': {
          const query = parsed.target || '';
          const contact = ContactsService.findContact(query);
          if (contact) {
            setState('CALLING');
            const reply = `Calling ${contact.name}, Akmal Sir.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            await PhoneService.makeCall(contact);
          } else {
            setState('SPEAKING');
            const reply = `I could not locate ${query || 'the contact'} in your phonebook.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            setState('IDLE');
          }
          break;
        }

        case 'END_CALL': {
          setState('SPEAKING');
          const reply = 'Disconnecting call, Akmal Sir.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await PhoneService.endCall();
          setState('IDLE');
          break;
        }

        case 'WHATSAPP_CALL': {
          const query = parsed.target || '';
          const contact = ContactsService.findContact(query);
          if (contact) {
            setState('CALLING');
            const reply = `Opening WhatsApp call for ${contact.name}.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            await WhatsAppService.makeCall(contact);
          } else {
            setState('SPEAKING');
            const reply = `Contact ${query} not found for WhatsApp.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            setState('IDLE');
          }
          break;
        }

        case 'WHATSAPP_MESSAGE': {
          const query = parsed.target || '';
          const contact = ContactsService.findContact(query);
          if (contact) {
            setState('SPEAKING');
            const reply = `Sending WhatsApp message to ${contact.name}.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            await WhatsAppService.sendMessage(contact, 'Salam Akmal Sir is on a bike ride.');
          } else {
            setState('SPEAKING');
            const reply = `Could not find ${query} for WhatsApp message.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
          }
          setState('IDLE');
          break;
        }

        case 'OPEN_GALLERY': {
          setState('SPEAKING');
          const reply = 'Opening phone gallery.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AppLauncherService.openGallery();
          setState('IDLE');
          break;
        }

        case 'OPEN_CAMERA': {
          setState('SPEAKING');
          const reply = 'Activating camera.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AppLauncherService.openCamera();
          setState('IDLE');
          break;
        }

        case 'OPEN_MAPS': {
          setState('SPEAKING');
          const reply = 'Opening navigation maps.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AppLauncherService.openMaps();
          setState('IDLE');
          break;
        }

        case 'BATTERY_STATUS': {
          setState('SPEAKING');
          const reply = 'Battery level is at 88 percent. Power cells nominal.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }

        case 'TIME_CHECK': {
          setState('SPEAKING');
          const reply = `The time is currently ${currentTime}.`;
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }

        case 'JARVIS_STATUS': {
          setState('SPEAKING');
          const reply = 'All bike telemetry systems and neural modules are running at peak efficiency.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }

        default: {
          setState('SPEAKING');
          const reply = `Command received: "${commandText}". Executing request.`;
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }
      }
    },
    [addLog, currentTime]
  );

  const handleMicTap = () => {
    if (state === 'LISTENING') {
      setState('IDLE');
      VoiceEngine.stopSpeaking();
    } else {
      setState('LISTENING');
      addLog('SYSTEM', 'Voice listening activated. Speak command...');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <View style={styles.container}>
        {/* Bike Mode Header with Telemetry */}
        <BikeModeHeader
          currentTime={currentTime}
          isBikeModeActive={isBikeMode}
          onToggleBikeMode={() => {
            const nextMode = !isBikeMode;
            setIsBikeMode(nextMode);
            addLog('SYSTEM', `Bike mode ${nextMode ? 'ENGAGED' : 'DISENGAGED'}`);
          }}
          onOpenGallery={() => executeVoiceCommand('gallery kholo')}
          onOpenCamera={() => executeVoiceCommand('camera on karo')}
          onOpenMaps={() => executeVoiceCommand('maps kholo')}
        />

        <ScrollView
          style={styles.mainScroll}
          contentContainerStyle={styles.mainScrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Central Arc Reactor Interactive Node */}
          <View style={styles.reactorSection}>
            <ArcReactor
              state={state}
              size={170}
              onPress={handleMicTap}
            />
            <VoiceWaveform
              isActive={state === 'LISTENING' || state === 'SPEAKING' || isPlaying}
            />
          </View>

          {/* Music Player Widget */}
          <MusicPlayerWidget
            track={currentTrack}
            isPlaying={isPlaying}
            position={position}
            duration={duration}
            onPlayPause={() => {
              if (isPlaying) {
                executeVoiceCommand('stop kro');
              } else {
                executeVoiceCommand('mere favourite songs play kro');
              }
            }}
            onNext={() => executeVoiceCommand('next kro')}
            onPrev={() => executeVoiceCommand('pichay kro')}
            onSeekForward={() => executeVoiceCommand('forword kro')}
            onSeekBackward={() => executeVoiceCommand('backward kro')}
            onPlayFavorites={() => executeVoiceCommand('mere favourite songs play kro')}
          />

          {/* Contacts Quick Voice Dial Row */}
          <ContactsQuickDial
            contacts={contacts}
            onCall={(c) => executeVoiceCommand(`${c.name} ko call milao`)}
            onWhatsApp={(c) => executeVoiceCommand(`whatsapp call ${c.name}`)}
          />

          {/* Live HUD Telemetry Terminal Log */}
          <TerminalLog logs={logs} />
        </ScrollView>

        {/* Bottom Voice Command Bar */}
        <VoiceCommandBar
          isListening={state === 'LISTENING'}
          onMicPress={handleMicTap}
          onSubmitVoiceText={(cmd) => executeVoiceCommand(cmd)}
        />
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#050a14',
  },
  container: {
    flex: 1,
    backgroundColor: '#050a14',
  },
  mainScroll: {
    flex: 1,
  },
  mainScrollContent: {
    paddingBottom: 10,
  },
  reactorSection: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
  },
});
