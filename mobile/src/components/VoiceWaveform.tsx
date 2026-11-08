import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';

interface Props {
  isActive: boolean;
  barColor?: string;
  count?: number;
}

export const VoiceWaveform: React.FC<Props> = ({
  isActive,
  barColor = '#00f0ff',
  count = 20,
}) => {
  // Symmetrical curve heights
  const anims = useRef(
    Array.from({ length: count }, () => new Animated.Value(4))
  ).current;

  useEffect(() => {
    if (!isActive) {
      anims.forEach((anim) => {
        Animated.timing(anim, {
          toValue: 4,
          duration: 300,
          useNativeDriver: false,
        }).start();
      });
      return;
    }

    const mid = count / 2;
    const loops = anims.map((anim, idx) => {
      // Bell curve factor: middle bars are taller
      const distanceFromMid = Math.abs(idx - mid);
      const factor = 1 - distanceFromMid / mid;
      const maxHeight = 8 + factor * 28 + (idx % 3) * 6;

      const delay = Math.abs(idx - mid) * 45;
      return Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(anim, {
            toValue: maxHeight,
            duration: 220 + (idx % 4) * 60,
            useNativeDriver: false,
          }),
          Animated.timing(anim, {
            toValue: 4,
            duration: 220 + (idx % 4) * 60,
            useNativeDriver: false,
          }),
        ])
      );
    });

    loops.forEach((l) => l.start());

    return () => {
      loops.forEach((l) => l.stop());
    };
  }, [isActive, anims, count]);

  return (
    <View style={styles.container}>
      <View style={styles.glowUnderlay} />
      {anims.map((anim, idx) => {
        const isCenter = Math.abs(idx - count / 2) < 3;
        return (
          <Animated.View
            key={idx}
            style={[
              styles.bar,
              {
                backgroundColor: isCenter ? '#ffffff' : barColor,
                height: anim,
                shadowColor: barColor,
              },
            ]}
          />
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 48,
    gap: 3.5,
    marginVertical: 4,
    position: 'relative',
  },
  glowUnderlay: {
    position: 'absolute',
    width: '60%',
    height: 16,
    backgroundColor: 'rgba(0, 240, 255, 0.12)',
    borderRadius: 8,
    filter: 'blur(10px)',
  },
  bar: {
    width: 3.5,
    borderRadius: 3,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 8,
    elevation: 4,
  },
});
