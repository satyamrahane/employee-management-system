const SORT_FIELD_PARAMS = {
  name: 'name',
  code: 'employee_code',
  department: 'department',
  date_of_joining: 'date_of_joining',
  status: 'employment_status',
  created_at: 'created_at',
};

function buildEmployeeListUrl(apiBaseUrl, params = {}) {
  const url = new URL(`${apiBaseUrl}/employees`);
  url.searchParams.set('skip', String(params.skip ?? 0));
  url.searchParams.set('limit', String(params.limit ?? 100));

  if (params.search && params.search.trim()) {
    url.searchParams.set('search', params.search.trim());
  }
  if (params.department && params.department !== 'All') {
    url.searchParams.set('department', params.department);
  }
  if (params.status && params.status !== 'ALL') {
    url.searchParams.set('status', params.status);
  }
  if (params.sortBy) {
    url.searchParams.set('sort_by', SORT_FIELD_PARAMS[params.sortBy] || params.sortBy);
  }
  if (params.sortOrder) {
    url.searchParams.set('sort_order', params.sortOrder);
  }

  return url.toString();
}

exports.buildEmployeeListUrl = buildEmployeeListUrl;