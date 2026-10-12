import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';

interface HeaderProps {
  currentScreen: 'dashboard' | 'employees';
  isDesktop: boolean;
  backendConnected?: boolean;
  isSyncing?: boolean;
  onRefresh?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentScreen,
  isDesktop,
  backendConnected = false,
  isSyncing = false,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.left}>
        {!isDesktop && (
          <View style={styles.mobileBrand}>
            <Ionicons name="people-circle" size={26} color={colors.primary} />
            <Text style={styles.mobileBrandText}>EMS</Text>
          </View>
        )}
        <Text style={styles.screenTitle}>
          {currentScreen === 'dashboard' ? 'Overview Dashboard' : 'Employee Directory'}
        </Text>
      </View>

      <View style={styles.right}>
        {backendConnected ? (
          <View style={styles.statusBadge}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>System Live</Text>
          </View>
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 64,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingHorizontal: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  mobileBrand: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginRight: 8,
  },
  mobileBrandText: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.primary,
  },
  screenTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  right: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: colors.statusActiveBg,
    borderWidth: 1,
    borderColor: colors.statusActiveBorder,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.statusActiveText,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.statusActiveText,
  },
});

