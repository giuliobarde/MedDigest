// API Configuration for MedDigest Frontend

const isDevelopment = process.env.NODE_ENV === 'development';

// API Base URL - use localhost for development, deployed URL for production
export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8000' 
  : 'https://med-digest-ch2gclx5n-giulio-bardellis-projects.vercel.app';

// API Endpoints - these are backend API routes, not frontend pages
export const API_ENDPOINTS = {
  newsletter: `${API_BASE_URL}/api/newsletter`,
  signup: `${API_BASE_URL}/api/signup`,
} as const;

// Helper function to get API URL
export const getApiUrl = (endpoint: keyof typeof API_ENDPOINTS): string => {
  return API_ENDPOINTS[endpoint];
}; 