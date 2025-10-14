"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getUser, isAuthenticated, logout as logoutUser, type User } from '@/lib/auth';

/**
 * Hook for authentication state and actions
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check authentication on mount
    const currentUser = getUser();
    setUser(currentUser);
    setLoading(false);
  }, []);

  const logout = async () => {
    await logoutUser();
    setUser(null);
    router.push('/login');
  };

  return {
    user,
    isAuthenticated: !!user,
    loading,
    logout,
  };
}

/**
 * Hook to require authentication (redirects to login if not authenticated)
 */
export function useRequireAuth() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
    } else {
      setLoading(false);
    }
  }, [router]);

  return { loading };
}

