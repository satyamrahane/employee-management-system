import {
  DashboardStats,
  Employee,
  EmployeeFormData,
  EmployeeListRequestParams,
  EmployeePage,
  EmploymentStatus,
} from '../types/employee';
import { buildEmployeeListUrl } from '../utils/employeeListRequest';

/**
 * Central API Configuration
 * The Python FastAPI backend runs locally on port 8000.
 */
export const API_BASE_URL = 'http://127.0.0.1:8000/api';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * Helper to process HTTP responses and parse backend errors into friendly messages.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        // FastAPI / Pydantic validation error list
        errorMessage = errorData.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
      }
    } catch {
      // response was not JSON
    }
    throw new ApiError(errorMessage, response.status);
  }
  return response.json();
}

/**
 * Fetch health status of the backend API
 */
export async function getHealthStatus(): Promise<{ status: string; database_driver: string }> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse(res);
}

/**
 * Fetch employees from backend with optional search and filters
 */
export async function getEmployees(
  params: EmployeeListRequestParams = {},
  signal?: AbortSignal,
): Promise<EmployeePage> {
  const url = buildEmployeeListUrl(API_BASE_URL, params);
  const res = await fetch(url, {
    headers: { 'Accept': 'application/json' },
    signal,
  });
  return handleResponse<EmployeePage>(res);
}

/**
 * Fetch single employee by ID
 */
export async function getEmployeeById(id: string): Promise<Employee> {
  const res = await fetch(`${API_BASE_URL}/employees/${id}`, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<Employee>(res);
}

/**
 * Fetch live dashboard workforce statistics
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE_URL}/dashboard/stats`, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<DashboardStats>(res);
}

/**
 * Create a new employee record (POST /api/employees)
 */
export async function createEmployee(data: EmployeeFormData): Promise<Employee> {
  const res = await fetch(`${API_BASE_URL}/employees`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse<Employee>(res);
}

/**
 * Update an existing employee record (PUT /api/employees/{id})
 */
export async function updateEmployee(id: string, data: Partial<EmployeeFormData>): Promise<Employee> {
  const res = await fetch(`${API_BASE_URL}/employees/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return handleResponse<Employee>(res);
}

/**
 * Toggle or update an employee status (PATCH /api/employees/{id}/status)
 */
export async function updateEmployeeStatus(id: string, newStatus: EmploymentStatus): Promise<Employee> {
  const res = await fetch(`${API_BASE_URL}/employees/${id}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ employment_status: newStatus }),
  });
  return handleResponse<Employee>(res);
}
