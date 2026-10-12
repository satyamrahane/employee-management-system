// Verification script for Employee Management System logic
const assert = require('assert');
const { buildEmployeeListUrl } = require('../utils/employeeListRequest');

// 1. Initial Sample Data
const sampleEmployees = [
  {
    id: 'emp-1',
    employee_code: 'EMP-1001',
    first_name: 'Priya',
    last_name: 'Sharma',
    email: 'priya.sharma@example.com',
    phone_number: '+1 (555) 234-5678',
    job_title: 'Senior Software Engineer',
    department: 'Engineering',
    date_of_joining: '2023-03-15',
    employment_status: 'ACTIVE',
  },
  {
    id: 'emp-2',
    employee_code: 'EMP-1002',
    first_name: 'Marcus',
    last_name: 'Vance',
    email: 'marcus.vance@example.com',
    phone_number: '+1 (555) 345-6789',
    job_title: 'Lead Product Designer',
    department: 'Design',
    date_of_joining: '2022-08-01',
    employment_status: 'ACTIVE',
  },
  {
    id: 'emp-6',
    employee_code: 'EMP-1006',
    first_name: 'Liam',
    last_name: "O'Connor",
    email: 'liam.oconnor@example.com',
    phone_number: '+1 (555) 789-0123',
    job_title: 'Growth Marketing Manager',
    department: 'Marketing',
    date_of_joining: '2022-04-18',
    employment_status: 'INACTIVE',
  },
];

console.log('--- STARTING FRONTEND LOGIC VERIFICATION ---');

// Test 1: Stats Calculation
function computeStats(employees) {
  const totalEmployees = employees.length;
  const activeEmployees = employees.filter((e) => e.employment_status === 'ACTIVE').length;
  const inactiveEmployees = employees.filter((e) => e.employment_status === 'INACTIVE').length;
  const uniqueDepartments = new Set(employees.map((e) => e.department));
  return {
    totalEmployees,
    activeEmployees,
    inactiveEmployees,
    departmentsCount: uniqueDepartments.size,
  };
}

const stats = computeStats(sampleEmployees);
assert.strictEqual(stats.totalEmployees, 3, 'Total employees should be 3');
assert.strictEqual(stats.activeEmployees, 2, 'Active employees should be 2');
assert.strictEqual(stats.inactiveEmployees, 1, 'Inactive employees should be 1');
assert.strictEqual(stats.departmentsCount, 3, 'Unique departments should be 3');
console.log('✓ Test 1 Passed: Dashboard stats calculation is accurate.');

// Test 2: Server-side directory query parameters
const directoryUrl = new URL(buildEmployeeListUrl('http://localhost:8000/api', {
  skip: 25,
  limit: 25,
  search: '  Priya  ',
  department: 'Engineering',
  status: 'ACTIVE',
  sortBy: 'code',
  sortOrder: 'desc',
}));
assert.strictEqual(directoryUrl.pathname, '/api/employees');
assert.strictEqual(directoryUrl.searchParams.get('skip'), '25');
assert.strictEqual(directoryUrl.searchParams.get('limit'), '25');
assert.strictEqual(directoryUrl.searchParams.get('search'), 'Priya');
assert.strictEqual(directoryUrl.searchParams.get('department'), 'Engineering');
assert.strictEqual(directoryUrl.searchParams.get('status'), 'ACTIVE');
assert.strictEqual(directoryUrl.searchParams.get('sort_by'), 'employee_code');
assert.strictEqual(directoryUrl.searchParams.get('sort_order'), 'desc');

const defaultDirectoryUrl = new URL(buildEmployeeListUrl('http://localhost:8000/api', {
  department: 'All',
  status: 'ALL',
  search: '   ',
}));
assert.strictEqual(defaultDirectoryUrl.searchParams.get('skip'), '0');
assert.strictEqual(defaultDirectoryUrl.searchParams.get('limit'), '100');
assert.strictEqual(defaultDirectoryUrl.searchParams.has('search'), false);
assert.strictEqual(defaultDirectoryUrl.searchParams.has('department'), false);
assert.strictEqual(defaultDirectoryUrl.searchParams.has('status'), false);
console.log('✓ Test 2 Passed: Pagination, search, filters, and sorting are serialized for the API.');

// Test 3: Status Toggle (Soft-delete / Reactivate)
function toggleStatus(employees, id) {
  return employees.map((emp) => {
    if (emp.id === id) {
      const newStatus = emp.employment_status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
      return { ...emp, employment_status: newStatus };
    }
    return emp;
  });
}

let updatedList = toggleStatus(sampleEmployees, 'emp-1');
assert.strictEqual(updatedList.find((e) => e.id === 'emp-1').employment_status, 'INACTIVE');
const updatedStats = computeStats(updatedList);
assert.strictEqual(updatedStats.activeEmployees, 1);
assert.strictEqual(updatedStats.inactiveEmployees, 2);

updatedList = toggleStatus(updatedList, 'emp-1');
assert.strictEqual(updatedList.find((e) => e.id === 'emp-1').employment_status, 'ACTIVE');
console.log('✓ Test 3 Passed: Status toggling (deactivation/reactivation) updates list and recalculates stats.');

// Test 4: Duplicate Email & Code Validation
function validateForm(formData, existingEmployees, editingId = null) {
  const errors = {};
  if (!formData.first_name.trim()) errors.first_name = 'First name is required.';
  if (!formData.last_name.trim()) errors.last_name = 'Last name is required.';
  if (!formData.employee_code.trim()) {
    errors.employee_code = 'Employee code is required.';
  } else if (
    existingEmployees.some(
      (emp) =>
        emp.employee_code.trim().toUpperCase() === formData.employee_code.trim().toUpperCase() &&
        emp.id !== editingId
    )
  ) {
    errors.employee_code = 'An employee with this code already exists.';
  }

  if (!formData.email.trim()) {
    errors.email = 'Email address is required.';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    errors.email = 'Please enter a valid email address.';
  } else if (
    existingEmployees.some(
      (emp) =>
        emp.email.trim().toLowerCase() === formData.email.trim().toLowerCase() &&
        emp.id !== editingId
    )
  ) {
    errors.email = 'An employee with this email address already exists.';
  }

  return { isValid: Object.keys(errors).length === 0, errors };
}

// Test duplicate email rejection
const dupEmailCheck = validateForm(
  {
    first_name: 'Test',
    last_name: 'User',
    employee_code: 'EMP-9999',
    email: 'priya.sharma@example.com',
  },
  sampleEmployees
);
assert.strictEqual(dupEmailCheck.isValid, false);
assert.strictEqual(dupEmailCheck.errors.email, 'An employee with this email address already exists.');

// Test duplicate code rejection
const dupCodeCheck = validateForm(
  {
    first_name: 'Test',
    last_name: 'User',
    employee_code: 'EMP-1001',
    email: 'unique.email@example.com',
  },
  sampleEmployees
);
assert.strictEqual(dupCodeCheck.isValid, false);
assert.strictEqual(dupCodeCheck.errors.employee_code, 'An employee with this code already exists.');

// Test valid submission
const validCheck = validateForm(
  {
    first_name: 'Test',
    last_name: 'User',
    employee_code: 'EMP-9999',
    email: 'unique.email@example.com',
  },
  sampleEmployees
);
assert.strictEqual(validCheck.isValid, true);
console.log('✓ Test 4 Passed: Duplicate email and employee code prevention (FR-EMP-02) working as expected.');

// Test 5: Editing Existing Employee without Self-Conflict
const editSelfCheck = validateForm(
  {
    first_name: 'Priya',
    last_name: 'Sharma',
    employee_code: 'EMP-1001',
    email: 'priya.sharma@example.com',
  },
  sampleEmployees,
  'emp-1' // Editing self
);
assert.strictEqual(editSelfCheck.isValid, true);
console.log('✓ Test 5 Passed: Editing existing employee retains own code and email without self-collision.');

// Test 6: DD-MM-YYYY Date Formatting & Conversion Logic
function formatDateDDMMYYYY(dateStr) {
  if (!dateStr || typeof dateStr !== 'string') return '';
  const cleanStr = dateStr.includes('T') ? dateStr.split('T')[0] : dateStr.trim();
  const parts = cleanStr.split('-');
  if (parts.length === 3 && parts[0].length === 4) {
    const year = parts[0];
    const month = parts[1].padStart(2, '0');
    const day = parts[2].padStart(2, '0');
    return `${day}-${month}-${year}`;
  }
  return cleanStr;
}

function parseDDMMYYYYToISO(displayDate) {
  if (!displayDate || typeof displayDate !== 'string') return '';
  const parts = displayDate.trim().split('-');
  if (parts.length === 3 && parts[2].length === 4) {
    const day = parts[0].padStart(2, '0');
    const month = parts[1].padStart(2, '0');
    const year = parts[2];
    return `${year}-${month}-${day}`;
  }
  return displayDate.trim();
}

// Verification checks for requested examples
assert.strictEqual(formatDateDDMMYYYY('2023-03-15'), '15-03-2023', '2023-03-15 must format to 15-03-2023');
assert.strictEqual(formatDateDDMMYYYY('2026-10-10'), '10-10-2026', '2026-10-10 must format to 10-10-2026');
assert.strictEqual(formatDateDDMMYYYY('2022-08-01'), '01-08-2022', '2022-08-01 must format to 01-08-2022');
assert.strictEqual(formatDateDDMMYYYY('2021-11-05'), '05-11-2021', '2021-11-05 must format to 05-11-2021');

// Verification of reverse ISO parsing for backend submission
assert.strictEqual(parseDDMMYYYYToISO('15-03-2023'), '2023-03-15', '15-03-2023 must parse to 2023-03-15');
assert.strictEqual(parseDDMMYYYYToISO('10-10-2026'), '2026-10-10', '10-10-2026 must parse to 2026-10-10');
console.log('✓ Test 6 Passed: Date formatting and parsing accurately handles DD-MM-YYYY conversions without timezone shifts.');

console.log('--- ALL FRONTEND LOGIC CHECKS PASSED SUCCESSFULLY ---');
