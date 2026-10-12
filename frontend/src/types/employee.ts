export type EmploymentStatus = 'ACTIVE' | 'INACTIVE';

export type Department =
  | 'Engineering'
  | 'Design'
  | 'Product'
  | 'Human Resources'
  | 'Finance'
  | 'Marketing'
  | 'Sales'
  | 'Operations'
  | 'People Analytics';

export interface EmployeeListItem {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  job_title: string;
  department: Department;
  date_of_joining: string;
  employment_status: EmploymentStatus;
}

export interface Employee extends EmployeeListItem {
  created_at: string;
  updated_at: string;
}

export interface EmployeePage {
  items: EmployeeListItem[];
  total: number;
  skip: number;
  limit: number;
  page: number;
  total_pages: number;
  has_previous: boolean;
  has_next: boolean;
}

export interface EmployeeFormData {
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  job_title: string;
  department: Department;
  date_of_joining: string;
  employment_status: EmploymentStatus;
}

export interface DashboardStats {
  totalEmployees: number;
  activeEmployees: number;
  inactiveEmployees: number;
  departmentsCount: number;
}

export type SortField = 'name' | 'code' | 'department' | 'date_of_joining' | 'status';
export type SortDirection = 'asc' | 'desc';

export interface EmployeeListRequestParams {
  skip?: number;
  limit?: number;
  search?: string;
  department?: Department | 'All';
  status?: EmploymentStatus | 'ALL';
  sortBy?: SortField | 'created_at';
  sortOrder?: SortDirection;
}
