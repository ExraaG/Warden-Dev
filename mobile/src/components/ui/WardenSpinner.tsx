import React, { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet } from 'react-native';

export const WardenSpinner: React.FC<{ size?: number; color?: string }> = ({
  size = 20,
  color = '#1bd96a',
}) => {
  const spinValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.timing(spinValue, {
        toValue: 1,
        duration: 700,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    );
    loop.start();
    return () => loop.stop();
  }, [spinValue]);

  const spin = spinValue.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <Animated.View
      style={[
        styles.spinner,
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          borderWidth: 2,
          borderColor: color,
          borderTopColor: 'transparent',
          transform: [{ rotate: spin }],
        },
      ]}
    />
  );
};

const styles = StyleSheet.create({
  spinner: {
    borderStyle: 'solid',
  },
});
