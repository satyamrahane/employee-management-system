import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  StyleSheet,
  Pressable,
  ScrollView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { EmployeeListItem, EmployeeFormData, Department } from '../types/employee';
import { colors } from '../theme/colors';
import { DatePickerInput } from './DatePickerInput';
import { formatDateDDMMYYYY, parseDDMMYYYYToISO } from '../utils/date';

interface EmployeeModalFormProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: (data: EmployeeFormData) => void;
  initialEmployee?: EmployeeListItem | null;
  existingEmployees?: EmployeeListItem[];
  backendError?: string | null;
  isSubmitting?: boolean;
}

const DEPARTMENTS: Department[] = [
  'Engineering',
  'Design',
  'Product',
  'Human Resources',
  'Finance',
  'Marketing',
  'Sales',
  'Operations',
  'People Analytics',
];

export const EmployeeModalForm: React.FC<EmployeeModalFormProps> = ({
  visible,
  onClose,
  onSubmit,
  initialEmployee,
  existingEmployees = [],
  backendError = null,
  isSubmitting = false,
}) => {
  const [formData, setFormData] = useState<EmployeeFormData>({
    employee_code: '',
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    job_title: '',
    department: 'Engineering',
    date_of_joining: new Date().toISOString().split('T')[0],
    employment_status: 'ACTIVE',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (initialEmployee) {
      setFormData({
        employee_code: initialEmployee.employee_code,
        first_name: initialEmployee.first_name,
        last_name: initialEmployee.last_name,
        email: initialEmployee.email,
        phone_number: initialEmployee.phone_number,
        job_title: initialEmployee.job_title,
        department: initialEmployee.department,
        date_of_joining: initialEmployee.date_of_joining,
        employment_status: initialEmployee.employment_status,
      });
    } else {
      setFormData({
        employee_code: `EMP-${Math.floor(1000 + Math.random() * 9000)}`,
        first_name: '',
        last_name: '',
        email: '',
        phone_number: '',
        job_title: '',
        department: 'Engineering',
        date_of_joining: new Date().toISOString().split('T')[0],
        employment_status: 'ACTIVE',
      });
    }
    setErrors({});
  }, [initialEmployee, visible]);

  const handleFieldChange = (field: keyof EmployeeFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required.';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required.';
    }
    if (!formData.employee_code.trim()) {
      newErrors.employee_code = 'Employee code is required.';
    } else if (
      existingEmployees.some(
        (emp) =>
          emp.employee_code.trim().toUpperCase() === formData.employee_code.trim().toUpperCase() &&
          emp.id !== initialEmployee?.id
      )
    ) {
      newErrors.employee_code = 'An employee with this code already exists.';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = 'Please enter a valid email address.';
    } else if (
      existingEmployees.some(
        (emp) =>
          emp.email.trim().toLowerCase() === formData.email.trim().toLowerCase() &&
          emp.id !== initialEmployee?.id
      )
    ) {
      newErrors.email = 'An employee with this email address already exists.';
    }

    if (!formData.job_title.trim()) {
      newErrors.job_title = 'Job title is required.';
    }

    if (!formData.date_of_joining.trim()) {
      newErrors.date_of_joining = 'Date of joining is required.';
    } else {
      let isoDate = formData.date_of_joining.trim();
      if (/^\d{2}-\d{2}-\d{4}$/.test(isoDate)) {
        isoDate = parseDDMMYYYYToISO(isoDate);
      }
      if (!/^\d{4}-\d{2}-\d{2}$/.test(isoDate)) {
        newErrors.date_of_joining = 'Date must be formatted as DD-MM-YYYY or YYYY-MM-DD.';
      } else {
        const [yStr, mStr, dStr] = isoDate.split('-');
        const y = parseInt(yStr, 10);
        const m = parseInt(mStr, 10);
        const d = parseInt(dStr, 10);
        if (y < 1970 || y > 2100 || m < 1 || m > 12 || d < 1 || d > 31) {
          newErrors.date_of_joining = 'Please select a valid calendar date.';
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (isSubmitting) return; // Prevent duplicate submissions
    if (validate()) {
      let submissionDate = formData.date_of_joining.trim();
      if (/^\d{2}-\d{2}-\d{4}$/.test(submissionDate)) {
        submissionDate = parseDDMMYYYYToISO(submissionDate);
      }
      onSubmit({ ...formData, date_of_joining: submissionDate });
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalCard}>
          {/* Header */}
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>
                {initialEmployee ? 'Edit Employee Profile' : 'Add New Employee'}
              </Text>
              <Text style={styles.subtitle}>
                {initialEmployee
                  ? `Updating record for ${initialEmployee.employee_code}`
                  : 'Enter employee information to create a new profile'}
              </Text>
            </View>
            <Pressable
              style={styles.closeButton}
              onPress={onClose}
              disabled={isSubmitting}
            >
              <Ionicons name="close" size={20} color={colors.textSecondary} />
            </Pressable>
          </View>

          {/* Form Scroll Body */}
          <ScrollView style={styles.formBody} showsVerticalScrollIndicator={false}>
            {/* Backend Error Alert Banner */}
            {backendError ? (
              <View style={styles.backendErrorBox}>
                <Ionicons name="alert-circle" size={18} color={colors.danger} />
                <Text style={styles.backendErrorText}>{backendError}</Text>
              </View>
            ) : null}

            {/* Row: First Name & Last Name */}
            <View style={styles.row}>
              <View style={styles.col}>
                <Text style={styles.label}>First Name *</Text>
                <TextInput
                  style={[styles.input, errors.first_name && styles.inputError]}
                  placeholder="e.g. Maya"
                  placeholderTextColor={colors.textMuted}
                  value={formData.first_name}
                  onChangeText={(text) => handleFieldChange('first_name', text)}
                  editable={!isSubmitting}
                  returnKeyType="next"
                />
                {errors.first_name ? (
                  <View style={styles.errorRow}>
                    <Ionicons name="alert-circle" size={13} color={colors.danger} />
                    <Text style={styles.errorText}>{errors.first_name}</Text>
                  </View>
                ) : null}
              </View>

              <View style={styles.col}>
                <Text style={styles.label}>Last Name *</Text>
                <TextInput
                  style={[styles.input, errors.last_name && styles.inputError]}
                  placeholder="e.g. Patel"
                  placeholderTextColor={colors.textMuted}
                  value={formData.last_name}
                  onChangeText={(text) => handleFieldChange('last_name', text)}
                  editable={!isSubmitting}
                  returnKeyType="next"
                />
                {errors.last_name ? (
                  <View style={styles.errorRow}>
                    <Ionicons name="alert-circle" size={13} color={colors.danger} />
                    <Text style={styles.errorText}>{errors.last_name}</Text>
                  </View>
                ) : null}
              </View>
            </View>

            {/* Row: Employee Code & Job Title */}
            <View style={styles.row}>
              <View style={styles.col}>
                <Text style={styles.label}>Employee Code *</Text>
                <TextInput
                  style={[styles.input, errors.employee_code && styles.inputError]}
                  placeholder="e.g. EMP-1010"
                  placeholderTextColor={colors.textMuted}
                  value={formData.employee_code}
                  onChangeText={(text) => handleFieldChange('employee_code', text)}
                  editable={!isSubmitting}
                  returnKeyType="next"
                />
                {errors.employee_code ? (
                  <View style={styles.errorRow}>
                    <Ionicons name="alert-circle" size={13} color={colors.danger} />
                    <Text style={styles.errorText}>{errors.employee_code}</Text>
                  </View>
                ) : null}
              </View>

              <View style={styles.col}>
                <Text style={styles.label}>Job Title *</Text>
                <TextInput
                  style={[styles.input, errors.job_title && styles.inputError]}
                  placeholder="e.g. Systems Engineer"
                  placeholderTextColor={colors.textMuted}
                  value={formData.job_title}
                  onChangeText={(text) => handleFieldChange('job_title', text)}
                  editable={!isSubmitting}
                  returnKeyType="next"
                />
                {errors.job_title ? (
                  <View style={styles.errorRow}>
                    <Ionicons name="alert-circle" size={13} color={colors.danger} />
                    <Text style={styles.errorText}>{errors.job_title}</Text>
                  </View>
                ) : null}
              </View>
            </View>

            {/* Row: Email & Phone */}
            <View style={styles.row}>
              <View style={styles.col}>
                <Text style={styles.label}>Work Email *</Text>
                <TextInput
                  style={[styles.input, errors.email && styles.inputError]}
                  placeholder="name@company.com"
                  placeholderTextColor={colors.textMuted}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  value={formData.email}
                  onChangeText={(text) => handleFieldChange('email', text)}
                  editable={!isSubmitting}
                  returnKeyType="next"
                />
                {errors.email ? (
                  <View style={styles.errorRow}>
                    <Ionicons name="alert-circle" size={13} color={colors.danger} />
                    <Text style={styles.errorText}>{errors.email}</Text>
                  </View>
                ) : null}
              </View>

              <View style={styles.col}>
                <Text style={styles.label}>Phone Number (Optional)</Text>
                <TextInput
                  style={styles.input}
                  placeholder="+1 (555) 000-0000"
                  placeholderTextColor={colors.textMuted}
                  keyboardType="phone-pad"
                  value={formData.phone_number}
                  onChangeText={(text) => handleFieldChange('phone_number', text)}
                  editable={!isSubmitting}
                  returnKeyType="next"
                />
              </View>
            </View>

            {/* Department Selector */}
            <View style={styles.fullField}>
              <Text style={styles.label}>Department *</Text>
              <View style={styles.pillContainer}>
                {DEPARTMENTS.map((dept) => {
                  const isSelected = formData.department === dept;
                  return (
                    <Pressable
                      key={dept}
                      style={[
                        styles.deptPill,
                        isSelected && styles.deptPillSelected,
                      ]}
                      onPress={() => handleFieldChange('department', dept)}
                      disabled={isSubmitting}
                    >
                      <Text
                        style={[
                          styles.deptPillText,
                          isSelected && styles.deptPillTextSelected,
                        ]}
                      >
                        {dept}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>

            {/* Row: Joining Date & Status */}
            <View style={styles.row}>
              <View style={styles.col}>
                <Text style={styles.label}>Date of Joining (DD-MM-YYYY) *</Text>
                <DatePickerInput
                  value={formData.date_of_joining}
                  onChange={(date) => handleFieldChange('date_of_joining', date)}
                  error={Boolean(errors.date_of_joining)}
                  disabled={isSubmitting}
                />
                {errors.date_of_joining ? (
                  <View style={styles.errorRow}>
                    <Ionicons name="alert-circle" size={13} color={colors.danger} />
                    <Text style={styles.errorText}>{errors.date_of_joining}</Text>
                  </View>
                ) : null}
              </View>

              <View style={styles.col}>
                <Text style={styles.label}>Employment Status</Text>
                <View style={styles.statusToggleRow}>
                  <Pressable
                    style={[
                      styles.statusToggleBtn,
                      formData.employment_status === 'ACTIVE' && styles.statusActiveBtnSelected,
                    ]}
                    onPress={() => handleFieldChange('employment_status', 'ACTIVE')}
                    disabled={isSubmitting}
                  >
                    <Text
                      style={[
                        styles.statusToggleText,
                        formData.employment_status === 'ACTIVE' && styles.statusActiveTextSelected,
                      ]}
                    >
                      Active
                    </Text>
                  </Pressable>

                  <Pressable
                    style={[
                      styles.statusToggleBtn,
                      formData.employment_status === 'INACTIVE' && styles.statusInactiveBtnSelected,
                    ]}
                    onPress={() => handleFieldChange('employment_status', 'INACTIVE')}
                    disabled={isSubmitting}
                  >
                    <Text
                      style={[
                        styles.statusToggleText,
                        formData.employment_status === 'INACTIVE' && styles.statusInactiveTextSelected,
                      ]}
                    >
                      Inactive
                    </Text>
                  </Pressable>
                </View>
              </View>
            </View>
          </ScrollView>

          {/* Footer Actions */}
          <View style={styles.footer}>
            <Pressable
              style={[styles.cancelBtn, isSubmitting && { opacity: 0.6 }]}
              onPress={onClose}
              disabled={isSubmitting}
            >
              <Text style={styles.cancelBtnText}>Cancel</Text>
            </Pressable>

            <Pressable
              style={[styles.submitBtn, isSubmitting && styles.submitBtnDisabled]}
              onPress={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <View style={styles.submittingContent}>
                  <ActivityIndicator size="small" color="#FFFFFF" style={{ marginRight: 6 }} />
                  <Text style={styles.submitBtnText}>Saving...</Text>
                </View>
              ) : (
                <Text style={styles.submitBtnText}>
                  {initialEmployee ? 'Save Changes' : 'Create Employee'}
                </Text>
              )}
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
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  modalCard: {
    width: '100%',
    maxWidth: 580,
    maxHeight: '90%',
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
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
    borderRadius: 6,
  },
  formBody: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  row: {
    flexDirection: Platform.OS === 'web' ? 'row' : 'column',
    gap: 14,
    marginBottom: 14,
  },
  col: {
    flex: 1,
  },
  fullField: {
    marginBottom: 14,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: 6,
    letterSpacing: 0.3,
  },
  input: {
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 42,
    fontSize: 14,
    color: colors.textPrimary,
  },
  inputError: {
    borderColor: colors.danger,
    backgroundColor: colors.dangerBg,
  },
  errorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  errorText: {
    fontSize: 11,
    color: colors.danger,
    fontWeight: '500',
  },
  pillContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  deptPill: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 6,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  deptPillSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  deptPillText: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  deptPillTextSelected: {
    color: colors.primaryDark,
    fontWeight: '700',
  },
  statusToggleRow: {
    flexDirection: 'row',
    gap: 8,
    height: 42,
  },
  statusToggleBtn: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  statusActiveBtnSelected: {
    backgroundColor: colors.statusActiveBg,
    borderColor: colors.statusActiveBorder,
  },
  statusInactiveBtnSelected: {
    backgroundColor: colors.statusInactiveBg,
    borderColor: colors.statusInactiveBorder,
  },
  statusToggleText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textMuted,
  },
  statusActiveTextSelected: {
    color: colors.statusActiveText,
  },
  statusInactiveTextSelected: {
    color: colors.statusInactiveText,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.background,
  },
  cancelBtn: {
    paddingVertical: 9,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  submitBtn: {
    paddingVertical: 9,
    paddingHorizontal: 18,
    borderRadius: 8,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitBtnDisabled: {
    opacity: 0.65,
  },
  submittingContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  submitBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  backendErrorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.dangerBg,
    borderColor: colors.dangerBorder,
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  backendErrorText: {
    color: colors.danger,
    fontSize: 12,
    fontWeight: '500',
    flex: 1,
    lineHeight: 16,
  },
});
