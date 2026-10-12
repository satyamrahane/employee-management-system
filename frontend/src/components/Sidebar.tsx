import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';

interface SidebarProps {
  currentScreen: 'dashboard' | 'employees';
  onNavigate: (screen: 'dashboard' | 'employees') => void;
  onOpenAddModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentScreen,
  onNavigate,
  onOpenAddModal,
}) => {
  return (
    <View style={styles.container}>
      {/* Brand / Logo */}
      <View style={styles.brandContainer}>
        <View style={styles.logoIcon}>
          <Ionicons name="business" size={20} color="#FFFFFF" />
        </View>
        <View>
          <Text style={styles.brandTitle}>EMS Admin</Text>
          <Text style={styles.brandSubtitle}>Management Portal</Text>
        </View>
      </View>

      {/* Primary Action Button */}
      <View style={styles.actionContainer}>
        <Pressable
          style={({ hovered }: any) => [
            styles.addButton,
            hovered && styles.addButtonHovered,
          ]}
          onPress={onOpenAddModal}
        >
          <Ionicons name="add" size={18} color="#FFFFFF" />
          <Text style={styles.addButtonText}>Add Employee</Text>
        </Pressable>
      </View>

      {/* Navigation Links */}
      <View style={styles.navSection}>
        <Text style={styles.sectionLabel}>MAIN MENU</Text>

        <Pressable
          style={({ hovered }: any) => [
            styles.navItem,
            currentScreen === 'dashboard' && styles.navItemActive,
            hovered && styles.navItemHovered,
          ]}
          onPress={() => onNavigate('dashboard')}
        >
          <Ionicons
            name={currentScreen === 'dashboard' ? 'grid' : 'grid-outline'}
            size={18}
            color={currentScreen === 'dashboard' ? colors.sidebarTextActive : colors.sidebarText}
          />
          <Text
            style={[
              styles.navText,
              currentScreen === 'dashboard' && styles.navTextActive,
            ]}
          >
            Dashboard
          </Text>
        </Pressable>

        <Pressable
          style={({ hovered }: any) => [
            styles.navItem,
            currentScreen === 'employees' && styles.navItemActive,
            hovered && styles.navItemHovered,
          ]}
          onPress={() => onNavigate('employees')}
        >
          <Ionicons
            name={currentScreen === 'employees' ? 'people' : 'people-outline'}
            size={18}
            color={currentScreen === 'employees' ? colors.sidebarTextActive : colors.sidebarText}
          />
          <Text
            style={[
              styles.navText,
              currentScreen === 'employees' && styles.navTextActive,
            ]}
          >
            Employees
          </Text>
        </Pressable>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: 240,
    backgroundColor: colors.sidebar,
    paddingVertical: 20,
    paddingHorizontal: 16,
    flexDirection: 'column',
  },
  brandContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: colors.sidebarActive,
  },
  logoIcon: {
    width: 38,
    height: 38,
    borderRadius: 8,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  brandSubtitle: {
    color: colors.sidebarText,
    fontSize: 11,
  },
  actionContainer: {
    marginTop: 20,
    marginBottom: 16,
  },
  addButton: {
    backgroundColor: colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  addButtonHovered: {
    backgroundColor: colors.primaryDark,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  navSection: {
    marginTop: 8,
    flex: 1,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
    marginBottom: 8,
    paddingHorizontal: 8,
    letterSpacing: 0.5,
  },
  navItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: 4,
  },
  navItemActive: {
    backgroundColor: colors.sidebarActive,
  },
  navItemHovered: {
    backgroundColor: '#1E293B99',
  },
  navText: {
    color: colors.sidebarText,
    fontSize: 14,
    fontWeight: '500',
  },
  navTextActive: {
    color: colors.sidebarTextActive,
    fontWeight: '600',
  },
});

