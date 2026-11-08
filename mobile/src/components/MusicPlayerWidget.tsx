import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Track } from '../types';
import * as Haptics from 'expo-haptics';

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

  const handleAction = (action: () => void) => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    } catch (e) {
      // ignore
    }
    action();
  };

  return (
    <View style={styles.card}>
      {/* Header bar */}
      <View style={styles.header}>
        <View style={styles.badgeRow}>
          <MaterialCommunityIcons name="headphones" size={16} color="#00f0ff" />
          <Text style={styles.badgeText}>BIKE AUDIO DECK</Text>
        </View>
        <TouchableOpacity
          style={styles.favBadge}
          onPress={() => handleAction(onPlayFavorites)}
        >
          <MaterialCommunityIcons name="heart-pulse" size={14} color="#ff0055" />
          <Text style={styles.favText}>FAVORITES</Text>
        </TouchableOpacity>
      </View>

      {/* Track Info */}
      <View style={styles.infoBox}>
        <Text style={styles.trackTitle} numberOfLines={1}>
          {track ? track.title : 'No Track Selected'}
        </Text>
        <Text style={styles.trackArtist} numberOfLines={1}>
          {track ? track.artist : 'Say "JARVIS play favorite songs"'}
        </Text>
      </View>

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBarBg}>
          <View style={[styles.progressBarFill, { width: `${progressPercent}%` }]} />
        </View>
        <View style={styles.timeRow}>
          <Text style={styles.timeText}>{formatTime(position)}</Text>
          <Text style={styles.timeText}>{formatTime(duration)}</Text>
        </View>
      </View>

      {/* Bike-Optimized Oversized Controls */}
      <View style={styles.controlsRow}>
        {/* Seek -15s */}
        <TouchableOpacity
          style={styles.subBtn}
          onPress={() => handleAction(onSeekBackward)}
        >
          <MaterialCommunityIcons name="rewind-15" size={26} color="#00f0ff" />
        </TouchableOpacity>

        {/* Prev */}
        <TouchableOpacity
          style={styles.medBtn}
          onPress={() => handleAction(onPrev)}
        >
          <MaterialCommunityIcons name="skip-previous" size={32} color="#ffffff" />
        </TouchableOpacity>

        {/* Big Central Play/Pause Button */}
        <TouchableOpacity
          style={[styles.bigPlayBtn, isPlaying && styles.bigPlayBtnActive]}
          onPress={() => handleAction(onPlayPause)}
        >
          <MaterialCommunityIcons
            name={isPlaying ? 'pause' : 'play'}
            size={40}
            color="#050a14"
          />
        </TouchableOpacity>

        {/* Next */}
        <TouchableOpacity
          style={styles.medBtn}
          onPress={() => handleAction(onNext)}
        >
          <MaterialCommunityIcons name="skip-next" size={32} color="#ffffff" />
        </TouchableOpacity>

        {/* Seek +15s */}
        <TouchableOpacity
          style={styles.subBtn}
          onPress={() => handleAction(onSeekForward)}
        >
          <MaterialCommunityIcons name="fast-forward-15" size={26} color="#00f0ff" />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'rgba(10, 20, 35, 0.85)',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.3)',
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  badgeText: {
    color: '#00f0ff',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  favBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255, 0, 85, 0.15)',
    borderColor: '#ff0055',
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  favText: {
    color: '#ff6699',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
  },
  infoBox: {
    marginBottom: 10,
  },
  trackTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  trackArtist: {
    color: '#94a3b8',
    fontSize: 12,
    marginTop: 2,
  },
  progressContainer: {
    marginBottom: 12,
  },
  progressBarBg: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#00f0ff',
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  timeText: {
    color: '#64748b',
    fontSize: 10,
    fontFamily: 'monospace',
  },
  controlsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  subBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0, 240, 255, 0.08)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.2)',
  },
  medBtn: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  bigPlayBtn: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#00f0ff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 16,
    elevation: 12,
  },
  bigPlayBtnActive: {
    backgroundColor: '#38ef7d',
    shadowColor: '#38ef7d',
  },
});

