/**
 * API Client for AI Bookkeeper Backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public data: any) {
    super(`API Error: ${status}`);
  }
}

async function fetchJSON<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include", // For cookie-based JWT
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new ApiError(res.status, data);
  }

  return data;
}

// Auth API
export const authAPI = {
  login: (email: string, password?: string, magicToken?: string) =>
    fetchJSON("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, magic_token: magicToken }),
    }),

  logout: () =>
    fetchJSON("/api/auth/logout", {
      method: "POST",
    }),

  me: () => fetchJSON("/api/auth/me"),
};

// Tenants API
export const tenantsAPI = {
  list: () => fetchJSON("/api/tenants"),
  
  get: (id: string) => fetchJSON(`/api/tenants/${id}`),
  
  updateSettings: (id: string, settings: any) =>
    fetchJSON(`/api/tenants/${id}/settings`, {
      method: "POST",
      body: JSON.stringify(settings),
    }),
};

// Rules API
export const rulesAPI = {
  getCandidates: (status?: string) => {
    const params = status ? `?status=${status}` : "";
    return fetchJSON(`/api/rules/candidates${params}`);
  },

  dryRun: (candidateIds: string[], tenantId: string) =>
    fetchJSON("/api/rules/dryrun", {
      method: "POST",
      body: JSON.stringify({ candidate_ids: candidateIds, tenant_id: tenantId }),
    }),

  accept: (id: string) =>
    fetchJSON(`/api/rules/candidates/${id}/accept`, {
      method: "POST",
    }),

  reject: (id: string) =>
    fetchJSON(`/api/rules/candidates/${id}/reject`, {
      method: "POST",
    }),

  rollback: (toVersion: string) =>
    fetchJSON("/api/rules/rollback", {
      method: "POST",
      body: JSON.stringify({ to_version: toVersion }),
    }),

  getVersions: () => fetchJSON("/api/rules/versions"),
};

// Audit API
export const auditAPI = {
  exportCSV: (filters: Record<string, string>) => {
    const params = new URLSearchParams(filters);
    return `${API_BASE}/api/audit/export.csv?${params}`;
  },
};

// Transactions API
export const transactionsAPI = {
  list: (filters?: Record<string, any>) => {
    const params = new URLSearchParams(filters);
    return fetchJSON(`/api/transactions?${params}`);
  },

  approve: (ids: string[]) =>
    fetchJSON("/api/transactions/approve", {
      method: "POST",
      body: JSON.stringify({ transaction_ids: ids }),
    }),
};

// Export API
export const exportAPI = {
  toQBO: (tenantId: string, dateFrom: string, dateTo: string) =>
    fetchJSON("/api/export/qbo", {
      method: "POST",
      body: JSON.stringify({ tenant_id: tenantId, date_from: dateFrom, date_to: dateTo }),
    }),

  toXero: (tenantId: string, dateFrom: string, dateTo: string) =>
    fetchJSON("/api/export/xero", {
      method: "POST",
      body: JSON.stringify({ tenant_id: tenantId, date_from: dateFrom, date_to: dateTo }),
    }),

  getXeroStatus: (tenantId: string) =>
    fetchJSON(`/api/export/xero/status?tenant_id=${tenantId}`),
};

