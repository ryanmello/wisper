"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface GitHubUser {
  login: string;
  avatar_url: string;
  name: string | null;
}

interface AuthContextType {
  user: GitHubUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();

  const [user, setUser] = useState<GitHubUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Fetch user data from backend API
  const fetchUser = async (token: string): Promise<GitHubUser | null> => {
    try {
      const response = await fetch("http://localhost:8000/user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token }),
      });

      if (response.ok) {
        const body = await response.json()
        console.log(body)
        return body;
      }
      return null;
    } catch (error) {
      console.error("Failed to fetch user data:", error);
      return null;
    }
  };

  // Set token in both localStorage and cookies
  const setToken = (token: string) => {
    localStorage.setItem("github_token", token);
    // Set cookie for middleware
    document.cookie = `github_token=${token}; path=/; max-age=${60 * 60 * 24 * 7}`; // 7 days
  };

  // Remove token from both localStorage and cookies
  const removeToken = () => {
    localStorage.removeItem("github_token");
    // Remove cookie
    document.cookie = 'github_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  };

  // Login function
  const login = async (token: string) => {
    setIsLoading(true);
    try {
      const userData = await fetchUser(token);
      
      if (userData) {
        setUser(userData);
        setIsAuthenticated(true);
        setToken(token);
      } else {
        throw new Error("Invalid token");
      }
    } catch (error) {
      removeToken();
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    removeToken();
    setUser(null);
    setIsAuthenticated(false);
    router.push('/sign-in');
  };

  // Refresh user data
  const refreshUser = async () => {
    const token = localStorage.getItem("github_token");
    if (token) {
      try {
        const userData = await fetchUser(token);
        if (userData) {
          setUser(userData);
          setIsAuthenticated(true);
        } else {
          logout();
        }
      } catch (error) {
        logout();
      }
    }
  };

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem("github_token");
      
      if (token) {
        try {
          const userData = await fetchUser(token);
          if (userData) {
            setUser(userData);
            setIsAuthenticated(true);
            // Ensure cookie is set
            setToken(token);
          } else {
            removeToken();
          }
        } catch (error) {
          removeToken();
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 
