import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  useWindowDimensions,
  SafeAreaView,
  ActivityIndicator,
  Pressable,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';

import { EmployeeListItem, EmployeeFormData, DashboardStats } from './src/types/employee';
import { colors } from './src/theme/colors';

import { Header } from './src/components/Header';
import { Sidebar } from './src/components/Sidebar';
import { MobileBottomNav } from './src/components/MobileBottomNav';
import { EmployeeModalForm } from './src/components/EmployeeModalForm';
import { DeactivateConfirmModal } from './src/components/DeactivateConfirmModal';
import { NotificationToast } from './src/components/NotificationToast';
import { DashboardScreen } from './src/screens/DashboardScreen';
import { EmployeeListScreen } from './src/screens/EmployeeListScreen';

import {
  getEmployees,
  getDashboardStats,
  createEmployee,
  updateEmployee,
  updateEmployeeStatus,
} from './src/services/api';

export default function App() {
  const { width } = useWindowDimensions();
  // Standard responsive breakpoint: 768px divides mobile from desktop
  const isDesktop = width >= 768;

  // Backend Data State (Connected to Python FastAPI on Port 8000)
  const [employees, setEmployees] = useState<EmployeeListItem[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalEmployees: 0,
    activeEmployees: 0,
    inactiveEmployees: 0,
    departmentsCount: 0,
  });

  // Request & Connection States
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean>(false);

  // Active Screen Navigation
  const [currentScreen, setCurrentScreen] = useState<'dashboard' | 'employees'>('dashboard');
  const [directoryRefreshKey, setDirectoryRefreshKey] = useState(0);

  // Modal State for Add / Edit
  const [modalVisible, setModalVisible] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<EmployeeListItem | null>(null);
  const [modalBackendError, setModalBackendError] = useState<string | null>(null);
  const [isSubmittingModal, setIsSubmittingModal] = useState<boolean>(false);

  // Deactivation Confirmation State
  const [deactivatingEmployee, setDeactivatingEmployee] = useState<EmployeeListItem | null>(null);
  const [isDeactivating, setIsDeactivating] = useState<boolean>(false);

  // Toast Notification State
  const [notification, setNotification] = useState<{
    id: number;
    message: string;
    type: 'success' | 'error';
  } | null>(null);

  const showNotification = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setNotification({
      id: Date.now(),
      message,
      type,
    });
  }, []);

  const dismissNotification = useCallback(() => {
    setNotification(null);
  }, []);

  // Load live data from FastAPI backend
  const loadData = useCallback(async () => {
    setIsSyncing(true);
    try {
      const [fetchedEmployees, fetchedStats] = await Promise.all([
        getEmployees({ limit: 100, sortBy: 'created_at', sortOrder: 'desc' }),
        getDashboardStats(),
      ]);
      setEmployees(fetchedEmployees.items);
      setStats(fetchedStats);
      setDirectoryRefreshKey((current) => current + 1);
      setBackendConnected(true);
      setApiError(null);
    } catch (err: any) {
      setBackendConnected(false);
      setApiError(err.message || 'Unable to connect to FastAPI backend at http://127.0.0.1:8000.');
    } finally {
      setIsLoading(false);
      setIsSyncing(false);
    }
  }, []);

  // Fetch initial data on application mount
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Open Add Employee Modal
  const handleOpenAddModal = () => {
    setEditingEmployee(null);
    setModalBackendError(null);
    setModalVisible(true);
  };

  // Open Edit Employee Modal
  const handleEdit = (employee: EmployeeListItem) => {
    setEditingEmployee(employee);
    setModalBackendError(null);
    setModalVisible(true);
  };

  // Execute status update (Active <-> Inactive) via PATCH /api/employees/{id}/status
  const executeStatusChange = async (id: string, newStatus: 'ACTIVE' | 'INACTIVE') => {
    setIsSyncing(true);
    try {
      await updateEmployeeStatus(id, newStatus);
      await loadData();
    } catch (err: any) {
      setApiError(`Failed to update status: ${err.message}`);
      throw err;
    } finally {
      setIsSyncing(false);
    }
  };

  // Toggle employment status: Intercept deactivation to require confirmation; allow instant reactivation
  const handleToggleStatus = async (id: string) => {
    const target = employees.find((e) => e.id === id);
    if (!target) return;

    if (target.employment_status === 'ACTIVE') {
      // Require explicit confirmation before soft-deactivating
      setDeactivatingEmployee(target);
    } else {
      // Reactivate directly without redundant confirmation
      try {
        await executeStatusChange(id, 'ACTIVE');
        showNotification('Employee reactivated successfully.', 'success');
      } catch (err: any) {
        showNotification(err.message || 'Failed to reactivate employee.', 'error');
      }
    }
  };

  // Confirm deactivation from modal
  const handleConfirmDeactivate = async () => {
    if (!deactivatingEmployee) return;
    setIsDeactivating(true);
    try {
      await executeStatusChange(deactivatingEmployee.id, 'INACTIVE');
      setDeactivatingEmployee(null);
      showNotification('Employee deactivated successfully.', 'success');
    } catch (err: any) {
      showNotification(err.message || 'Failed to deactivate employee.', 'error');
    } finally {
      setIsDeactivating(false);
    }
  };

  // Cancel deactivation
  const handleCancelDeactivate = () => {
    setDeactivatingEmployee(null);
  };

  // Create or Update Employee via FastAPI endpoints
  const handleSubmitEmployee = async (data: EmployeeFormData) => {
    setIsSubmittingModal(true);
    setModalBackendError(null);

    const isEditing = Boolean(editingEmployee);
    try {
      if (editingEmployee) {
        // PUT /api/employees/{id}
        await updateEmployee(editingEmployee.id, data);
      } else {
        // POST /api/employees
        await createEmployee(data);
      }
      // Success: close modal and refresh live database state
      setModalVisible(false);
      await loadData();
      showNotification(
        isEditing ? 'Employee updated successfully.' : 'Employee created successfully.',
        'success'
      );
    } catch (err: any) {
      // Keep modal open and display specific backend validation error
      const errorMsg = err.message || 'Operation failed. Please check your inputs.';
      setModalBackendError(errorMsg);
      showNotification(errorMsg, 'error');
    } finally {
      setIsSubmittingModal(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />

      <View style={[styles.appContainer, isDesktop ? styles.desktopLayout : styles.mobileLayout]}>
        {/* Desktop Sidebar (renders on desktop viewports) */}
        {isDesktop && (
          <Sidebar
            currentScreen={currentScreen}
            onNavigate={setCurrentScreen}
            onOpenAddModal={handleOpenAddModal}
          />
        )}

        {/* Main Workspace Area */}
        <View style={styles.mainContent}>
          <Header
            currentScreen={currentScreen}
            isDesktop={isDesktop}
            backendConnected={backendConnected}
            isSyncing={isSyncing}
            onRefresh={loadData}
          />

          {/* Network/API Error Banner */}
          {apiError ? (
            <View style={styles.errorBanner}>
              <Ionicons name="cloud-offline" size={20} color={colors.danger} />
              <View style={styles.errorTextContainer}>
                <Text style={styles.errorBannerTitle}>Backend Communication Notice</Text>
                <Text style={styles.errorBannerMessage}>{apiError}</Text>
              </View>
              <Pressable style={styles.retryButton} onPress={loadData}>
                <Ionicons name="refresh" size={14} color="#FFFFFF" />
                <Text style={styles.retryButtonText}>Retry</Text>
              </Pressable>
            </View>
          ) : null}

          {/* Initial Loading Indicator */}
          {isLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={styles.loadingText}>Connecting to Employee Management API...</Text>
            </View>
          ) : (
            <View style={styles.screenWrapper}>
              {currentScreen === 'dashboard' ? (
                <DashboardScreen
                  employees={employees}
                  stats={stats}
                  isDesktop={isDesktop}
                  onNavigateToEmployees={() => setCurrentScreen('employees')}
                  onOpenAddModal={handleOpenAddModal}
                />
              ) : (
                <EmployeeListScreen
                  isDesktop={isDesktop}
                  refreshKey={directoryRefreshKey}
                  onEdit={handleEdit}
                  onToggleStatus={handleToggleStatus}
                  onOpenAddModal={handleOpenAddModal}
                />
              )}
            </View>
          )}
        </View>

        {/* Mobile Bottom Navigation (renders on mobile viewports) */}
        {!isDesktop && (
          <MobileBottomNav
            currentScreen={currentScreen}
            onNavigate={setCurrentScreen}
            onOpenAddModal={handleOpenAddModal}
          />
        )}
      </View>

      {/* Add / Edit Employee Modal */}
      <EmployeeModalForm
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        onSubmit={handleSubmitEmployee}
        initialEmployee={editingEmployee}
        existingEmployees={employees}
        backendError={modalBackendError}
        isSubmitting={isSubmittingModal}
      />

      {/* Employee Deactivation Confirmation Modal */}
      <DeactivateConfirmModal
        visible={Boolean(deactivatingEmployee)}
        employee={deactivatingEmployee}
        onCancel={handleCancelDeactivate}
        onConfirm={handleConfirmDeactivate}
        isSubmitting={isDeactivating}
      />

      {/* Toast Notification Container */}
      {notification && (
        <View
          style={[
            styles.toastContainer,
            isDesktop ? styles.toastDesktop : styles.toastMobile,
          ]}
          pointerEvents="box-none"
        >
          <NotificationToast
            key={notification.id}
            message={notification.message}
            type={notification.type}
            onDismiss={dismissNotification}
          />
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  toastContainer: {
    position: 'absolute',
    zIndex: 9999,
  },
  toastDesktop: {
    top: 20,
    right: 24,
  },
  toastMobile: {
    top: 14,
    left: 16,
    right: 16,
    alignItems: 'center',
  },
  appContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  desktopLayout: {
    flexDirection: 'row',
  },
  mobileLayout: {
    flexDirection: 'column',
  },
  mainContent: {
    flex: 1,
    flexDirection: 'column',
    backgroundColor: colors.background,
  },
  screenWrapper: {
    flex: 1,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.dangerBg,
    borderColor: colors.dangerBorder,
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginHorizontal: 24,
    marginTop: 16,
    borderRadius: 8,
    gap: 12,
  },
  errorTextContainer: {
    flex: 1,
  },
  errorBannerTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.danger,
  },
  errorBannerMessage: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colors.danger,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
});
