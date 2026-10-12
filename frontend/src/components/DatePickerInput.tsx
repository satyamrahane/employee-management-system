import React from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { formatDateDDMMYYYY } from '../utils/date';

interface DatePickerInputProps {
  value: string;
  onChange: (date: string) => void;
  error?: boolean;
  disabled?: boolean;
}

export const DatePickerInput: React.FC<DatePickerInputProps> = ({
  value,
  onChange,
  error = false,
  disabled = false,
}) => {
  const formattedDisplay = formatDateDDMMYYYY(value);

  return (
    <View
      style={[
        styles.container,
        error && styles.containerError,
        disabled && styles.containerDisabled,
      ]}
    >
      <Ionicons
        name="calendar-outline"
        size={18}
        color={error ? colors.danger : colors.primary}
        style={styles.calendarIcon}
      />

      <View style={styles.pickerContent}>
        {Platform.OS === 'web' ? (
          // Standard Web Native Date Picker with calendar popup & keyboard navigation
          React.createElement('input', {
            type: 'date',
            value: value || '',
            min: '1990-01-01',
            max: '2099-12-31',
            disabled: disabled,
            onChange: (e: any) => {
              const nextValue = e?.target?.value;
              if (nextValue) {
                onChange(nextValue);
              }
            },
            style: {
              flex: 1,
              border: 'none',
              outline: 'none',
              backgroundColor: 'transparent',
              fontSize: '14px',
              color: colors.textPrimary,
              fontFamily: 'inherit',
              cursor: disabled ? 'not-allowed' : 'pointer',
              padding: '4px 6px',
              minWidth: '130px',
            },
          })
        ) : (
          <TextInput
            style={styles.nativeInput}
            value={value}
            onChangeText={onChange}
            placeholder="YYYY-MM-DD"
            placeholderTextColor={colors.textMuted}
            editable={!disabled}
          />
        )}

        {formattedDisplay ? (
          <View style={styles.formatBadge}>
            <Text style={styles.formatBadgeText}>{formattedDisplay}</Text>
          </View>
        ) : null}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 42,
  },
  containerError: {
    borderColor: colors.danger,
    backgroundColor: colors.dangerBg,
  },
  containerDisabled: {
    opacity: 0.6,
  },
  calendarIcon: {
    marginRight: 6,
  },
  pickerContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  nativeInput: {
    flex: 1,
    fontSize: 14,
    color: colors.textPrimary,
    paddingVertical: 6,
  },
  formatBadge: {
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginLeft: 8,
  },
  formatBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primaryDark,
    letterSpacing: 0.3,
  },
});
