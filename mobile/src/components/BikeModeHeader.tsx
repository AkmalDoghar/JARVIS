import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { SafeNative } from '../services/safeNativeModules';

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
      const Haptics = SafeNative.Haptics;
      if (Haptics && typeof Haptics.impactAsync === 'function') {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
    } catch (e) {}
    fn();
  };

  return (
    <View style={styles.container}>
      {/* Top Telemetry Flight Bar */}
      <View style={styles.flightBar}>
        {/* Brand / Core Title */}
        <View style={styles.brandGroup}>
          <View style={styles.starkEmblem}>
            <MaterialCommunityIcons name="atom" size={16} color="#00f0ff" />
          </View>
          <View>
            <View style={styles.titleRow}>
              <Text style={styles.brandTitle}>JARVIS</Text>
              <Text style={styles.brandVersion}>MK-85</Text>
            </View>
            <Text style={styles.brandSubtitle}>STARK HUD OPERATING SYSTEM</Text>
          </View>
        </View>

        {/* Speedometer & Time */}
        <View style={styles.telemetryGroup}>
          <View style={styles.speedBadge}>
            <MaterialCommunityIcons name="speedometer" size={13} color="#00ffaa" />
            <Text style={styles.speedValue}>0</Text>
            <Text style={styles.speedUnit}>KM/H</Text>
          </View>

          <View style={styles.timeBadge}>
            <Text style={styles.timeText}>{currentTime}</Text>
          </View>
        </View>
      </View>

      {/* Cockpit Status & Quick Actions Bar */}
      <View style={styles.actionShelf}>
        {/* Mode Toggle Button */}
        <TouchableOpacity
          style={[styles.modeToggle, isBikeModeActive && styles.modeToggleActive]}
          onPress={() => triggerHaptic(onToggleBikeMode)}
        >
          <MaterialCommunityIcons
            name="motorbike"
            size={16}
            color={isBikeModeActive ? '#020617' : '#00f0ff'}
          />
          <Text style={[styles.modeText, isBikeModeActive && styles.modeTextActive]}>
            {isBikeModeActive ? 'BIKE COCKPIT: ON' : 'STANDBY MODE'}
          </Text>
        </TouchableOpacity>

        {/* Quick Launch Glass Buttons */}
        <View style={styles.quickIcons}>
          <TouchableOpacity
            style={styles.glassBtn}
            onPress={() => triggerHaptic(onOpenGallery)}
          >
            <MaterialCommunityIcons name="image-multiple-outline" size={16} color="#38bdf8" />
            <Text style={styles.glassBtnText}>Photos</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.glassBtn}
            onPress={() => triggerHaptic(onOpenCamera)}
          >
            <MaterialCommunityIcons name="camera-iris" size={16} color="#38bdf8" />
            <Text style={styles.glassBtnText}>Cam</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.glassBtn}
            onPress={() => triggerHaptic(onOpenMaps)}
          >
            <MaterialCommunityIcons name="crosshairs-gps" size={16} color="#38bdf8" />
            <Text style={styles.glassBtnText}>Nav</Text>
          </TouchableOpacity>

          {/* BT Indicator */}
          <View style={styles.btBadge}>
            <MaterialCommunityIcons name="bluetooth-audio" size={15} color="#10b981" />
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(2, 6, 23, 0.95)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 240, 255, 0.25)',
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 10,
  },
  flightBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  brandGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  starkEmblem: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: 'rgba(0, 240, 255, 0.1)',
    borderWidth: 1,
    borderColor: '#00f0ff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 4,
  },
  brandTitle: {
    color: '#00f0ff',
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 2,
  },
  brandVersion: {
    color: '#38bdf8',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: 'monospace',
  },
  brandSubtitle: {
    color: '#64748b',
    fontSize: 8,
    letterSpacing: 1.2,
    fontFamily: 'monospace',
  },
  telemetryGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  speedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: 'rgba(16, 185, 129, 0.12)',
    borderColor: 'rgba(16, 185, 129, 0.4)',
    borderWidth: 1,
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 8,
  },
  speedValue: {
    color: '#10b981',
    fontSize: 11,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  speedUnit: {
    color: '#6ee7b7',
    fontSize: 8,
    fontFamily: 'monospace',
  },
  timeBadge: {
    backgroundColor: 'rgba(0, 240, 255, 0.08)',
    borderColor: 'rgba(0, 240, 255, 0.25)',
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  timeText: {
    color: '#00f0ff',
    fontSize: 11,
    fontFamily: 'monospace',
    fontWeight: '700',
  },
  actionShelf: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  modeToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(0, 240, 255, 0.08)',
    borderColor: '#00f0ff',
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
  },
  modeToggleActive: {
    backgroundColor: '#00f0ff',
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 10,
  },
  modeText: {
    color: '#00f0ff',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: 'monospace',
  },
  modeTextActive: {
    color: '#020617',
  },
  quickIcons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  glassBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 8,
  },
  glassBtnText: {
    color: '#94a3b8',
    fontSize: 10,
    fontWeight: '600',
  },
  btBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderWidth: 1,
    borderColor: '#10b981',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
