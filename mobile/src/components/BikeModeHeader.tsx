import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface Props {
  currentTime: string;
  isBikeModeActive: boolean;
  onToggleBikeMode: () => void;
  onOpenGallery: () => void;
  onOpenCamera: () => void;
  onOpenMaps: () => void;
}

export const BikeModeHeader: React.FC<Props> = ({
  currentTime,
  isBikeModeActive,
  onToggleBikeMode,
  onOpenGallery,
  onOpenCamera,
  onOpenMaps,
}) => {
  const triggerHaptic = (fn: () => void) => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch (e) {
      // ignore
    }
    fn();
  };

  return (
    <View style={styles.container}>
      {/* Top Bar */}
      <View style={styles.topRow}>
        <View style={styles.brandRow}>
          <MaterialCommunityIcons name="shield-airplane" size={20} color="#00f0ff" />
          <Text style={styles.brandTitle}>JARVIS</Text>
          <View style={styles.pillActive}>
            <Text style={styles.pillText}>ONLINE</Text>
          </View>
        </View>

        <View style={styles.rightStats}>
          <View style={styles.timeBadge}>
            <MaterialCommunityIcons name="clock-outline" size={14} color="#00f0ff" />
            <Text style={styles.timeText}>{currentTime}</Text>
          </View>
          <TouchableOpacity
            style={[styles.bikeBadge, isBikeModeActive && styles.bikeBadgeActive]}
            onPress={() => triggerHaptic(onToggleBikeMode)}
          >
            <MaterialCommunityIcons
              name="motorbike"
              size={16}
              color={isBikeModeActive ? '#050a14' : '#00f0ff'}
            />
            <Text style={[styles.bikeText, isBikeModeActive && styles.bikeTextActive]}>
              {isBikeModeActive ? 'BIKE MODE' : 'STANDBY'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Quick Launch Icons for Bike Helm/Mount */}
      <View style={styles.quickLaunchRow}>
        <TouchableOpacity
          style={styles.quickBtn}
          onPress={() => triggerHaptic(onOpenGallery)}
        >
          <MaterialCommunityIcons name="image-multiple" size={18} color="#00f0ff" />
          <Text style={styles.quickBtnText}>Gallery</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickBtn}
          onPress={() => triggerHaptic(onOpenCamera)}
        >
          <MaterialCommunityIcons name="camera" size={18} color="#00f0ff" />
          <Text style={styles.quickBtnText}>Camera</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickBtn}
          onPress={() => triggerHaptic(onOpenMaps)}
        >
          <MaterialCommunityIcons name="navigation" size={18} color="#00f0ff" />
          <Text style={styles.quickBtnText}>Maps</Text>
        </TouchableOpacity>

        <View style={styles.btStatus}>
          <MaterialCommunityIcons name="bluetooth-audio" size={16} color="#38ef7d" />
          <Text style={styles.btText}>BT HEADSET</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 240, 255, 0.2)',
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  brandTitle: {
    color: '#00f0ff',
    fontSize: 18,
    fontWeight: '900',
    letterSpacing: 2,
  },
  pillActive: {
    backgroundColor: 'rgba(0, 255, 170, 0.15)',
    borderColor: '#00ffaa',
    borderWidth: 1,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  pillText: {
    color: '#00ffaa',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1,
  },
  rightStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  timeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  timeText: {
    color: '#94a3b8',
    fontSize: 12,
    fontFamily: 'monospace',
  },
  bikeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(0, 240, 255, 0.1)',
    borderColor: '#00f0ff',
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  bikeBadgeActive: {
    backgroundColor: '#00f0ff',
  },
  bikeText: {
    color: '#00f0ff',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  bikeTextActive: {
    color: '#050a14',
  },
  quickLaunchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  quickBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  quickBtnText: {
    color: '#e2e8f0',
    fontSize: 11,
    fontWeight: '600',
  },
  btStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  btText: {
    color: '#38ef7d',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});

