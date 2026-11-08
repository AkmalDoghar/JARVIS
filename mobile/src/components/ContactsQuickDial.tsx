import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ContactItem } from '../types';
import { SafeNative } from '../services/safeNativeModules';

interface Props {
  contacts: ContactItem[];
  onCall: (c: ContactItem) => void;
  onWhatsApp: (c: ContactItem) => void;
}

export const ContactsQuickDial: React.FC<Props> = ({ contacts, onCall, onWhatsApp }) => {
  const triggerHaptic = (fn: () => void) => {
    try {
      const Haptics = SafeNative.Haptics;
      if (Haptics && typeof Haptics.impactAsync === 'function') {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
    } catch (e) {}
    fn();
  };

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.titleGroup}>
          <MaterialCommunityIcons name="satellite-variant" size={14} color="#00ffaa" />
          <Text style={styles.headerText}>NEURAL COMMS LINK</Text>
        </View>
        <Text style={styles.subHint}>"Ali ko call milao"</Text>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollList}
      >
        {contacts.map((contact) => (
          <View key={contact.id} style={styles.contactPod}>
            {/* Glowing Avatar */}
            <View style={styles.avatarOrb}>
              <Text style={styles.avatarLetter}>
                {contact.name.charAt(0).toUpperCase()}
              </Text>
            </View>

            <Text style={styles.contactName} numberOfLines={1}>
              {contact.name}
            </Text>
            <Text style={styles.contactPhone} numberOfLines={1}>
              {contact.primaryNumber}
            </Text>

            {/* Comms Action Buttons */}
            <View style={styles.actionRow}>
              {/* Cellular Call */}
              <TouchableOpacity
                style={styles.callOrb}
                onPress={() => triggerHaptic(() => onCall(contact))}
              >
                <MaterialCommunityIcons name="phone" size={16} color="#ffffff" />
              </TouchableOpacity>

              {/* WhatsApp Call / Msg */}
              <TouchableOpacity
                style={styles.waOrb}
                onPress={() => triggerHaptic(() => onWhatsApp(contact))}
              >
                <MaterialCommunityIcons name="whatsapp" size={16} color="#ffffff" />
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'rgba(3, 7, 18, 0.88)',
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 255, 170, 0.28)',
    padding: 14,
    marginHorizontal: 16,
    marginVertical: 6,
    shadowColor: '#00ffaa',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 14,
    elevation: 6,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  titleGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  headerText: {
    color: '#00ffaa',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.5,
    fontFamily: 'monospace',
  },
  subHint: {
    color: '#64748b',
    fontSize: 9,
    fontStyle: 'italic',
  },
  scrollList: {
    flexDirection: 'row',
    gap: 10,
    paddingVertical: 2,
  },
  contactPod: {
    width: 114,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    padding: 10,
    alignItems: 'center',
  },
  avatarOrb: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(0, 240, 255, 0.12)',
    borderWidth: 1.5,
    borderColor: '#00f0ff',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 6,
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.7,
    shadowRadius: 6,
  },
  avatarLetter: {
    color: '#00f0ff',
    fontSize: 16,
    fontWeight: '800',
  },
  contactName: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
    width: '100%',
  },
  contactPhone: {
    color: '#64748b',
    fontSize: 9,
    fontFamily: 'monospace',
    marginTop: 2,
    marginBottom: 8,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 8,
  },
  callOrb: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#059669',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#10b981',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
  },
  waOrb: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#16a34a',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#22c55e',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
  },
});
