/**
 * Authentication Context - Global User State Management
 * ======================================================
 * 
 * This module provides React Context for user authentication state throughout
 * the Next.js application. It manages the current user, login/logout actions,
 * and loading states.
 * 
 * Architecture:
 * ------------
 * Uses React Context API to share authentication state across components
 * without prop drilling. Any component can access user info via useAuth() hook.
 * 
 * Features:
 * --------
 * - Automatic user fetch on app load (checks if already logged in)
 * - Global login/logout functions
 * - Loading state for auth operations
 * - User data caching (avoid repeated API calls)
 * - Role-based access control (owner vs staff)
 * - Multi-tenant support (user can access multiple companies)
 * 
 * Usage:
 * ------
 * 1. Wrap app with AuthProvider in root layout:
 *    <AuthProvider>
 *      <App />
 *    </AuthProvider>
 * 
 * 2. Access auth state in any component:
 *    const { user, loading, login, logout } = useAuth();
 * 
 *    if (loading) return <Loading />;
 *    if (!user) return <LoginPage />;
 *    return <Dashboard user={user} />;
 * 
 * Protected Routes:
 * ----------------
 * Components can check user state to enforce authentication:
 * - if (!user): Redirect to login
 * - if (user.role !== "owner"): Show permission denied
 * - if (!user.tenant_ids.includes(tenantId)): Block access
 * 
 * Session Management:
 * ------------------
 * - JWT token stored in HTTP-only cookie (managed by backend)
 * - Frontend doesn't directly handle tokens
 * - On app load, calls /api/auth/me to check if logged in
 * - If 401 response, user is logged out
 * - If 200 response, user data is loaded into context
 * 
 * State Flow:
 * ----------
 * 1. App loads → fetchUser() called automatically
 * 2. fetchUser() calls /api/auth/me
 * 3. If successful → setUser(data)
 * 4. If fails (401) → setUser(null)
 * 5. setLoading(false) → UI can render
 * 
 * Login Flow:
 * ----------
 * 1. User submits login form
 * 2. login() calls authAPI.login()
 * 3. Backend sets HTTP-only cookie
 * 4. fetchUser() gets full user data
 * 5. User state updated → UI redirects to dashboard
 * 
 * Logout Flow:
 * -----------
 * 1. User clicks logout
 * 2. logout() calls authAPI.logout()
 * 3. Backend clears cookie
 * 4. setUser(null) → UI redirects to login
 */
"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { authAPI } from "@/lib/api";

/**
 * User Interface - Authenticated User Data
 * 
 * Represents the current logged-in user.
 */
export interface User {
  user_id: string;           // Unique user identifier
  email: string;             // User's email address
  role: "owner" | "staff";   // Access level (owner = full, staff = read-only)
  tenant_ids: string[];      // Companies/tenants user can access
}

/**
 * Auth Context Value Interface
 * 
 * Shape of the data provided by AuthContext.
 */
interface AuthContextValue {
  user: User | null;          // Current user (null if logged out)
  loading: boolean;           // True while fetching user data
  login: (email: string, password?: string, magicToken?: string) => Promise<void>;
  logout: () => Promise<void>;
  refetch: () => Promise<void>;  // Manually refresh user data
}

// Create React Context for authentication state
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Auth Provider Component - Provides Authentication Context to App
 * 
 * This component wraps the entire app and provides authentication state
 * to all child components via React Context.
 * 
 * @param children - App components that need access to auth state
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  // User state: null = logged out, User object = logged in
  const [user, setUser] = useState<User | null>(null);
  
  // Loading state: true while checking authentication status
  const [loading, setLoading] = useState(true);

  /**
   * Fetch User Data - Get current user from backend
   * 
   * Called:
   * - On app load (useEffect below)
   * - After login (to get full user data)
   * - On manual refetch
   * 
   * Sets user state based on /api/auth/me response:
   * - Success (200): User is logged in → set user data
   * - Failure (401): User is logged out → set user to null
   */
  const fetchUser = async () => {
    try {
      const data = await authAPI.me();
      
      // Backend returns user data, transform to User interface
      setUser({
        user_id: data.user_id,
        email: data.email,
        role: data.role,
        tenant_ids: data.tenants || []  // List of companies user can access
      });
    } catch (err) {
      // API call failed (likely 401 Unauthorized)
      // User is not logged in
      setUser(null);
    } finally {
      // Always set loading to false (even if fetch fails)
      setLoading(false);
    }
  };

  /**
   * Auto-fetch user on app load
   * 
   * This runs once when the app first loads to check if user is
   * already logged in (via existing cookie).
   */
  useEffect(() => {
    fetchUser();
  }, []);  // Empty deps = run once on mount

  /**
   * Login Function - Authenticate user
   * 
   * @param email - User's email
   * @param password - User's password (optional for magic link)
   * @param magicToken - Magic link token (dev mode only)
   * 
   * Process:
   * 1. Call backend /api/auth/login (sets HTTP-only cookie)
   * 2. Fetch full user data from /api/auth/me
   * 3. Update user state → UI redirects to dashboard
   */
  const login = async (email: string, password?: string, magicToken?: string) => {
    await authAPI.login(email, password, magicToken);
    
    // After login, fetch full user info (includes tenant IDs)
    await fetchUser();
  };

  /**
   * Logout Function - Clear session
   * 
   * Process:
   * 1. Call backend /api/auth/logout (clears cookie)
   * 2. Clear user state → UI redirects to login
   */
  const logout = async () => {
    await authAPI.logout();
    setUser(null);  // Clear user state immediately
  };

  /**
   * Refetch Function - Manually reload user data
   * 
   * Useful when user data may have changed (e.g., role updated,
   * tenant access changed).
   */
  const refetch = async () => {
    setLoading(true);  // Show loading state during refetch
    await fetchUser();
  };

  // Provide auth state and functions to all child components
  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refetch }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth Hook - Access Authentication State
 * 
 * This hook provides access to the authentication context in any component.
 * Must be used within a component wrapped by AuthProvider.
 * 
 * @returns AuthContextValue with user, loading, login, logout, refetch
 * @throws Error if used outside of AuthProvider
 * 
 * @example
 * function Dashboard() {
 *   const { user, loading, logout } = useAuth();
 *   
 *   if (loading) return <div>Loading...</div>;
 *   if (!user) return <Navigate to="/login" />;
 *   
 *   return (
 *     <div>
 *       <h1>Welcome, {user.email}</h1>
 *       <button onClick={logout}>Logout</button>
 *     </div>
 *   );
 * }
 */
export function useAuth() {
  const context = useContext(AuthContext);
  
  // Ensure hook is used within AuthProvider
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  
  return context;
}

