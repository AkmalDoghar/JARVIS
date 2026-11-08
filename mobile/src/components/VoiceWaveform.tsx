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
  count = 12,
}) => {
  const anims = useRef(
    Array.from({ length: count }, () => new Animated.Value(6))
  ).current;

  useEffect(() => {
    if (!isActive) {
      anims.forEach(anim => anim.setValue(6));
      return;
    }

    const loops = anims.map((anim, idx) => {
      const delay = idx * 60;
      const targetHeight = 12 + ((idx % 5) + 1) * 7;
      return Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(anim, {
            toValue: targetHeight,
            duration: 250 + (idx % 3) * 70,
            useNativeDriver: false,
          }),
          Animated.timing(anim, {
            toValue: 6,
            duration: 250 + (idx % 3) * 70,
            useNativeDriver: false,
          }),
        ])
      );
    });

    loops.forEach(l => l.start());

    return () => {
      loops.forEach(l => l.stop());
    };
  }, [isActive, anims]);

  return (
    <View style={styles.container}>
      {anims.map((anim, idx) => (
        <Animated.View
          key={idx}
          style={[
            styles.bar,
            {
              backgroundColor: barColor,
              height: anim,
            },
          ]}
        />
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 48,
    gap: 4,
  },
  bar: {
    width: 3.5,
    borderRadius: 2,
    shadowColor: '#00f0ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
    elevation: 3,
  },
});

