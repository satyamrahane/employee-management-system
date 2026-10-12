import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';

interface MobileBottomNavProps {
  currentScreen: 'dashboard' | 'employees';
  onNavigate: (screen: 'dashboard' | 'employees') => void;
  onOpenAddModal: () => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  currentScreen,
  onNavigate,
  onOpenAddModal,
}) => {
  return (
    <View style={styles.container}>
      {/* Dashboard tab */}
      <Pressable
        style={styles.tabItem}
        onPress={() => onNavigate('dashboard')}
      >
        <Ionicons
          name={currentScreen === 'dashboard' ? 'grid' : 'grid-outline'}
          size={22}
          color={currentScreen === 'dashboard' ? colors.primary : colors.textMuted}
        />
        <Text
          style={[
            styles.tabLabel,
            currentScreen === 'dashboard' && styles.tabLabelActive,
          ]}
        >
          Dashboard
        </Text>
      </Pressable>

      {/* Center Action (Add Employee) */}
      <Pressable style={styles.centerAddButton} onPress={onOpenAddModal}>
        <Ionicons name="add" size={26} color="#FFFFFF" />
      </Pressable>

      {/* Employees tab */}
      <Pressable
        style={styles.tabItem}
        onPress={() => onNavigate('employees')}
      >
        <Ionicons
          name={currentScreen === 'employees' ? 'people' : 'people-outline'}
          size={22}
          color={currentScreen === 'employees' ? colors.primary : colors.textMuted}
        />
        <Text
          style={[
            styles.tabLabel,
            currentScreen === 'employees' && styles.tabLabelActive,
          ]}
        >
          Employees
        </Text>
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 64,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 16,
  },
  tabItem: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 6,
    flex: 1,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: colors.textMuted,
    marginTop: 2,
  },
  tabLabelActive: {
    color: colors.primary,
    fontWeight: '600',
  },
  centerAddButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: -20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
});
