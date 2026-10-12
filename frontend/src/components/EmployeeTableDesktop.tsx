import React from 'react';
import { View, Text, StyleSheet, Pressable, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { EmployeeListItem, SortField, SortDirection } from '../types/employee';
import { colors } from '../theme/colors';
import { formatDateDDMMYYYY } from '../utils/date';

interface EmployeeTableDesktopProps {
  employees: EmployeeListItem[];
  onEdit: (employee: EmployeeListItem) => void;
  onToggleStatus: (id: string) => void;
  sortField?: SortField;
  sortDirection?: SortDirection;
  onSort?: (field: SortField) => void;
  searchQuery?: string;
  hasActiveFilters?: boolean;
  onResetFilters?: () => void;
  onOpenAddModal?: () => void;
  totalEmployeesCount?: number;
}

export const EmployeeTableDesktop: React.FC<EmployeeTableDesktopProps> = ({
  employees,
  onEdit,
  onToggleStatus,
  sortField = 'name',
  sortDirection = 'asc',
  onSort,
  searchQuery = '',
  hasActiveFilters = false,
  onResetFilters,
  onOpenAddModal,
  totalEmployeesCount = 0,
}) => {
  // Render column sort indicator
  const renderSortIndicator = (field: SortField) => {
    if (sortField === field) {
      return (
        <Ionicons
          name={sortDirection === 'asc' ? 'chevron-up' : 'chevron-down'}
          size={14}
          color={colors.primary}
          style={styles.sortIndicator}
        />
      );
    }
    return (
      <Ionicons
        name="swap-vertical"
        size={12}
        color={colors.textMuted}
        style={[styles.sortIndicator, { opacity: 0.35 }]}
      />
    );
  };

  if (employees.length === 0) {
    const isTotalZero = totalEmployeesCount === 0;
    const hasSearch = searchQuery.trim().length > 0;

    return (
      <View style={styles.emptyContainer}>
        <View style={styles.emptyIconWrapper}>
          <Ionicons
            name={isTotalZero ? 'people-outline' : hasSearch ? 'search-outline' : 'filter-outline'}
            size={40}
            color={colors.textMuted}
          />
        </View>

        <Text style={styles.emptyTitle}>
          {isTotalZero
            ? 'No Employees in Directory'
            : hasSearch
            ? 'No Matching Results'
            : 'No Filter Matches'}
        </Text>

        <Text style={styles.emptySubtitle}>
          {isTotalZero
            ? 'There are currently no employee records. Add your first employee to get started.'
            : hasSearch
            ? `No employee records match "${searchQuery}". Try a different search term or reset your filters.`
            : 'No employee records match the selected department or status filters.'}
        </Text>

        {hasActiveFilters && onResetFilters ? (
          <Pressable style={styles.emptyActionBtn} onPress={onResetFilters}>
            <Ionicons name="refresh-outline" size={14} color={colors.primary} />
            <Text style={styles.emptyActionBtnText}>Reset Search & Filters</Text>
          </Pressable>
        ) : isTotalZero && onOpenAddModal ? (
          <Pressable style={styles.emptyAddBtn} onPress={onOpenAddModal}>
            <Ionicons name="add" size={16} color="#FFFFFF" />
            <Text style={styles.emptyAddBtnText}>Add New Employee</Text>
          </Pressable>
        ) : null}
      </View>
    );
  }

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.scrollWrapper}>
      <View style={styles.container}>
        {/* Table Header with Sortable Columns */}
        <View style={styles.tableHeader}>
          {/* Employee Name */}
          <Pressable
            style={({ hovered }: any) => [
              styles.headerCellPressable,
              { flex: 2.5 },
              hovered && styles.headerCellHovered,
            ]}
            onPress={() => onSort && onSort('name')}
            accessibilityRole="button"
            accessibilityLabel={`Sort by name, currently ${sortField === 'name' ? sortDirection : 'unsorted'}`}
          >
            <Text style={[styles.headerCellText, sortField === 'name' && styles.headerCellTextActive]}>
              EMPLOYEE
            </Text>
            {renderSortIndicator('name')}
          </Pressable>

          {/* Employee Code */}
          <Pressable
            style={({ hovered }: any) => [
              styles.headerCellPressable,
              { flex: 1.2 },
              hovered && styles.headerCellHovered,
            ]}
            onPress={() => onSort && onSort('code')}
            accessibilityRole="button"
            accessibilityLabel={`Sort by code, currently ${sortField === 'code' ? sortDirection : 'unsorted'}`}
          >
            <Text style={[styles.headerCellText, sortField === 'code' && styles.headerCellTextActive]}>
              CODE
            </Text>
            {renderSortIndicator('code')}
          </Pressable>

          {/* Department & Role */}
          <Pressable
            style={({ hovered }: any) => [
              styles.headerCellPressable,
              { flex: 2 },
              hovered && styles.headerCellHovered,
            ]}
            onPress={() => onSort && onSort('department')}
            accessibilityRole="button"
            accessibilityLabel={`Sort by department, currently ${sortField === 'department' ? sortDirection : 'unsorted'}`}
          >
            <Text style={[styles.headerCellText, sortField === 'department' && styles.headerCellTextActive]}>
              DEPARTMENT & ROLE
            </Text>
            {renderSortIndicator('department')}
          </Pressable>

          {/* Date of Joining */}
          <Pressable
            style={({ hovered }: any) => [
              styles.headerCellPressable,
              { flex: 1.3 },
              hovered && styles.headerCellHovered,
            ]}
            onPress={() => onSort && onSort('date_of_joining')}
            accessibilityRole="button"
            accessibilityLabel={`Sort by join date, currently ${sortField === 'date_of_joining' ? sortDirection : 'unsorted'}`}
          >
            <Text style={[styles.headerCellText, sortField === 'date_of_joining' && styles.headerCellTextActive]}>
              JOIN DATE
            </Text>
            {renderSortIndicator('date_of_joining')}
          </Pressable>

          {/* Status */}
          <Pressable
            style={({ hovered }: any) => [
              styles.headerCellPressable,
              { flex: 1 },
              hovered && styles.headerCellHovered,
            ]}
            onPress={() => onSort && onSort('status')}
            accessibilityRole="button"
            accessibilityLabel={`Sort by status, currently ${sortField === 'status' ? sortDirection : 'unsorted'}`}
          >
            <Text style={[styles.headerCellText, sortField === 'status' && styles.headerCellTextActive]}>
              STATUS
            </Text>
            {renderSortIndicator('status')}
          </Pressable>

          {/* Actions (Not sortable) */}
          <View style={[styles.headerCellStatic, { flex: 1.5 }]}>
            <Text style={[styles.headerCellText, { textAlign: 'right' }]}>ACTIONS</Text>
          </View>
        </View>

        {/* Table Rows */}
        {employees.map((emp, index) => {
          const initials = `${emp.first_name[0] || ''}${emp.last_name[0] || ''}`.toUpperCase();
          const isActive = emp.employment_status === 'ACTIVE';

          return (
            <View
              key={emp.id}
              style={[
                styles.tableRow,
                index % 2 === 1 && styles.tableRowAlt,
              ]}
            >
              {/* Employee Name & Email */}
              <View style={[styles.cell, { flex: 2.5, flexDirection: 'row', alignItems: 'center', gap: 12 }]}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>{initials}</Text>
                </View>
                <View>
                  <Text style={styles.nameText}>{emp.first_name} {emp.last_name}</Text>
                  <Text style={styles.emailText}>{emp.email}</Text>
                </View>
              </View>

              {/* Code */}
              <View style={[styles.cell, { flex: 1.2 }]}>
                <Text style={styles.codeBadge}>{emp.employee_code}</Text>
              </View>

              {/* Department & Role */}
              <View style={[styles.cell, { flex: 2 }]}>
                <Text style={styles.roleText}>{emp.job_title}</Text>
                <Text style={styles.deptText}>{emp.department}</Text>
              </View>

              {/* Join Date */}
              <View style={[styles.cell, { flex: 1.3 }]}>
                <Text style={styles.dateText}>{formatDateDDMMYYYY(emp.date_of_joining)}</Text>
              </View>

              {/* Status */}
              <View style={[styles.cell, { flex: 1 }]}>
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
                    {emp.employment_status}
                  </Text>
                </View>
              </View>

              {/* Actions */}
              <View style={[styles.cell, { flex: 1.5, flexDirection: 'row', justifyContent: 'flex-end', gap: 6 }]}>
                <Pressable
                  style={({ hovered }: any) => [
                    styles.editButton,
                    hovered && styles.editButtonHovered,
                  ]}
                  onPress={() => onEdit(emp)}
                >
                  <Ionicons name="create-outline" size={14} color={colors.primaryDark} />
                  <Text style={styles.actionEditText}>Edit</Text>
                </Pressable>

                <Pressable
                  style={({ hovered }: any) => [
                    styles.statusActionButton,
                    isActive ? styles.deactivateButton : styles.activateButton,
                    hovered && (isActive ? styles.deactivateButtonHovered : styles.activateButtonHovered),
                  ]}
                  onPress={() => onToggleStatus(emp.id)}
                >
                  <Ionicons
                    name={isActive ? 'pause-circle-outline' : 'play-circle-outline'}
                    size={14}
                    color={isActive ? colors.warningDark : colors.success}
                  />
                  <Text
                    style={[
                      styles.actionStatusText,
                      { color: isActive ? colors.warningDark : colors.success },
                    ]}
                  >
                    {isActive ? 'Deactivate' : 'Activate'}
                  </Text>
                </Pressable>
              </View>
            </View>
          );
        })}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  scrollWrapper: {
    flexGrow: 1,
  },
  container: {
    minWidth: 800,
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: colors.borderLight,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingHorizontal: 16,
  },
  headerCellPressable: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingRight: 8,
    gap: 4,
    cursor: 'pointer',
  },
  headerCellHovered: {
    opacity: 0.8,
  },
  headerCellStatic: {
    justifyContent: 'center',
    paddingVertical: 12,
  },
  headerCellText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textSecondary,
    letterSpacing: 0.5,
  },
  headerCellTextActive: {
    color: colors.primaryDark,
    fontWeight: '800',
  },
  sortIndicator: {
    marginLeft: 2,
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  tableRowAlt: {
    backgroundColor: colors.background,
  },
  cell: {
    justifyContent: 'center',
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.primaryDark,
    fontWeight: '700',
    fontSize: 13,
  },
  nameText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  emailText: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  codeBadge: {
    fontSize: 12,
    fontFamily: 'monospace',
    color: colors.textSecondary,
    backgroundColor: colors.borderLight,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  roleText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textPrimary,
  },
  deptText: {
    fontSize: 12,
    color: colors.textMuted,
  },
  dateText: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    gap: 5,
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
    fontSize: 11,
    fontWeight: '600',
  },
  statusActiveText: {
    color: colors.statusActiveText,
  },
  statusInactiveText: {
    color: colors.statusInactiveText,
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  editButtonHovered: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primaryBorder,
  },
  statusActionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
  },
  deactivateButton: {
    backgroundColor: colors.warningBg,
    borderColor: colors.warningBorder,
  },
  deactivateButtonHovered: {
    backgroundColor: '#FEF3C7',
  },
  activateButton: {
    backgroundColor: colors.successBg,
    borderColor: colors.successBorder,
  },
  activateButtonHovered: {
    backgroundColor: '#D1FAE5',
  },
  actionEditText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  actionStatusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  emptyContainer: {
    paddingVertical: 48,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    minHeight: 280,
  },
  emptyIconWrapper: {
    width: 64,
    height: 64,
    borderRadius: 12,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 6,
  },
  emptySubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    textAlign: 'center',
    maxWidth: 420,
    lineHeight: 18,
    marginBottom: 20,
  },
  emptyActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 9,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
  },
  emptyActionBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  emptyAddBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 9,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: colors.primary,
  },
  emptyAddBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
