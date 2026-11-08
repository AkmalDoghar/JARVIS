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
import * as Haptics from 'expo-haptics';

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

  const handleSend = () => {
    if (!inputText.trim()) return;
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    } catch (e) {
      // ignore
    }
    onSubmitVoiceText(inputText.trim());
    setInputText('');
  };

  const handleChipPress = (cmd: string) => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch (e) {
      // ignore
    }
    onSubmitVoiceText(cmd);
  };

  return (
    <View style={styles.container}>
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
            <MaterialCommunityIcons name="microphone-outline" size={12} color="#00f0ff" />
            <Text style={styles.chipText}>{cmd}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Voice Mic + Input Box */}
      <View style={styles.inputRow}>
        <TouchableOpacity
          style={[styles.micBtn, isListening && styles.micBtnActive]}
          onPress={() => {
            try {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
            } catch (e) {}
            onMicPress();
          }}
        >
          <MaterialCommunityIcons
            name={isListening ? 'microphone-settings' : 'microphone'}
            size={24}
            color={isListening ? '#050a14' : '#00f0ff'}
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
          style={[styles.sendBtn, !inputText.trim() && styles.sendBtnDisabled]}
          disabled={!inputText.trim()}
          onPress={handleSend}
        >
          <MaterialCommunityIcons
            name="send"
            size={18}
            color={inputText.trim() ? '#00f0ff' : '#475569'}
          />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 16,
    backgroundColor: '#050a14',
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 240, 255, 0.2)',
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
    borderColor: 'rgba(0, 240, 255, 0.25)',
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  chipText: {
    color: '#94a3b8',
    fontSize: 11,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  micBtn: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(0, 240, 255, 0.12)',
    borderWidth: 1.5,
    borderColor: '#00f0ff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 8,
  },
  micBtnActive: {
    backgroundColor: '#00ffaa',
    borderColor: '#00ffaa',
    shadowColor: '#00ffaa',
  },
  input: {
    flex: 1,
    height: 44,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 16,
    color: '#ffffff',
    fontSize: 13,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0, 240, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendBtnDisabled: {
    borderColor: 'rgba(255, 255, 255, 0.05)',
    backgroundColor: 'transparent',
  },
});

