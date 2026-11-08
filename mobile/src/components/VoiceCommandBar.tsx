import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { SafeNative } from '../services/safeNativeModules';

interface Props {
  isListening: boolean;
  onMicPress: () => void;
  onSubmitVoiceText: (text: string) => void;
}

const QUICK_COMMANDS = [
  'Mere favourite songs play kro',
  'Next kro',
  'Pichay kro',
  'Stop kro',
  'Forword kro',
  'Ali ko call milao',
  'WhatsApp call Ali',
  'WhatsApp message Ali Salam',
  'Call band kr do',
  'Gallery kholo',
  'Camera on karo',
  'Maps kholo',
];

export const VoiceCommandBar: React.FC<Props> = ({
  isListening,
  onMicPress,
  onSubmitVoiceText,
}) => {
  const [inputText, setInputText] = useState('');

  const triggerHaptic = (style: any = 'medium') => {
    try {
      const Haptics = SafeNative.Haptics;
      if (Haptics && typeof Haptics.impactAsync === 'function') {
        const feedback =
          style === 'heavy'
            ? Haptics.ImpactFeedbackStyle.Heavy
            : Haptics.ImpactFeedbackStyle.Medium;
        Haptics.impactAsync(feedback);
      }
    } catch (e) {}
  };

  const handleSend = () => {
    if (!inputText.trim()) return;
    triggerHaptic('medium');
    onSubmitVoiceText(inputText.trim());
    setInputText('');
  };

  const handleChipPress = (cmd: string) => {
    triggerHaptic('medium');
    onSubmitVoiceText(cmd);
  };

  return (
    <View style={styles.dock}>
      {/* Quick Spoken Voice Prompt Chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chipRow}
      >
        {QUICK_COMMANDS.map((cmd, i) => (
          <TouchableOpacity
            key={i}
            style={styles.chip}
            onPress={() => handleChipPress(cmd)}
          >
            <MaterialCommunityIcons name="microphone-variant" size={12} color="#00f0ff" />
            <Text style={styles.chipText}>{cmd}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Voice Mic + Holographic Input Bar */}
      <View style={styles.inputRow}>
        {/* Massive Glowing Mic Trigger */}
        <TouchableOpacity
          style={[styles.micOrb, isListening && styles.micOrbActive]}
          onPress={() => {
            triggerHaptic('heavy');
            onMicPress();
          }}
        >
          <MaterialCommunityIcons
            name={isListening ? 'microphone-settings' : 'microphone'}
            size={26}
            color={isListening ? '#020617' : '#00f0ff'}
          />
        </TouchableOpacity>

        <TextInput
          style={styles.input}
          placeholder="Speak or test voice command..."
          placeholderTextColor="#475569"
          value={inputText}
          onChangeText={setInputText}
          onSubmitEditing={handleSend}
          returnKeyType="send"
        />

        <TouchableOpacity
          style={[styles.sendOrb, !inputText.trim() && styles.sendOrbDisabled]}
          disabled={!inputText.trim()}
          onPress={handleSend}
        >
          <MaterialCommunityIcons
            name="send"
            size={18}
            color={inputText.trim() ? '#00f0ff' : '#334155'}
          />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  dock: {
    backgroundColor: 'rgba(2, 6, 23, 0.98)',
    borderTopWidth: 1.5,
    borderTopColor: 'rgba(0, 240, 255, 0.35)',
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 16,
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 20,
  },
  chipRow: {
    gap: 8,
    paddingBottom: 10,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(0, 240, 255, 0.08)',
    borderColor: 'rgba(0, 240, 255, 0.3)',
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
  },
  chipText: {
    color: '#cbd5e1',
    fontSize: 11,
    fontWeight: '600',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  micOrb: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: 'rgba(0, 240, 255, 0.12)',
    borderWidth: 2,
    borderColor: '#00f0ff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 12,
    elevation: 8,
  },
  micOrbActive: {
    backgroundColor: '#00ffaa',
    borderColor: '#00ffaa',
    shadowColor: '#00ffaa',
  },
  input: {
    flex: 1,
    height: 48,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    paddingHorizontal: 18,
    color: '#ffffff',
    fontSize: 13,
  },
  sendOrb: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: 'rgba(0, 240, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendOrbDisabled: {
    borderColor: 'rgba(255, 255, 255, 0.06)',
    backgroundColor: 'transparent',
  },
});
