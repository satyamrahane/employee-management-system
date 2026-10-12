import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { EmployeeListItem } from '../types/employee';
import { colors } from '../theme/colors';
import { formatDateDDMMYYYY } from '../utils/date';

interface EmployeeCardMobileProps {
  employee: EmployeeListItem;
  onEdit: (employee: EmployeeListItem) => void;
  onToggleStatus: (id: string) => void;
}

export const EmployeeCardMobile: React.FC<EmployeeCardMobileProps> = ({
  employee,
  onEdit,
  onToggleStatus,
}) => {
  const initials = `${employee.first_name[0] || ''}${employee.last_name[0] || ''}`.toUpperCase();
  const isActive = employee.employment_status === 'ACTIVE';

  return (
    <View style={styles.card}>
      {/* Top Header */}
      <View style={styles.headerRow}>
        <View style={styles.avatarRow}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>
          <View>
            <Text style={styles.nameText}>
              {employee.first_name} {employee.last_name}
            </Text>
            <Text style={styles.codeText}>{employee.employee_code}</Text>
          </View>
        </View>

        {/* Status Badge */}
        <View
          style={[
            styles.statusBadge,
            isActive ? styles.statusActiveBadge : styles.statusInactiveBadge,
          ]}
        >
          <View
            style={[
              styles.statusDot,
              { backgroundColor: isActive ? colors.statusActiveText : colors.statusInactiveText },
            ]}
          />
          <Text
            style={[
              styles.statusText,
              isActive ? styles.statusActiveText : styles.statusInactiveText,
            ]}
          >
            {employee.employment_status}
          </Text>
        </View>
      </View>

      {/* Info Details Grid */}
      <View style={styles.detailsGrid}>
        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>Position</Text>
          <Text style={styles.detailValue}>{employee.job_title}</Text>
        </View>

        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>Department</Text>
          <Text style={styles.detailValue}>{employee.department}</Text>
        </View>

        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>Email</Text>
          <Text style={styles.detailValue} numberOfLines={1}>{employee.email}</Text>
        </View>

        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>Joined</Text>
          <Text style={styles.detailValue}>{formatDateDDMMYYYY(employee.date_of_joining)}</Text>
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionsRow}>
        <Pressable
          style={styles.editButton}
          onPress={() => onEdit(employee)}
        >
          <Ionicons name="create-outline" size={15} color={colors.primaryDark} />
          <Text style={styles.editText}>Edit Profile</Text>
        </Pressable>

        <Pressable
          style={[
            styles.toggleButton,
            isActive ? styles.deactivateButton : styles.activateButton,
          ]}
          onPress={() => onToggleStatus(employee.id)}
        >
          <Ionicons
            name={isActive ? 'pause-circle-outline' : 'play-circle-outline'}
            size={15}
            color={isActive ? colors.warningDark : colors.success}
          />
          <Text
            style={[
              styles.toggleText,
              { color: isActive ? colors.warningDark : colors.success },
            ]}
          >
            {isActive ? 'Deactivate' : 'Activate'}
          </Text>
        </Pressable>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginVertical: 6,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  avatarRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primaryDark,
  },
  nameText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  codeText: {
    fontSize: 11,
    color: colors.textMuted,
    fontFamily: 'monospace',
    marginTop: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    gap: 4,
  },
  statusActiveBadge: {
    backgroundColor: colors.statusActiveBg,
    borderColor: colors.statusActiveBorder,
  },
  statusInactiveBadge: {
    backgroundColor: colors.statusInactiveBg,
    borderColor: colors.statusInactiveBorder,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
  },
  statusActiveText: {
    color: colors.statusActiveText,
  },
  statusInactiveText: {
    color: colors.statusInactiveText,
  },
  detailsGrid: {
    paddingVertical: 12,
    gap: 8,
  },
  detailItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
  },
  detailLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '500',
  },
  detailValue: {
    fontSize: 13,
    color: colors.textPrimary,
    fontWeight: '500',
    flex: 1,
    textAlign: 'right',
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 10,
    paddingTop: 8,
  },
  editButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 8,
    borderRadius: 8,
  },
  editText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  toggleButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  deactivateButton: {
    backgroundColor: colors.warningBg,
    borderColor: colors.warningBorder,
  },
  activateButton: {
    backgroundColor: colors.successBg,
    borderColor: colors.successBorder,
  },
  toggleText: {
    fontSize: 13,
    fontWeight: '600',
  },
});
