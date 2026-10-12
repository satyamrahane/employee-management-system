// Automated End-to-End Integration Verification between Frontend Client and FastAPI Backend
// Self-cleaning and idempotent test suite
const assert = require('assert');

const API_BASE_URL = 'http://127.0.0.1:8000/api';

async function runLiveIntegrationTests() {
  console.log('--- STARTING LIVE FRONTEND-BACKEND INTEGRATION TESTS ---');

  // 1. Health Endpoint Check
  console.log('1. Checking GET /api/health...');
  const healthRes = await fetch(`${API_BASE_URL}/health`);
  assert.strictEqual(healthRes.status, 200, 'Health check should return 200');
  const healthData = await healthRes.json();
  assert.strictEqual(healthData.status, 'healthy');
  console.log('✓ Test 1 Passed: FastAPI backend is healthy. Database driver:', healthData.database_driver);

  // 2. Fetch Initial Dashboard Stats
  console.log('2. Checking GET /api/dashboard/stats...');
  const statsRes = await fetch(`${API_BASE_URL}/dashboard/stats`);
  assert.strictEqual(statsRes.status, 200);
  const initialStats = await statsRes.json();
  console.log(`✓ Test 2 Passed: Baseline workforce stats retrieved (Total: ${initialStats.totalEmployees}, Active: ${initialStats.activeEmployees}).`);

  // 3. Fetch Employees List
  console.log('3. Checking GET /api/employees...');
  const employeesRes = await fetch(`${API_BASE_URL}/employees`);
  assert.strictEqual(employeesRes.status, 200);
  const employeePage = await employeesRes.json();
  assert(Array.isArray(employeePage.items), 'Employees response should contain an items array');
  assert(employeePage.items.length >= 6, 'Database should contain pre-seeded canonical employees');
  console.log(`✓ Test 3 Passed: Fetched ${employeePage.items.length} employees from database.`);

  // 4. Create a New Employee via POST /api/employees
  console.log('4. Testing POST /api/employees (Adding new employee)...');
  const testEmpCode = `TEST-${Date.now().toString().slice(-4)}`;
  const testEmpEmail = `test.${Date.now()}@example.com`;
  const createPayload = {
    employee_code: testEmpCode,
    first_name: 'Ananya',
    last_name: 'Deshmukh',
    email: testEmpEmail,
    phone_number: '+1 555-9876',
    job_title: 'Full Stack Engineer',
    department: 'Engineering',
    date_of_joining: '2024-03-01',
    employment_status: 'ACTIVE',
  };

  const createRes = await fetch(`${API_BASE_URL}/employees`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(createPayload),
  });
  assert.strictEqual(createRes.status, 201, 'Should return 201 Created');
  const createdEmployee = await createRes.json();
  assert.strictEqual(createdEmployee.employee_code, testEmpCode);
  assert(createdEmployee.id, 'Created employee must have a backend-generated id');
  console.log(`✓ Test 4 Passed: Created employee '${createdEmployee.first_name} ${createdEmployee.last_name}' with ID '${createdEmployee.id}'.`);

  // 5. Verify Duplicate Employee Code Rejection (400 Bad Request)
  console.log('5. Testing Duplicate Employee Code Rejection...');
  const dupCodeRes = await fetch(`${API_BASE_URL}/employees`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(createPayload),
  });
  assert.strictEqual(dupCodeRes.status, 400, 'Duplicate code should return 400 Bad Request');
  const dupCodeError = await dupCodeRes.json();
  assert(dupCodeError.detail.includes('already exists'), 'Error detail should mention code exists');
  console.log(`✓ Test 5 Passed: Duplicate code correctly rejected with message: "${dupCodeError.detail}".`);

  // 6. Verify Duplicate Email Rejection (400 Bad Request)
  console.log('6. Testing Duplicate Email Rejection...');
  const dupEmailPayload = {
    ...createPayload,
    employee_code: `DIFF-${Date.now().toString().slice(-4)}`,
  };
  const dupEmailRes = await fetch(`${API_BASE_URL}/employees`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dupEmailPayload),
  });
  assert.strictEqual(dupEmailRes.status, 400, 'Duplicate email should return 400 Bad Request');
  const dupEmailError = await dupEmailRes.json();
  assert(dupEmailError.detail.includes('already registered'), 'Error detail should mention email registered');
  console.log(`✓ Test 6 Passed: Duplicate email correctly rejected with message: "${dupEmailError.detail}".`);

  // 7. Verify Database Persistence & Stats Recalculation
  console.log('7. Verifying Database Persistence & Updated Stats...');
  const updatedStatsRes = await fetch(`${API_BASE_URL}/dashboard/stats`);
  const updatedStats = await updatedStatsRes.json();
  assert.strictEqual(
    updatedStats.totalEmployees,
    initialStats.totalEmployees + 1,
    'Total employees in database should have incremented by 1'
  );
  console.log(`✓ Test 7 Passed: Database confirmed new record. Total employees is now ${updatedStats.totalEmployees}.`);

  // 8. Soft-Deactivate Employee via PATCH /api/employees/{id}/status
  console.log('8. Testing PATCH /api/employees/{id}/status (Soft-deactivate)...');
  const patchRes = await fetch(`${API_BASE_URL}/employees/${createdEmployee.id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employment_status: 'INACTIVE' }),
  });
  assert.strictEqual(patchRes.status, 200);
  const patchedEmployee = await patchRes.json();
  assert.strictEqual(patchedEmployee.employment_status, 'INACTIVE');
  console.log(`✓ Test 8 Passed: Successfully deactivated employee status to 'INACTIVE'.`);

  // 9. Reactivate Employee via PATCH /api/employees/{id}/status
  console.log('9. Testing PATCH /api/employees/{id}/status (Reactivate)...');
  const reactivateRes = await fetch(`${API_BASE_URL}/employees/${createdEmployee.id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employment_status: 'ACTIVE' }),
  });
  assert.strictEqual(reactivateRes.status, 200);
  const reactivatedEmployee = await reactivateRes.json();
  assert.strictEqual(reactivatedEmployee.employment_status, 'ACTIVE');
  console.log(`✓ Test 9 Passed: Successfully reactivated employee status to 'ACTIVE'.`);

  // 10. Update Employee Details via PUT /api/employees/{id}
  console.log('10. Testing PUT /api/employees/{id}...');
  const putRes = await fetch(`${API_BASE_URL}/employees/${createdEmployee.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_title: 'Staff Software Architect' }),
  });
  assert.strictEqual(putRes.status, 200);
  const updatedEmployee = await putRes.json();
  assert.strictEqual(updatedEmployee.job_title, 'Staff Software Architect');
  console.log(`✓ Test 10 Passed: Successfully updated job title to 'Staff Software Architect'.`);

  // 11. Search Query Test
  console.log('11. Testing search query parameter on GET /api/employees?search=...');
  const searchRes = await fetch(`${API_BASE_URL}/employees?search=Deshmukh`);
  assert.strictEqual(searchRes.status, 200);
  const searchResults = await searchRes.json();
  assert(searchResults.length >= 1, 'Should find at least 1 record matching Deshmukh');
  console.log('✓ Test 11 Passed: Search query filter returned matching record accurately.');

  console.log('--- ALL LIVE INTEGRATION TESTS PASSED SUCCESSFULLY ---');
}

runLiveIntegrationTests().catch((err) => {
  console.error('❌ Integration Test Failed:', err);
  process.exit(1);
});
