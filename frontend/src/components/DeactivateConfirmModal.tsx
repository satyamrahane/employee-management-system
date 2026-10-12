import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Employee } from '../types/employee';
import { colors } from '../theme/colors';
import { formatDateDDMMYYYY } from '../utils/date';

interface DeactivateConfirmModalProps {
  visible: boolean;
  employee: Employee | null;
  onCancel: () => void;
  onConfirm: () => void;
  isSubmitting?: boolean;
}

export const DeactivateConfirmModal: React.FC<DeactivateConfirmModalProps> = ({
  visible,
  employee,
  onCancel,
  onConfirm,
  isSubmitting = false,
}) => {
  if (!employee) return null;

  const fullName = `${employee.first_name} ${employee.last_name}`;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <View style={styles.overlay}>
        <View style={styles.dialogCard}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.iconContainer}>
              <Ionicons name="alert-circle-outline" size={22} color={colors.warning} />
            </View>
            <View style={styles.headerTextGroup}>
              <Text style={styles.title}>Confirm Deactivation</Text>
              <Text style={styles.subtitle}>Action requires confirmation</Text>
            </View>
            <Pressable
              style={styles.closeButton}
              onPress={onCancel}
              disabled={isSubmitting}
            >
              <Ionicons name="close" size={20} color={colors.textSecondary} />
            </Pressable>
          </View>

          {/* Body */}
          <View style={styles.body}>
            <Text style={styles.message}>
              Are you sure you want to deactivate <Text style={styles.highlightName}>{fullName}</Text>?
            </Text>
            <Text style={styles.consequenceText}>
              This will update their employment status to <Text style={styles.statusInactiveText}>INACTIVE</Text> and exclude them from active headcount totals. This record can be reactivated at any time.
            </Text>

            {/* Employee Metadata Box */}
            <View style={styles.detailsBox}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Employee Code</Text>
                <Text style={styles.detailValue}>{employee.employee_code}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Department</Text>
                <Text style={styles.detailValue}>{employee.department}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Job Title</Text>
                <Text style={styles.detailValue}>{employee.job_title}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Joined</Text>
                <Text style={styles.detailValue}>{formatDateDDMMYYYY(employee.date_of_joining)}</Text>
              </View>
            </View>
          </View>

          {/* Footer Actions */}
          <View style={styles.footer}>
            <Pressable
              style={styles.cancelButton}
              onPress={onCancel}
              disabled={isSubmitting}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </Pressable>

            <Pressable
              style={[styles.confirmButton, isSubmitting && styles.buttonDisabled]}
              onPress={onConfirm}
              disabled={isSubmitting}
            >
              <Text style={styles.confirmButtonText}>
                {isSubmitting ? 'Deactivating...' : 'Confirm Deactivation'}
              </Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  dialogCard: {
    width: '100%',
    maxWidth: 440,
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: colors.warningBg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTextGroup: {
    flex: 1,
  },
  title: {
    fontSize: 17,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  subtitle: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  closeButton: {
    padding: 4,
  },
  body: {
    marginBottom: 20,
  },
  message: {
    fontSize: 14,
    color: colors.textPrimary,
    lineHeight: 20,
  },
  highlightName: {
    fontWeight: '700',
    color: colors.textPrimary,
  },
  consequenceText: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 18,
    marginTop: 8,
  },
  statusInactiveText: {
    fontWeight: '700',
    color: colors.warning,
  },
  detailsBox: {
    backgroundColor: colors.background,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 12,
    marginTop: 14,
    gap: 6,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    color: colors.textMuted,
  },
  detailValue: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  cancelButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  confirmButton: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 8,
    backgroundColor: colors.danger,
    alignItems: 'center',
    justifyContent: 'center',
  },
  confirmButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});
