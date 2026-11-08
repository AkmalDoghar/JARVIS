import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Track } from '../types';
import { SafeNative } from '../services/safeNativeModules';

interface Props {
  track: Track | null;
  isPlaying: boolean;
  position: number;
  duration: number;
  onPlayPause: () => void;
  onNext: () => void;
  onPrev: () => void;
  onSeekForward: () => void;
  onSeekBackward: () => void;
  onPlayFavorites: () => void;
}

export const MusicPlayerWidget: React.FC<Props> = ({
  track,
  isPlaying,
  position,
  duration,
  onPlayPause,
  onNext,
  onPrev,
  onSeekForward,
  onSeekBackward,
  onPlayFavorites,
}) => {
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const progressPercent = duration > 0 ? Math.min((position / duration) * 100, 100) : 0;

  const triggerHaptic = (action: () => void) => {
    try {
      const Haptics = SafeNative.Haptics;
      if (Haptics && typeof Haptics.impactAsync === 'function') {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      }
    } catch (e) {}
    action();
  };

  return (
    <View style={styles.card}>
      {/* Top Header Row */}
      <View style={styles.topRow}>
        <View style={styles.deckBadge}>
          <MaterialCommunityIcons name="disc" size={14} color="#00f0ff" />
          <Text style={styles.deckText}>AUDIO COCKPIT DECK</Text>
        </View>

        <TouchableOpacity
          style={styles.favBtn}
          onPress={() => triggerHaptic(onPlayFavorites)}
        >
          <MaterialCommunityIcons name="star-four-points" size={12} color="#f59e0b" />
          <Text style={styles.favBtnText}>FAVORITES</Text>
        </TouchableOpacity>
      </View>

      {/* Main Track Display */}
      <View style={styles.trackCard}>
        <View style={styles.discCover}>
          <MaterialCommunityIcons
            name={isPlaying ? 'music-note-eighth' : 'music-note'}
            size={24}
            color="#00f0ff"
          />
        </View>
        <View style={styles.trackDetails}>
          <Text style={styles.title} numberOfLines={1}>
            {track ? track.title : 'Ready to Stream'}
          </Text>
          <Text style={styles.artist} numberOfLines={1}>
            {track ? track.artist : 'Say "JARVIS play favorite songs"'}
          </Text>
        </View>
      </View>

      {/* Futuristic Progress Tracker */}
      <View style={styles.progressSection}>
        <View style={styles.barBackground}>
          <View style={[styles.barFill, { width: `${progressPercent}%` }]}>
            <View style={styles.barIndicatorGlow} />
          </View>
        </View>
        <View style={styles.timeRow}>
          <Text style={styles.timeVal}>{formatTime(position)}</Text>
          <Text style={styles.timeVal}>{formatTime(duration)}</Text>
        </View>
      </View>

      {/* Oversized Bike-Glove Touch Controls */}
      <View style={styles.controlsRow}>
        {/* Seek -15s */}
        <TouchableOpacity
          style={styles.seekBtn}
          onPress={() => triggerHaptic(onSeekBackward)}
        >
          <MaterialCommunityIcons name="rewind-15" size={24} color="#38bdf8" />
        </TouchableOpacity>

        {/* Previous */}
        <TouchableOpacity
          style={styles.skipBtn}
          onPress={() => triggerHaptic(onPrev)}
        >
          <MaterialCommunityIcons name="skip-previous" size={30} color="#e2e8f0" />
        </TouchableOpacity>

        {/* Central Giant Glowing Arc Play Orb */}
        <TouchableOpacity
          style={[styles.mainPlayOrb, isPlaying && styles.mainPlayOrbActive]}
          onPress={() => triggerHaptic(onPlayPause)}
        >
          <MaterialCommunityIcons
            name={isPlaying ? 'pause' : 'play'}
            size={36}
            color="#020617"
          />
        </TouchableOpacity>

        {/* Next */}
        <TouchableOpacity
          style={styles.skipBtn}
          onPress={() => triggerHaptic(onNext)}
        >
          <MaterialCommunityIcons name="skip-next" size={30} color="#e2e8f0" />
        </TouchableOpacity>

        {/* Seek +15s */}
        <TouchableOpacity
          style={styles.seekBtn}
          onPress={() => triggerHaptic(onSeekForward)}
        >
          <MaterialCommunityIcons name="fast-forward-15" size={24} color="#38bdf8" />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'rgba(3, 7, 18, 0.88)',
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 240, 255, 0.35)',
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 6,
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 8,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  deckBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  deckText: {
    color: '#00f0ff',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.5,
    fontFamily: 'monospace',
  },
  favBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    borderColor: '#f59e0b',
    borderWidth: 1,
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 10,
  },
  favBtnText: {
    color: '#fbbf24',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: 'monospace',
  },
  trackCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    padding: 10,
    borderRadius: 14,
    marginBottom: 12,
  },
  discCover: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0, 240, 255, 0.12)',
    borderWidth: 1.5,
    borderColor: '#00f0ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  trackDetails: {
    flex: 1,
  },
  title: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  artist: {
    color: '#94a3b8',
    fontSize: 11,
    marginTop: 2,
  },
  progressSection: {
    marginBottom: 14,
  },
  barBackground: {
    height: 5,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    backgroundColor: '#00f0ff',
    position: 'relative',
  },
  barIndicatorGlow: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: 6,
    backgroundColor: '#ffffff',
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 6,
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 5,
  },
  timeVal: {
    color: '#64748b',
    fontSize: 10,
    fontFamily: 'monospace',
    fontWeight: '600',
  },
  controlsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  seekBtn: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: 'rgba(56, 189, 248, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(56, 189, 248, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  skipBtn: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  mainPlayOrb: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#00f0ff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 18,
    elevation: 14,
  },
  mainPlayOrbActive: {
    backgroundColor: '#00ffaa',
    shadowColor: '#00ffaa',
  },
});
