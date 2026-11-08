import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing, TouchableOpacity } from 'react-native';
import { AssistantState } from '../types';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface Props {
  state: AssistantState;
  onPress?: () => void;
  size?: number;
}

export const ArcReactor: React.FC<Props> = ({ state, onPress, size = 190 }) => {
  const rotateClockwise = useRef(new Animated.Value(0)).current;
  const rotateCounter = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.6)).current;

  useEffect(() => {
    // Clockwise Outer Ring
    const cwLoop = Animated.loop(
      Animated.timing(rotateClockwise, {
        toValue: 1,
        duration: state === 'THINKING' ? 2500 : state === 'LISTENING' ? 4000 : 12000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    );
    cwLoop.start();

    // Counter-Clockwise Middle Ring
    const ccwLoop = Animated.loop(
      Animated.timing(rotateCounter, {
        toValue: 1,
        duration: state === 'THINKING' ? 3000 : state === 'LISTENING' ? 5000 : 15000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    );
    ccwLoop.start();

    // Pulse Core
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: state === 'LISTENING' ? 1.18 : state === 'SPEAKING' ? 1.12 : 1.06,
          duration: state === 'LISTENING' ? 500 : state === 'SPEAKING' ? 800 : 1600,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: state === 'LISTENING' ? 500 : state === 'SPEAKING' ? 800 : 1600,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    pulseLoop.start();

    // Glow Breathing
    const glowLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 1000,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0.5,
          duration: 1000,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    glowLoop.start();

    return () => {
      cwLoop.stop();
      ccwLoop.stop();
      pulseLoop.stop();
      glowLoop.stop();
    };
  }, [state, rotateClockwise, rotateCounter, pulseAnim, glowAnim]);

  const spinCW = rotateClockwise.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const spinCCW = rotateCounter.interpolate({
    inputRange: [0, 1],
    outputRange: ['360deg', '0deg'],
  });

  const getTheme = () => {
    switch (state) {
      case 'LISTENING':
        return {
          primary: '#00ffaa',
          secondary: 'rgba(0, 255, 170, 0.25)',
          glow: '#00ffaa',
          label: 'LISTENING...',
          icon: 'microphone',
        };
      case 'THINKING':
        return {
          primary: '#f59e0b',
          secondary: 'rgba(245, 158, 11, 0.25)',
          glow: '#f59e0b',
          label: 'PROCESSING',
          icon: 'brain',
        };
      case 'SPEAKING':
        return {
          primary: '#38bdf8',
          secondary: 'rgba(56, 189, 248, 0.25)',
          glow: '#00f0ff',
          label: 'SPEAKING',
          icon: 'waveform',
        };
      case 'PLAYING':
        return {
          primary: '#c084fc',
          secondary: 'rgba(192, 132, 252, 0.25)',
          glow: '#a855f7',
          label: 'AUDIO ACTIVE',
          icon: 'music-note',
        };
      case 'CALLING':
        return {
          primary: '#2dd4bf',
          secondary: 'rgba(45, 212, 191, 0.25)',
          glow: '#14b8a6',
          label: 'CALL IN PROGRESS',
          icon: 'phone-in-talk',
        };
      default:
        return {
          primary: '#00f0ff',
          secondary: 'rgba(0, 240, 255, 0.2)',
          glow: '#00f0ff',
          label: 'STARK MK-85 // READY',
          icon: 'atom',
        };
    }
  };

  const theme = getTheme();

  return (
    <View style={styles.wrapper}>
      <TouchableOpacity
        activeOpacity={0.85}
        onPress={onPress}
        style={[styles.container, { width: size, height: size }]}
      >
        {/* Outermost Holographic Halo */}
        <Animated.View
          style={[
            styles.outerHalo,
            {
              width: size * 1.16,
              height: size * 1.16,
              borderRadius: (size * 1.16) / 2,
              borderColor: theme.secondary,
              shadowColor: theme.glow,
              opacity: glowAnim,
              transform: [{ scale: pulseAnim }],
            },
          ]}
        />

        {/* Outer Tech Ring with Segmented Ticks */}
        <Animated.View
          style={[
            styles.outerTechRing,
            {
              width: size,
              height: size,
              borderRadius: size / 2,
              borderColor: theme.primary,
              transform: [{ rotate: spinCW }],
            },
          ]}
        >
          <View style={[styles.tickMark, styles.tickTop, { backgroundColor: theme.primary }]} />
          <View style={[styles.tickMark, styles.tickRight, { backgroundColor: theme.primary }]} />
          <View style={[styles.tickMark, styles.tickBottom, { backgroundColor: theme.primary }]} />
          <View style={[styles.tickMark, styles.tickLeft, { backgroundColor: theme.primary }]} />
        </Animated.View>

        {/* Middle Counter-Rotating Ring */}
        <Animated.View
          style={[
            styles.middleDashedRing,
            {
              width: size * 0.78,
              height: size * 0.78,
              borderRadius: (size * 0.78) / 2,
              borderColor: theme.primary,
              transform: [{ rotate: spinCCW }],
            },
          ]}
        >
          <View style={[styles.crossHairH, { backgroundColor: `${theme.primary}55` }]} />
          <View style={[styles.crossHairV, { backgroundColor: `${theme.primary}55` }]} />
        </Animated.View>

        {/* Inner Glowing Reactor Core */}
        <Animated.View
          style={[
            styles.coreCircle,
            {
              width: size * 0.52,
              height: size * 0.52,
              borderRadius: (size * 0.52) / 2,
              backgroundColor: '#040b17',
              borderColor: theme.primary,
              shadowColor: theme.glow,
              transform: [{ scale: pulseAnim }],
            },
          ]}
        >
          <View
            style={[
              styles.innerGlowBackdrop,
              { backgroundColor: theme.secondary, borderRadius: (size * 0.52) / 2 },
            ]}
          />
          <MaterialCommunityIcons
            name={theme.icon as any}
            size={size * 0.25}
            color={theme.primary}
          />
        </Animated.View>
      </TouchableOpacity>

      {/* Cybernetic Status Badge */}
      <View style={[styles.statusBadge, { borderColor: `${theme.primary}44` }]}>
        <View style={[styles.statusDot, { backgroundColor: theme.primary }]} />
        <Text style={[styles.statusText, { color: theme.primary }]}>
          {theme.label}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  container: {
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  outerHalo: {
    position: 'absolute',
    borderWidth: 1.5,
    borderStyle: 'dashed',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 24,
    elevation: 12,
  },
  outerTechRing: {
    position: 'absolute',
    borderWidth: 2,
    borderStyle: 'solid',
    justifyContent: 'center',
    alignItems: 'center',
  },
  tickMark: {
    position: 'absolute',
    borderRadius: 2,
  },
  tickTop: {
    top: -6,
    width: 4,
    height: 12,
  },
  tickRight: {
    right: -6,
    width: 12,
    height: 4,
  },
  tickBottom: {
    bottom: -6,
    width: 4,
    height: 12,
  },
  tickLeft: {
    left: -6,
    width: 12,
    height: 4,
  },
  middleDashedRing: {
    position: 'absolute',
    borderWidth: 1.5,
    borderStyle: 'dotted',
    justifyContent: 'center',
    alignItems: 'center',
  },
  crossHairH: {
    position: 'absolute',
    width: '100%',
    height: 1,
  },
  crossHairV: {
    position: 'absolute',
    height: '100%',
    width: 1,
  },
  coreCircle: {
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2.5,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 20,
    elevation: 16,
    position: 'relative',
    overflow: 'hidden',
  },
  innerGlowBackdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    opacity: 0.6,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 14,
    backgroundColor: 'rgba(3, 7, 18, 0.85)',
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 16,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.8,
    fontFamily: 'monospace',
  },
});
