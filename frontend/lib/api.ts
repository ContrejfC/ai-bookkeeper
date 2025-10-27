/**
 * API Client - Frontend to Backend Communication Layer
 * ====================================================
 * 
 * This module provides a type-safe, centralized API client for all backend
 * communication from the Next.js frontend.
 * 
 * Architecture:
 * ------------
 * - Wraps fetch() with error handling and JSON parsing
 * - Automatically includes authentication cookies
 * - Provides namespaced API functions by feature
 * - Throws ApiError for failed requests (can be caught in UI)
 * 
 * Configuration:
 * -------------
 * API base URL is configured via environment variable:
 * - NEXT_PUBLIC_API_URL: Backend API URL (default: http://localhost:8000)
 * - Set in .env.local (dev) or .env.production (prod)
 * 
 * Authentication:
 * --------------
 * - Uses HTTP-only cookies for JWT tokens
 * - credentials: "include" ensures cookies are sent with requests
 * - No need to manually manage tokens in localStorage
 * - Automatically handles 401 errors (can redirect to login)
 * 
 * Error Handling:
 * --------------
 * All API functions throw ApiError on failure:
 * - status: HTTP status code (401, 403, 404, 500, etc.)
 * - data: Response body from backend (may include error details)
 * 
 * Usage Example:
 * -------------
 * ```typescript
 * try {
 *   const data = await authAPI.login("user@example.com", "password");
 *   console.log("Logged in:", data.user_id);
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     if (error.status === 401) {
 *       console.log("Invalid credentials");
 *     }
 *   }
 * }
 * ```
 * 
 * API Namespaces:
 * --------------
 * - authAPI: Login, logout, current user
 * - tenantsAPI: Company/tenant management
 * - rulesAPI: Categorization rules management
 * - auditAPI: Audit logs and exports
 * - transactionsAPI: Transaction operations
 * - exportAPI: Export to QuickBooks/Xero
 */

// API Base URL - Configurable via environment variable
// In production, this points to Google Cloud Run backend
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom Error Class for API Failures
 * 
 * Thrown by fetchJSON() when API returns non-2xx status.
 * Contains HTTP status code and response body for error handling.
 */
export class ApiError extends Error {
  constructor(public status: number, public data: any) {
    super(`API Error: ${status}`);
  }
}

/**
 * Core Fetch Wrapper - Makes HTTP requests with error handling
 * 
 * This function handles all HTTP communication with the backend.
 * It automatically:
 * - Sets Content-Type to application/json
 * - Includes authentication cookies (credentials: include)
 * - Parses JSON responses
 * - Throws ApiError for non-2xx responses
 * 
 * @param endpoint - API endpoint path (e.g., "/api/auth/login")
 * @param options - Fetch options (method, body, headers, etc.)
 * @returns Parsed JSON response data
 * @throws ApiError if response status is not 2xx
 * 
 * @example
 * const user = await fetchJSON<User>("/api/auth/me");
 * const result = await fetchJSON("/api/transactions", {
 *   method: "POST",
 *   body: JSON.stringify({ ids: [1, 2, 3] })
 * });
 */
async function fetchJSON<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Construct full URL (base + endpoint)
  const url = `${API_BASE}${endpoint}`;
  
  // Make HTTP request with default headers
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",  // All requests send JSON
      ...options.headers,                   // Allow override if needed
    },
    credentials: "include",  // CRITICAL: Send HTTP-only cookies with request
  });

  // Parse JSON response (or empty object if parsing fails)
  const data = await res.json().catch(() => ({}));

  // Throw error for non-2xx responses (handled by calling code)
  if (!res.ok) {
    throw new ApiError(res.status, data);
  }

  return data;
}

// ==========================================================================
// Authentication API - User Login, Logout, and Session Management
// ==========================================================================
/**
 * Authentication API client
 * 
 * Handles user authentication with JWT tokens stored in HTTP-only cookies.
 */
export const authAPI = {
  /**
   * Login - Authenticate user and receive JWT token
   * 
   * @param email - User's email address
   * @param password - User's password (optional for magic link)
   * @param magicToken - Magic link token for passwordless login (dev mode)
   * @returns User data (user_id, email, role)
   * @throws ApiError(401) if credentials invalid
   * @throws ApiError(403) if account inactive
   */
  login: (email: string, password?: string, magicToken?: string) =>
    fetchJSON("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, magic_token: magicToken }),
    }),

  /**
   * Logout - Clear session and JWT cookie
   * 
   * @returns Success message
   */
  logout: () =>
    fetchJSON("/api/auth/logout", {
      method: "POST",
    }),

  /**
   * Get Current User - Retrieve authenticated user info
   * 
   * @returns User data (user_id, email, role, tenants)
   * @throws ApiError(401) if not authenticated
   */
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

