/**
 * Authentication utilities for JWT token management
 */

const TOKEN_KEY = 'ai_bookkeeper_token';
const USER_KEY = 'ai_bookkeeper_user';

export interface User {
  user_id: string;
  email: string;
  role: 'owner' | 'staff';
  tenants: string[];
}

export interface LoginResponse {
  success: boolean;
  user_id: string;
  email: string;
  role: string;
  token?: string;
}

/**
 * Store JWT token in localStorage
 */
export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

/**
 * Get JWT token from localStorage
 */
export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

/**
 * Remove JWT token from localStorage
 */
export function removeToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

/**
 * Store user info in localStorage
 */
export function setUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * Get user info from localStorage
 */
export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const userStr = localStorage.getItem(USER_KEY);
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
  }
  return null;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}

/**
 * Login user with email and password (or magic token for dev mode)
 */
export async function login(email: string, password?: string, magicToken?: string): Promise<LoginResponse> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password: password || undefined,
      magic_token: magicToken || undefined,
    }),
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data: LoginResponse = await response.json();
  
  if (data.success && data.token) {
    setToken(data.token);
    setUser({
      user_id: data.user_id,
      email: data.email,
      role: data.role as 'owner' | 'staff',
      tenants: [],
    });
  }

  return data;
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
      },
    });
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    removeToken();
  }
}

/**
 * Get authorization header with JWT token
 */
export function getAuthHeaders(): HeadersInit {
  const token = getToken();
  if (token) {
    return {
      'Authorization': `Bearer ${token}`,
    };
  }
  return {};
}

