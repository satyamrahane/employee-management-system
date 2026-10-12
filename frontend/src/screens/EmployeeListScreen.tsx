import React, { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import {
  Department,
  EmployeeListItem,
  EmployeePage,
  SortDirection,
  SortField,
} from '../types/employee';
import { EmployeeTableDesktop } from '../components/EmployeeTableDesktop';
import { EmployeeCardMobile } from '../components/EmployeeCardMobile';
import { colors } from '../theme/colors';
import { getEmployees } from '../services/api';

const PAGE_SIZE = 25;
const EMPTY_PAGE: EmployeePage = {
  items: [],
  total: 0,
  skip: 0,
  limit: PAGE_SIZE,
  page: 1,
  total_pages: 0,
  has_previous: false,
  has_next: false,
};

interface EmployeeListScreenProps {
  isDesktop: boolean;
  refreshKey: number;
  onEdit: (employee: EmployeeListItem) => void;
  onToggleStatus: (id: string) => void;
  onOpenAddModal: () => void;
}

const DEPARTMENTS: ('All' | Department)[] = [
  'All',
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

export const EmployeeListScreen: React.FC<EmployeeListScreenProps> = ({
  isDesktop,
  refreshKey,
  onEdit,
  onToggleStatus,
  onOpenAddModal,
}) => {
  const [pageData, setPageData] = useState<EmployeePage>(EMPTY_PAGE);
  const [skip, setSkip] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);
  const requestIdRef = useRef(0);

  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState<'All' | Department>('All');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');

  // Sorting States
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // Detect whether any non-default filters or searches are active
  const hasActiveFilters = Boolean(
    searchQuery.trim().length > 0 ||
    selectedDept !== 'All' ||
    statusFilter !== 'ALL'
  );

  // Reset all filters and search query back to default
  const handleResetFilters = () => {
    setSearchQuery('');
    setDebouncedSearch('');
    setSelectedDept('All');
    setStatusFilter('ALL');
    setSkip(0);
  };

  // Toggle or switch column sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
    setSkip(0);
  };

  useEffect(() => {
    const timeout = setTimeout(() => setDebouncedSearch(searchQuery.trim()), 300);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  useEffect(() => {
    const controller = new AbortController();
    const requestId = ++requestIdRef.current;
    setIsLoading(true);
    setLoadError(null);

    getEmployees(
      {
        skip,
        limit: PAGE_SIZE,
        search: debouncedSearch,
        department: selectedDept,
        status: statusFilter,
        sortBy: sortField,
        sortOrder: sortDirection,
      },
      controller.signal,
    )
      .then((result) => {
        if (requestId !== requestIdRef.current) return;
        if (result.total === 0 && skip > 0) {
          setSkip(0);
          return;
        }
        if (result.total > 0 && skip >= result.total) {
          setSkip((result.total_pages - 1) * PAGE_SIZE);
          return;
        }
        setPageData(result);
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setLoadError(error instanceof Error ? error.message : 'Unable to load employees.');
      })
      .finally(() => {
        if (!controller.signal.aborted && requestId === requestIdRef.current) {
          setIsLoading(false);
        }
      });

    return () => controller.abort();
  }, [
    debouncedSearch,
    selectedDept,
    statusFilter,
    skip,
    sortField,
    sortDirection,
    refreshKey,
    retryKey,
  ]);

  const employees = pageData.items;
  const shownFrom = pageData.total === 0 ? 0 : skip + 1;
  const shownTo = Math.min(skip + employees.length, pageData.total);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Top Filter and Controls Card */}
      <View style={styles.topControlCard}>
        {/* Search Input and Add Action */}
        <View style={styles.searchAndActionRow}>
          <View style={styles.searchContainer}>
            <Ionicons name="search" size={18} color={colors.textMuted} />
            <TextInput
              style={styles.searchInput}
              placeholder="Search by name, email, employee code, or title..."
              placeholderTextColor={colors.textMuted}
              value={searchQuery}
              onChangeText={(value) => {
                setSearchQuery(value);
                setSkip(0);
              }}
            />
            {searchQuery.length > 0 && (
              <Pressable
                onPress={() => setSearchQuery('')}
                accessibilityRole="button"
                accessibilityLabel="Clear search text"
              >
                <Ionicons name="close-circle" size={18} color={colors.textMuted} />
              </Pressable>
            )}
          </View>

          {isDesktop && (
            <Pressable style={styles.addButton} onPress={onOpenAddModal}>
              <Ionicons name="add" size={18} color="#FFFFFF" />
              <Text style={styles.addButtonText}>Add Employee</Text>
            </Pressable>
          )}
        </View>

        {/* Filter Row: Department Pills & Status Toggle */}
        <View style={styles.filtersSection}>
          {/* Department Pills */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.deptScrollContainer}
          >
            {DEPARTMENTS.map((dept) => {
              const isSelected = selectedDept === dept;
              return (
                <Pressable
                  key={dept}
                  style={[
                    styles.deptPill,
                    isSelected && styles.deptPillSelected,
                  ]}
                  onPress={() => {
                    setSelectedDept(dept);
                    setSkip(0);
                  }}
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
          </ScrollView>

          {/* Status Filter */}
          <View style={styles.statusFilterGroup}>
            {(['ALL', 'ACTIVE', 'INACTIVE'] as const).map((status) => {
              const isSelected = statusFilter === status;
              return (
                <Pressable
                  key={status}
                  style={[
                    styles.statusPill,
                    isSelected && styles.statusPillSelected,
                  ]}
                  onPress={() => {
                    setStatusFilter(status);
                    setSkip(0);
                  }}
                >
                  <Text
                    style={[
                      styles.statusPillText,
                      isSelected && styles.statusPillTextSelected,
                    ]}
                  >
                    {status === 'ALL' ? 'All Status' : status}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        {/* Mobile Sort Bar (renders on mobile viewports for clean sorting) */}
        {!isDesktop && (
          <View style={styles.mobileSortSection}>
            <Text style={styles.mobileSortLabel}>SORT BY:</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.mobileSortScroll}
            >
              {[
                { field: 'name' as const, label: 'Name' },
                { field: 'code' as const, label: 'Code' },
                { field: 'department' as const, label: 'Dept' },
                { field: 'date_of_joining' as const, label: 'Join Date' },
                { field: 'status' as const, label: 'Status' },
              ].map(({ field, label }) => {
                const isSelected = sortField === field;
                return (
                  <Pressable
                    key={field}
                    style={[styles.sortPill, isSelected && styles.sortPillSelected]}
                    onPress={() => handleSort(field)}
                  >
                    <Text style={[styles.sortPillText, isSelected && styles.sortPillTextSelected]}>
                      {label}
                    </Text>
                    {isSelected && (
                      <Ionicons
                        name={sortDirection === 'asc' ? 'arrow-up' : 'arrow-down'}
                        size={11}
                        color={colors.primaryDark}
                        style={{ marginLeft: 3 }}
                      />
                    )}
                  </Pressable>
                );
              })}
            </ScrollView>
          </View>
        )}

        {/* Results Counter & Reset Filters Row */}
        <View style={styles.resultsBar}>
          <Text style={styles.resultsCountText}>
            Showing <Text style={{ fontWeight: '700', color: colors.textPrimary }}>{shownFrom}-{shownTo}</Text> of {pageData.total} employees
          </Text>

          {hasActiveFilters && (
            <Pressable style={styles.resetFiltersBtn} onPress={handleResetFilters}>
              <Ionicons name="refresh-outline" size={13} color={colors.primary} />
              <Text style={styles.resetFiltersText}>Reset Filters</Text>
            </Pressable>
          )}
        </View>
      </View>

      {/* Directory Content: Desktop Table or Mobile Cards */}
      {loadError ? (
        <View style={styles.requestState}>
          <Text style={styles.requestStateText}>{loadError}</Text>
          <Pressable style={styles.retryButton} onPress={() => setRetryKey((value) => value + 1)}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </Pressable>
        </View>
      ) : isLoading ? (
        <View style={styles.requestState}>
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={styles.requestStateText}>Loading employees...</Text>
        </View>
      ) : isDesktop ? (
        <EmployeeTableDesktop
          employees={employees}
          onEdit={onEdit}
          onToggleStatus={onToggleStatus}
          sortField={sortField}
          sortDirection={sortDirection}
          onSort={handleSort}
          searchQuery={searchQuery}
          hasActiveFilters={hasActiveFilters}
          onResetFilters={handleResetFilters}
          onOpenAddModal={onOpenAddModal}
          totalEmployeesCount={pageData.total}
        />
      ) : (
        <View style={styles.mobileList}>
          {employees.length === 0 ? (
            <View style={styles.emptyMobile}>
              <View style={styles.emptyMobileIconWrapper}>
                <Ionicons
                  name={
                    pageData.total === 0
                      ? 'people-outline'
                      : searchQuery.trim()
                      ? 'search-outline'
                      : 'filter-outline'
                  }
                  size={36}
                  color={colors.textMuted}
                />
              </View>

              <Text style={styles.emptyMobileTitle}>
                {pageData.total === 0
                  ? 'No Employees in Directory'
                  : searchQuery.trim()
                  ? 'No Matching Results'
                  : 'No Filter Matches'}
              </Text>

              <Text style={styles.emptyMobileText}>
                {pageData.total === 0
                  ? 'There are currently no employee records. Add your first employee to get started.'
                  : searchQuery.trim()
                  ? `No employees match "${searchQuery}".`
                  : 'No employees match the selected department or status filters.'}
              </Text>

              {hasActiveFilters ? (
                <Pressable style={styles.emptyActionBtn} onPress={handleResetFilters}>
                  <Ionicons name="refresh-outline" size={14} color={colors.primary} />
                  <Text style={styles.emptyActionBtnText}>Reset Search & Filters</Text>
                </Pressable>
              ) : pageData.total === 0 ? (
                <Pressable style={styles.emptyAddBtn} onPress={onOpenAddModal}>
                  <Ionicons name="add" size={16} color="#FFFFFF" />
                  <Text style={styles.emptyAddBtnText}>Add Employee</Text>
                </Pressable>
              ) : null}
            </View>
          ) : (
            employees.map((emp) => (
              <EmployeeCardMobile
                key={emp.id}
                employee={emp}
                onEdit={onEdit}
                onToggleStatus={onToggleStatus}
              />
            ))
          )}
        </View>
      )}

      <View style={styles.paginationBar}>
        <Pressable
          style={[styles.paginationButton, (!pageData.has_previous || isLoading) && styles.paginationButtonDisabled]}
          disabled={!pageData.has_previous || isLoading}
          onPress={() => setSkip((value) => Math.max(0, value - PAGE_SIZE))}
          accessibilityRole="button"
          accessibilityLabel="Previous employee page"
        >
          <Ionicons name="chevron-back" size={16} color={colors.primaryDark} />
          <Text style={styles.paginationButtonText}>Previous</Text>
        </Pressable>
        <Text style={styles.paginationPageText}>
          {pageData.total_pages === 0 ? 'Page 0 of 0' : `Page ${pageData.page} of ${pageData.total_pages}`}
        </Text>
        <Pressable
          style={[styles.paginationButton, (!pageData.has_next || isLoading) && styles.paginationButtonDisabled]}
          disabled={!pageData.has_next || isLoading}
          onPress={() => setSkip((value) => value + PAGE_SIZE)}
          accessibilityRole="button"
          accessibilityLabel="Next employee page"
        >
          <Text style={styles.paginationButtonText}>Next</Text>
          <Ionicons name="chevron-forward" size={16} color={colors.primaryDark} />
        </Pressable>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  requestState: {
    minHeight: 180,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 24,
  },
  requestStateText: {
    color: colors.textSecondary,
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 6,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  paginationBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    paddingVertical: 16,
  },
  paginationButton: {
    minHeight: 40,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 6,
    backgroundColor: colors.surface,
  },
  paginationButtonDisabled: {
    opacity: 0.45,
  },
  paginationButtonText: {
    color: colors.primaryDark,
    fontSize: 13,
    fontWeight: '600',
  },
  paginationPageText: {
    flexShrink: 1,
    color: colors.textSecondary,
    fontSize: 13,
    textAlign: 'center',
  },
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 24,
  },
  topControlCard: {
    backgroundColor: colors.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 16,
    marginBottom: 20,
    gap: 14,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  searchAndActionRow: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  searchContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: colors.textPrimary,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    gap: 6,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 13,
  },
  filtersSection: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  deptScrollContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  deptPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
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
  statusFilterGroup: {
    flexDirection: 'row',
    backgroundColor: colors.background,
    padding: 3,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statusPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  statusPillSelected: {
    backgroundColor: colors.surface,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
    elevation: 1,
  },
  statusPillText: {
    fontSize: 11,
    color: colors.textMuted,
    fontWeight: '500',
  },
  statusPillTextSelected: {
    color: colors.textPrimary,
    fontWeight: '700',
  },
  mobileSortSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingTop: 4,
  },
  mobileSortLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textMuted,
    letterSpacing: 0.5,
  },
  mobileSortScroll: {
    flexDirection: 'row',
    gap: 6,
  },
  sortPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sortPillSelected: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primaryBorder,
  },
  sortPillText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  sortPillTextSelected: {
    color: colors.primaryDark,
    fontWeight: '700',
  },
  resultsBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    paddingTop: 10,
  },
  resultsCountText: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  resetFiltersBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
    backgroundColor: colors.primaryLight,
  },
  resetFiltersText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  mobileList: {
    paddingBottom: 24,
  },
  emptyMobile: {
    paddingVertical: 36,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  emptyMobileIconWrapper: {
    width: 56,
    height: 56,
    borderRadius: 12,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  emptyMobileTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  emptyMobileText: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: 'center',
    lineHeight: 16,
    marginBottom: 16,
  },
  emptyActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
  },
  emptyActionBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primaryDark,
  },
  emptyAddBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    backgroundColor: colors.primary,
  },
  emptyAddBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
