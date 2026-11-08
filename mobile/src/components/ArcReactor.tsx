import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Easing, TouchableOpacity } from 'react-native';
import { AssistantState } from '../types';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface Props {
  state: AssistantState;
  onPress?: () => void;
  size?: number;
}

export const ArcReactor: React.FC<Props> = ({ state, onPress, size = 160 }) => {
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Rotation animation
    const rotateLoop = Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: state === 'LISTENING' ? 4000 : state === 'THINKING' ? 2000 : 10000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    );
    rotateLoop.start();

    // Pulse animation
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: state === 'LISTENING' ? 1.15 : state === 'SPEAKING' ? 1.1 : 1.05,
          duration: state === 'LISTENING' ? 600 : 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: state === 'LISTENING' ? 600 : 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    pulseLoop.start();

    return () => {
      rotateLoop.stop();
      pulseLoop.stop();
    };
  }, [state, rotateAnim, pulseAnim]);

  const spin = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const getCoreColor = () => {
    switch (state) {
      case 'LISTENING':
        return '#00ffcc'; // neon green-cyan
      case 'THINKING':
        return '#ffb703'; // glowing amber
      case 'SPEAKING':
        return '#00f0ff'; // stark cyan
      case 'PLAYING':
        return '#7b2cbf'; // neon purple
      case 'CALLING':
        return '#2ec4b6'; // vibrant teal
      default:
        return '#00e5ff'; // classic arc reactor cyan
    }
  };

  const coreColor = getCoreColor();

  return (
    <TouchableOpacity
      activeOpacity={0.8}
      onPress={onPress}
      style={[styles.container, { width: size, height: size }]}
    >
      {/* Outer Pulse Glow Ring */}
      <Animated.View
        style={[
          styles.glowRing,
          {
            width: size * 1.1,
            height: size * 1.1,
            borderRadius: (size * 1.1) / 2,
            borderColor: coreColor,
            shadowColor: coreColor,
            transform: [{ scale: pulseAnim }],
          },
        ]}
      />

      {/* Rotating Ring */}
      <Animated.View
        style={[
          styles.rotatorRing,
          {
            width: size * 0.9,
            height: size * 0.9,
            borderRadius: (size * 0.9) / 2,
            borderColor: coreColor,
            transform: [{ rotate: spin }],
          },
        ]}
      >
        <View style={[styles.triSegment, { borderColor: coreColor }]} />
      </Animated.View>

      {/* Inner Core */}
      <Animated.View
        style={[
          styles.coreCircle,
          {
            width: size * 0.55,
            height: size * 0.55,
            borderRadius: (size * 0.55) / 2,
            backgroundColor: `${coreColor}22`,
            borderColor: coreColor,
            transform: [{ scale: pulseAnim }],
          },
        ]}
      >
        <MaterialCommunityIcons
          name={
            state === 'LISTENING'
              ? 'microphone'
              : state === 'PLAYING'
              ? 'music'
              : state === 'CALLING'
              ? 'phone-in-talk'
              : 'atom'
          }
          size={size * 0.28}
          color={coreColor}
        />
      </Animated.View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  glowRing: {
    position: 'absolute',
    borderWidth: 2,
    opacity: 0.4,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 18,
    elevation: 10,
  },
  rotatorRing: {
    position: 'absolute',
    borderWidth: 1.5,
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
  },
  triSegment: {
    width: '90%',
    height: '90%',
    borderRadius: 1000,
    borderWidth: 1,
    borderStyle: 'dotted',
  },
  coreCircle: {
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2.5,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 15,
    elevation: 12,
  },
});

