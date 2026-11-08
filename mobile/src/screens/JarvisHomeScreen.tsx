import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
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
import { MaterialCommunityIcons } from '@expo/vector-icons';

type HudTab = 'COCKPIT' | 'AUDIO' | 'COMMS' | 'DIAGNOSTICS';

export const JarvisHomeScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<HudTab>('COCKPIT');
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
      ...prev.slice(-30),
      {
        id: Math.random().toString(),
        timestamp: timeStr,
        sender,
        text,
      },
    ]);
  }, []);

  const triggerHaptic = (style: any = 'light') => {
    try {
      const Haptics = SafeNative.Haptics;
      if (Haptics && typeof Haptics.impactAsync === 'function') {
        const feedback =
          style === 'medium'
            ? Haptics.ImpactFeedbackStyle.Medium
            : Haptics.ImpactFeedbackStyle.Light;
        Haptics.impactAsync(feedback);
      }
    } catch (e) {}
  };

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
      addLog('SYSTEM', 'Initializing Stark MK-85 Mobile Core...');

      // Scan contacts
      const loadedContacts = await ContactsService.loadContacts();
      setContacts(loadedContacts);
      addLog('SYSTEM', `Phonebook online: ${loadedContacts.length} neural links established.`);

      // Scan local songs
      const songs = await AudioService.scanDeviceSongs();
      const first = AudioService.getCurrentTrack();
      setCurrentTrack(first);
      addLog('SYSTEM', `Audio frequency array: ${songs.length} audio tracks synced.`);

      // Welcome voice greeting for Akmal Sir
      VoiceEngine.speak(
        'Stark Systems Online. Ready for your ride, Akmal Sir.'
      );
      addLog('JARVIS', 'All systems calibrated at 100%. Ready for hands-free ride command, Akmal Sir.');
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
          const reply = 'Streaming your favorite ride tracks now, Akmal Sir.';
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
          const reply = 'Audio playback suspended.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }

        case 'NEXT_TRACK': {
          setState('SPEAKING');
          const reply = 'Engaging next track.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AudioService.next();
          setState('PLAYING');
          break;
        }

        case 'PREV_TRACK': {
          setState('SPEAKING');
          const reply = 'Rewinding to previous track.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AudioService.previous();
          setState('PLAYING');
          break;
        }

        case 'SEEK_FORWARD': {
          await AudioService.seekForward(15);
          setState('SPEAKING');
          const reply = 'Advanced track by 15 seconds.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('PLAYING');
          break;
        }

        case 'SEEK_BACKWARD': {
          await AudioService.seekBackward(15);
          setState('SPEAKING');
          const reply = 'Rewound track by 15 seconds.';
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
            const reply = `Connecting cellular link to ${contact.name}, Akmal Sir.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            await PhoneService.makeCall(contact);
          } else {
            setState('SPEAKING');
            const reply = `I could not locate ${query || 'the contact'} in your neural phonebook.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            setState('IDLE');
          }
          break;
        }

        case 'END_CALL': {
          setState('SPEAKING');
          const reply = 'Cellular connection severed, Akmal Sir.';
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
            const reply = `Establishing WhatsApp call with ${contact.name}.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            await WhatsAppService.makeCall(contact);
          } else {
            setState('SPEAKING');
            const reply = `Target ${query} not found for WhatsApp transmission.`;
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
            const reply = `Transmitting WhatsApp message to ${contact.name}.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
            await WhatsAppService.sendMessage(contact, 'Salam Akmal Sir is on a bike ride.');
          } else {
            setState('SPEAKING');
            const reply = `Unable to dispatch message: ${query} not found.`;
            addLog('JARVIS', reply);
            await VoiceEngine.speak(reply);
          }
          setState('IDLE');
          break;
        }

        case 'OPEN_GALLERY': {
          setState('SPEAKING');
          const reply = 'Displaying optical photo repository.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AppLauncherService.openGallery();
          setState('IDLE');
          break;
        }

        case 'OPEN_CAMERA': {
          setState('SPEAKING');
          const reply = 'Optical sensors active.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AppLauncherService.openCamera();
          setState('IDLE');
          break;
        }

        case 'OPEN_MAPS': {
          setState('SPEAKING');
          const reply = 'Synchronizing GPS satellite navigation.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          await AppLauncherService.openMaps();
          setState('IDLE');
          break;
        }

        case 'BATTERY_STATUS': {
          setState('SPEAKING');
          const reply = 'Power cells operating at optimal capacity: 88 percent.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }

        case 'TIME_CHECK': {
          setState('SPEAKING');
          const reply = `The time is exactly ${currentTime}.`;
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }

        case 'JARVIS_STATUS': {
          setState('SPEAKING');
          const reply = 'All telemetry links and speech recognition arrays are performing at maximum efficiency.';
          addLog('JARVIS', reply);
          await VoiceEngine.speak(reply);
          setState('IDLE');
          break;
        }

        default: {
          setState('SPEAKING');
          const reply = `Order acknowledged: "${commandText}". Processing directive.`;
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
      addLog('SYSTEM', 'Acoustic listener engaged. Awaiting voice command...');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <View style={styles.container}>
        {/* Top Cockpit Telemetry Bar */}
        <BikeModeHeader
          currentTime={currentTime}
          isBikeModeActive={isBikeMode}
          onToggleBikeMode={() => {
            const nextMode = !isBikeMode;
            setIsBikeMode(nextMode);
            addLog('SYSTEM', `Cockpit bike mode ${nextMode ? 'ENGAGED' : 'DISENGAGED'}`);
          }}
          onOpenGallery={() => executeVoiceCommand('gallery kholo')}
          onOpenCamera={() => executeVoiceCommand('camera on karo')}
          onOpenMaps={() => executeVoiceCommand('maps kholo')}
        />

        {/* Futuristic Cockpit Segmented Tab Bar */}
        <View style={styles.tabBar}>
          <TouchableOpacity
            style={[styles.tabItem, activeTab === 'COCKPIT' && styles.tabItemActive]}
            onPress={() => {
              triggerHaptic();
              setActiveTab('COCKPIT');
            }}
          >
            <MaterialCommunityIcons
              name="atom"
              size={14}
              color={activeTab === 'COCKPIT' ? '#00f0ff' : '#64748b'}
            />
            <Text style={[styles.tabText, activeTab === 'COCKPIT' && styles.tabTextActive]}>
              COCKPIT
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabItem, activeTab === 'AUDIO' && styles.tabItemActive]}
            onPress={() => {
              triggerHaptic();
              setActiveTab('AUDIO');
            }}
          >
            <MaterialCommunityIcons
              name="disc"
              size={14}
              color={activeTab === 'AUDIO' ? '#c084fc' : '#64748b'}
            />
            <Text style={[styles.tabText, activeTab === 'AUDIO' && styles.tabTextActiveAudio]}>
              AUDIO DECK
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabItem, activeTab === 'COMMS' && styles.tabItemActive]}
            onPress={() => {
              triggerHaptic();
              setActiveTab('COMMS');
            }}
          >
            <MaterialCommunityIcons
              name="satellite-variant"
              size={14}
              color={activeTab === 'COMMS' ? '#00ffaa' : '#64748b'}
            />
            <Text style={[styles.tabText, activeTab === 'COMMS' && styles.tabTextActiveComms]}>
              COMMS
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tabItem, activeTab === 'DIAGNOSTICS' && styles.tabItemActive]}
            onPress={() => {
              triggerHaptic();
              setActiveTab('DIAGNOSTICS');
            }}
          >
            <MaterialCommunityIcons
              name="console-line"
              size={14}
              color={activeTab === 'DIAGNOSTICS' ? '#38bdf8' : '#64748b'}
            />
            <Text style={[styles.tabText, activeTab === 'DIAGNOSTICS' && styles.tabTextActiveDiag]}>
              HUD FEED
            </Text>
          </TouchableOpacity>
        </View>

        {/* Main Content Area */}
        <ScrollView
          style={styles.mainScroll}
          contentContainerStyle={styles.mainScrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* TAB 1: COCKPIT (All-in-One Flight Deck) */}
          {activeTab === 'COCKPIT' && (
            <View>
              {/* Massive Holographic Arc Reactor */}
              <View style={styles.reactorDeck}>
                <ArcReactor
                  state={state}
                  size={200}
                  onPress={handleMicTap}
                />
                <VoiceWaveform
                  isActive={state === 'LISTENING' || state === 'SPEAKING' || isPlaying}
                  barColor={
                    state === 'LISTENING'
                      ? '#00ffaa'
                      : state === 'PLAYING'
                      ? '#c084fc'
                      : state === 'CALLING'
                      ? '#2dd4bf'
                      : '#00f0ff'
                  }
                />
              </View>

              {/* Music Player Deck */}
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

              {/* Neural Comms Link */}
              <ContactsQuickDial
                contacts={contacts}
                onCall={(c) => executeVoiceCommand(`${c.name} ko call milao`)}
                onWhatsApp={(c) => executeVoiceCommand(`whatsapp call ${c.name}`)}
              />

              {/* Live HUD Telemetry Log */}
              <TerminalLog logs={logs} />
            </View>
          )}

          {/* TAB 2: FULL AUDIO DECK */}
          {activeTab === 'AUDIO' && (
            <View style={styles.tabContentSection}>
              {/* Visualizer Header */}
              <View style={styles.audioTabHero}>
                <MaterialCommunityIcons name="album" size={80} color="#c084fc" />
                <Text style={styles.audioHeroTitle}>ACOUSTIC SYNTHESIZER</Text>
                <Text style={styles.audioHeroSubtitle}>
                  {currentTrack ? currentTrack.title : 'Ready for Audio Command'}
                </Text>
                <VoiceWaveform
                  isActive={isPlaying}
                  barColor="#c084fc"
                  count={24}
                />
              </View>

              {/* Master Player Controls */}
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

              {/* Playlist Directory */}
              <View style={styles.playlistSection}>
                <Text style={styles.sectionHeader}>STORAGE AUDIO TRACKS</Text>
                {AudioService.getPlaylist().slice(0, 8).map((t, idx) => (
                  <TouchableOpacity
                    key={t.id}
                    style={styles.playlistItem}
                    onPress={() => AudioService.playTrack(idx)}
                  >
                    <View style={styles.playIndexBadge}>
                      <Text style={styles.playIndexText}>{idx + 1}</Text>
                    </View>
                    <View style={styles.playItemInfo}>
                      <Text style={styles.playItemTitle} numberOfLines={1}>{t.title}</Text>
                      <Text style={styles.playItemArtist}>{t.artist}</Text>
                    </View>
                    <MaterialCommunityIcons
                      name={currentTrack?.id === t.id && isPlaying ? 'waveform' : 'play-circle-outline'}
                      size={20}
                      color="#00f0ff"
                    />
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* TAB 3: COMMS & CONTACTS DIRECTORY */}
          {activeTab === 'COMMS' && (
            <View style={styles.tabContentSection}>
              <View style={styles.commsHeader}>
                <MaterialCommunityIcons name="account-voice" size={32} color="#00ffaa" />
                <Text style={styles.commsHeaderTitle}>NEURAL COMMS DIRECTORY</Text>
                <Text style={styles.commsHeaderSubtitle}>Tap any node or speak: "Ali ko call milao"</Text>
              </View>

              {/* Expanded Contacts List */}
              <View style={styles.commsList}>
                {contacts.map((contact) => (
                  <View key={contact.id} style={styles.commsCard}>
                    <View style={styles.commsAvatar}>
                      <Text style={styles.commsLetter}>{contact.name.charAt(0)}</Text>
                    </View>
                    <View style={styles.commsInfo}>
                      <Text style={styles.commsName}>{contact.name}</Text>
                      <Text style={styles.commsNumber}>{contact.primaryNumber}</Text>
                    </View>
                    <View style={styles.commsActions}>
                      <TouchableOpacity
                        style={styles.commsCallBtn}
                        onPress={() => executeVoiceCommand(`${contact.name} ko call milao`)}
                      >
                        <MaterialCommunityIcons name="phone" size={18} color="#ffffff" />
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.commsWaBtn}
                        onPress={() => executeVoiceCommand(`whatsapp call ${contact.name}`)}
                      >
                        <MaterialCommunityIcons name="whatsapp" size={18} color="#ffffff" />
                      </TouchableOpacity>
                    </View>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* TAB 4: HUD DIAGNOSTICS & TELEMETRY */}
          {activeTab === 'DIAGNOSTICS' && (
            <View style={styles.tabContentSection}>
              {/* Telemetry Metric Cards */}
              <View style={styles.metricsGrid}>
                <View style={styles.metricCard}>
                  <Text style={styles.metricLabel}>CORE POWER</Text>
                  <Text style={styles.metricValue}>88%</Text>
                  <Text style={styles.metricSub}>NOMINAL // VOLT: 4.1V</Text>
                </View>
                <View style={styles.metricCard}>
                  <Text style={styles.metricLabel}>BT HEADSET LINK</Text>
                  <Text style={[styles.metricValue, { color: '#00ffaa' }]}>CONNECTED</Text>
                  <Text style={styles.metricSub}>SCO AUDIO WIDEBAND</Text>
                </View>
                <View style={styles.metricCard}>
                  <Text style={styles.metricLabel}>AUDIO RUNTIME</Text>
                  <Text style={styles.metricValue}>{isPlaying ? 'STREAMING' : 'IDLE'}</Text>
                  <Text style={styles.metricSub}>SAMPLE: 44.1kHz FLAC</Text>
                </View>
                <View style={styles.metricCard}>
                  <Text style={styles.metricLabel}>NEURAL LATENCY</Text>
                  <Text style={[styles.metricValue, { color: '#38bdf8' }]}>12ms</Text>
                  <Text style={styles.metricSub}>EDGE CACHE ACTIVE</Text>
                </View>
              </View>

              {/* Full Terminal Log */}
              <TerminalLog logs={logs} />
            </View>
          )}
        </ScrollView>

        {/* Floating Voice Command Dock */}
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
    backgroundColor: '#020617',
  },
  container: {
    flex: 1,
    backgroundColor: '#020617',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: 'rgba(3, 7, 18, 0.95)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 240, 255, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 6,
    justifyContent: 'space-around',
  },
  tabItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  tabItemActive: {
    backgroundColor: 'rgba(0, 240, 255, 0.1)',
    borderColor: 'rgba(0, 240, 255, 0.35)',
  },
  tabText: {
    color: '#64748b',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: 'monospace',
  },
  tabTextActive: {
    color: '#00f0ff',
  },
  tabTextActiveAudio: {
    color: '#c084fc',
  },
  tabTextActiveComms: {
    color: '#00ffaa',
  },
  tabTextActiveDiag: {
    color: '#38bdf8',
  },
  mainScroll: {
    flex: 1,
  },
  mainScrollContent: {
    paddingBottom: 16,
  },
  reactorDeck: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  tabContentSection: {
    paddingHorizontal: 16,
    paddingTop: 14,
  },
  audioTabHero: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    backgroundColor: 'rgba(192, 132, 252, 0.05)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(192, 132, 252, 0.2)',
    marginBottom: 12,
  },
  audioHeroTitle: {
    color: '#c084fc',
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 2,
    fontFamily: 'monospace',
    marginTop: 8,
  },
  audioHeroSubtitle: {
    color: '#94a3b8',
    fontSize: 12,
    marginTop: 4,
    marginBottom: 10,
  },
  playlistSection: {
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 14,
    marginTop: 8,
  },
  sectionHeader: {
    color: '#64748b',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.5,
    fontFamily: 'monospace',
    marginBottom: 10,
  },
  playlistItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.04)',
    gap: 10,
  },
  playIndexBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(0, 240, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playIndexText: {
    color: '#00f0ff',
    fontSize: 11,
    fontFamily: 'monospace',
    fontWeight: '700',
  },
  playItemInfo: {
    flex: 1,
  },
  playItemTitle: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  playItemArtist: {
    color: '#64748b',
    fontSize: 10,
    marginTop: 2,
  },
  commsHeader: {
    alignItems: 'center',
    paddingVertical: 16,
    backgroundColor: 'rgba(0, 255, 170, 0.05)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(0, 255, 170, 0.2)',
    marginBottom: 14,
  },
  commsHeaderTitle: {
    color: '#00ffaa',
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 2,
    fontFamily: 'monospace',
    marginTop: 6,
  },
  commsHeaderSubtitle: {
    color: '#94a3b8',
    fontSize: 11,
    marginTop: 4,
  },
  commsList: {
    gap: 8,
  },
  commsCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(3, 7, 18, 0.88)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 255, 170, 0.25)',
    padding: 12,
    gap: 12,
  },
  commsAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0, 255, 170, 0.12)',
    borderWidth: 1.5,
    borderColor: '#00ffaa',
    justifyContent: 'center',
    alignItems: 'center',
  },
  commsLetter: {
    color: '#00ffaa',
    fontSize: 18,
    fontWeight: '800',
  },
  commsInfo: {
    flex: 1,
  },
  commsName: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  commsNumber: {
    color: '#64748b',
    fontSize: 11,
    fontFamily: 'monospace',
    marginTop: 2,
  },
  commsActions: {
    flexDirection: 'row',
    gap: 8,
  },
  commsCallBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#059669',
    justifyContent: 'center',
    alignItems: 'center',
  },
  commsWaBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#16a34a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 14,
  },
  metricCard: {
    width: '48%',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 12,
  },
  metricLabel: {
    color: '#64748b',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.2,
    fontFamily: 'monospace',
  },
  metricValue: {
    color: '#00f0ff',
    fontSize: 18,
    fontWeight: '900',
    fontFamily: 'monospace',
    marginTop: 4,
  },
  metricSub: {
    color: '#475569',
    fontSize: 8,
    fontFamily: 'monospace',
    marginTop: 2,
  },
});
