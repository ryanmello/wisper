// Configuration utilities for the frontend application

export const getBackendUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}; 