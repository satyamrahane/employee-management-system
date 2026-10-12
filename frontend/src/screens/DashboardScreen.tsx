import React from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { EmployeeListItem, DashboardStats, Department } from '../types/employee';
import { StatCard } from '../components/StatCard';
import { colors } from '../theme/colors';
import { formatDateDDMMYYYY } from '../utils/date';

interface DashboardScreenProps {
  employees: EmployeeListItem[];
  stats: DashboardStats;
  isDesktop: boolean;
  onNavigateToEmployees: () => void;
  onOpenAddModal: () => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({
  employees,
  stats,
  isDesktop,
  onNavigateToEmployees,
  onOpenAddModal,
}) => {
  // Compute department breakdown
  const departmentCounts = employees.reduce((acc, emp) => {
    acc[emp.department] = (acc[emp.department] || 0) + 1;
    return acc;
  }, {} as Record<Department, number>);

  const recentEmployees = [...employees].slice(0, 4);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Welcome Banner */}
      <View style={styles.welcomeBanner}>
        <View style={styles.welcomeTextGroup}>
          <Text style={styles.welcomeTitle}>Welcome back, Administrator</Text>
          <Text style={styles.welcomeSubtitle}>
            Here is your organizational workforce summary and employee health metrics.
          </Text>
        </View>
        <Pressable style={styles.bannerAddButton} onPress={onOpenAddModal}>
          <Ionicons name="person-add" size={16} color="#FFFFFF" />
          <Text style={styles.bannerAddButtonText}>Add New Employee</Text>
        </Pressable>
      </View>

      {/* Stats Cards Grid */}
      <View style={styles.statsGrid}>
        <StatCard
          title="Total Staff"
          value={stats.totalEmployees}
          iconName="people"
          accentColor={colors.primary}
          subtitle="All recorded employees"
        />
        <StatCard
          title="Active Personnel"
          value={stats.activeEmployees}
          iconName="checkmark-circle"
          accentColor={colors.success}
          subtitle={`${Math.round((stats.activeEmployees / (stats.totalEmployees || 1)) * 100)}% of workforce`}
        />
        <StatCard
          title="Inactive Records"
          value={stats.inactiveEmployees}
          iconName="pause-circle"
          accentColor={colors.warning}
          subtitle="Soft-deleted / on leave"
        />
        <StatCard
          title="Departments"
          value={stats.departmentsCount}
          iconName="business"
          accentColor={colors.accent}
          subtitle="Active divisions"
        />
      </View>

      {/* Main Two-Column Layout on Desktop, Stacked on Mobile */}
      <View style={[styles.dashboardSections, isDesktop && styles.dashboardSectionsDesktop]}>
        {/* Department Distribution */}
        <View style={[styles.cardSection, isDesktop && { flex: 1.2 }]}>
          <View style={styles.sectionHeader}>
            <View>
              <Text style={styles.sectionTitle}>Department Headcount</Text>
              <Text style={styles.sectionSubtitle}>Distribution of employees by division</Text>
            </View>
            <Ionicons name="pie-chart-outline" size={20} color={colors.textMuted} />
          </View>

          <View style={styles.deptList}>
            {Object.entries(departmentCounts).map(([dept, count]) => {
              const percentage = Math.round((count / (employees.length || 1)) * 100);
              return (
                <View key={dept} style={styles.deptRow}>
                  <View style={styles.deptInfo}>
                    <Text style={styles.deptName}>{dept}</Text>
                    <Text style={styles.deptCount}>{count} {count === 1 ? 'member' : 'members'} ({percentage}%)</Text>
                  </View>
                  <View style={styles.progressBarBg}>
                    <View style={[styles.progressBarFill, { width: `${percentage}%` }]} />
                  </View>
                </View>
              );
            })}
          </View>
        </View>

        {/* Recent Additions Card */}
        <View style={[styles.cardSection, isDesktop && { flex: 1 }]}>
          <View style={styles.sectionHeader}>
            <View>
              <Text style={styles.sectionTitle}>Recent Employees</Text>
              <Text style={styles.sectionSubtitle}>Latest additions to the company</Text>
            </View>
            <Pressable onPress={onNavigateToEmployees}>
              <Text style={styles.viewAllLink}>View All</Text>
            </Pressable>
          </View>

          <View style={styles.recentList}>
            {recentEmployees.map((emp) => {
              const initials = `${emp.first_name[0] || ''}${emp.last_name[0] || ''}`.toUpperCase();
              const isActive = emp.employment_status === 'ACTIVE';
              return (
                <View key={emp.id} style={styles.recentItem}>
                  <View style={styles.recentAvatar}>
                    <Text style={styles.recentAvatarText}>{initials}</Text>
                  </View>
                  <View style={styles.recentInfo}>
                    <Text style={styles.recentName}>{emp.first_name} {emp.last_name}</Text>
                    <View style={styles.recentRoleRow}>
                      <View
                        style={[
                          styles.statusDotSmall,
                          { backgroundColor: isActive ? colors.statusActiveText : colors.statusInactiveText },
                        ]}
                      />
                      <Text style={styles.recentRole}>{emp.job_title} • {emp.department}</Text>
                    </View>
                  </View>
                  <Text style={styles.recentDate}>{formatDateDDMMYYYY(emp.date_of_joining)}</Text>
                </View>
              );
            })}
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 24,
  },
  welcomeBanner: {
    backgroundColor: colors.surface,
    borderRadius: 10,
    borderLeftWidth: 4,
    borderLeftColor: colors.primary,
    padding: 18,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 16,
    marginBottom: 16,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  welcomeTextGroup: {
    flex: 1,
    minWidth: 260,
  },
  welcomeTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  welcomeSubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
  },
  bannerAddButton: {
    backgroundColor: colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  bannerAddButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 13,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8,
    marginBottom: 16,
  },
  dashboardSections: {
    flexDirection: 'column',
    gap: 16,
  },
  dashboardSectionsDesktop: {
    flexDirection: 'row',
  },
  cardSection: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  viewAllLink: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
  },
  deptList: {
    gap: 14,
  },
  deptRow: {
    gap: 6,
  },
  deptInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  deptName: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  deptCount: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  progressBarBg: {
    height: 8,
    backgroundColor: colors.borderLight,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 4,
  },
  recentList: {
    gap: 12,
  },
  recentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 6,
  },
  recentAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recentAvatarText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.primaryDark,
  },
  recentInfo: {
    flex: 1,
  },
  recentName: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  recentRoleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 2,
  },
  statusDotSmall: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  recentRole: {
    fontSize: 12,
    color: colors.textMuted,
  },
  recentDate: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: '500',
  },
});
