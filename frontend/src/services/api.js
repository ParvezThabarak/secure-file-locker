import axios from 'axios';
import toast from 'react-hot-toast';

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000/api' : '/api'),
  timeout: 10000,
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 401) {
        // Handle unauthorized access
        toast.error(data.error || 'Unauthorized. Please log in again.');
        // Redirect to login if not already there
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      } else if (status === 403) {
        toast.error(data.error || 'Forbidden. You do not have access to this resource.');
      } else if (status === 404) {
        toast.error(data.error || 'Resource not found.');
      } else if (status === 409) {
        toast.error(data.error || 'Conflict. Resource already exists or cannot be processed.');
      } else if (status >= 500) {
        toast.error(data.error || 'Server error. Please try again later.');
      } else {
        toast.error(data.error || 'An error occurred.');
      }
    } else if (error.request) {
      // The request was made but no response was received
      toast.error('No response from server. Please check your network connection.');
    } else {
      // Something happened in setting up the request that triggered an Error
      toast.error('An unexpected error occurred: ' + error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api;
