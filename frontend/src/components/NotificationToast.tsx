import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Animated,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';

export interface NotificationToastProps {
  message: string;
  type: 'success' | 'error';
  onDismiss: () => void;
  duration?: number;
}

export const NotificationToast: React.FC<NotificationToastProps> = ({
  message,
  type = 'success',
  onDismiss,
  duration = 4000,
}) => {
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const translateYAnim = useRef(new Animated.Value(-12)).current;

  useEffect(() => {
    // Subtle entry transition
    Animated.parallel([
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: Platform.OS !== 'web',
      }),
      Animated.timing(translateYAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: Platform.OS !== 'web',
      }),
    ]).start();

    // Auto-dismiss timer
    const timer = setTimeout(() => {
      handleDismiss();
    }, duration);

    return () => clearTimeout(timer);
  }, [message, type, duration]);

  const handleDismiss = () => {
    Animated.parallel([
      Animated.timing(opacityAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: Platform.OS !== 'web',
      }),
      Animated.timing(translateYAnim, {
        toValue: -8,
        duration: 150,
        useNativeDriver: Platform.OS !== 'web',
      }),
    ]).start(() => {
      onDismiss();
    });
  };

  const isSuccess = type === 'success';

  return (
    <Animated.View
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
      style={[
        styles.toastContainer,
        {
          opacity: opacityAnim,
          transform: [{ translateY: translateYAnim }],
          borderLeftColor: isSuccess ? colors.primary : colors.danger,
        },
      ]}
    >
      <View
        style={[
          styles.iconWrapper,
          { backgroundColor: isSuccess ? colors.primaryLight : colors.dangerBg },
        ]}
      >
        <Ionicons
          name={isSuccess ? 'checkmark-circle' : 'alert-circle'}
          size={18}
          color={isSuccess ? colors.primary : colors.danger}
        />
      </View>

      <View style={styles.messageContainer}>
        <Text style={styles.messageText} numberOfLines={3}>
          {message}
        </Text>
      </View>

      <Pressable
        accessibilityLabel="Dismiss notification"
        accessibilityRole="button"
        onPress={handleDismiss}
        style={styles.closeButton}
      >
        <Ionicons name="close" size={16} color={colors.textMuted} />
      </Pressable>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  toastContainer: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    borderLeftWidth: 4,
    paddingVertical: 12,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 4,
    maxWidth: 460,
    minWidth: 280,
  },
  iconWrapper: {
    width: 28,
    height: 28,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  messageContainer: {
    flex: 1,
  },
  messageText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textPrimary,
    lineHeight: 18,
  },
  closeButton: {
    padding: 4,
    marginLeft: 4,
  },
});
