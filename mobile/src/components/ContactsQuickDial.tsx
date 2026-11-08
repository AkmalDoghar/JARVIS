import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ContactItem } from '../types';
import * as Haptics from 'expo-haptics';

interface Props {
  contacts: ContactItem[];
  onCall: (c: ContactItem) => void;
  onWhatsApp: (c: ContactItem) => void;
}

export const ContactsQuickDial: React.FC<Props> = ({ contacts, onCall, onWhatsApp }) => {
  const triggerHaptic = (fn: () => void) => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch (e) {
      // ignore
    }
    fn();
  };

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <MaterialCommunityIcons name="card-account-phone-outline" size={16} color="#00f0ff" />
          <Text style={styles.headerText}>VOICE DIAL & WHATSAPP</Text>
        </View>
        <Text style={styles.hintText}>"Ali ko call milao"</Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.scroll}>
        {contacts.map((contact) => (
          <View key={contact.id} style={styles.contactItem}>
            <View style={styles.avatar}>
              <Text style={styles.avatarLetter}>
                {contact.name.charAt(0).toUpperCase()}
              </Text>
            </View>
            <Text style={styles.contactName} numberOfLines={1}>
              {contact.name}
            </Text>
            <Text style={styles.contactNumber} numberOfLines={1}>
              {contact.primaryNumber}
            </Text>

            <View style={styles.actionRow}>
              {/* Phone Call */}
              <TouchableOpacity
                style={styles.callBtn}
                onPress={() => triggerHaptic(() => onCall(contact))}
              >
                <MaterialCommunityIcons name="phone" size={16} color="#ffffff" />
              </TouchableOpacity>

              {/* WhatsApp */}
              <TouchableOpacity
                style={styles.waBtn}
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
    backgroundColor: 'rgba(10, 20, 35, 0.85)',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.25)',
    padding: 14,
    marginHorizontal: 16,
    marginVertical: 6,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  headerText: {
    color: '#00f0ff',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  hintText: {
    color: '#64748b',
    fontSize: 10,
    fontStyle: 'italic',
  },
  scroll: {
    flexDirection: 'row',
    gap: 10,
  },
  contactItem: {
    width: 110,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 10,
    alignItems: 'center',
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(0, 240, 255, 0.15)',
    borderWidth: 1,
    borderColor: '#00f0ff',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 6,
  },
  avatarLetter: {
    color: '#00f0ff',
    fontSize: 16,
    fontWeight: '700',
  },
  contactName: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
    width: '100%',
  },
  contactNumber: {
    color: '#94a3b8',
    fontSize: 9,
    fontFamily: 'monospace',
    marginTop: 2,
    marginBottom: 8,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 8,
  },
  callBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#10b981', // green
    justifyContent: 'center',
    alignItems: 'center',
  },
  waBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#25D366', // WhatsApp brand green
    justifyContent: 'center',
    alignItems: 'center',
  },
});

