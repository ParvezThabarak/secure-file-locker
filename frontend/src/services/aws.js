import api from './api';

export const awsAPI = {
  // Get AWS credentials status
  getStatus: () => api.get('/aws/status'),
  
  // Setup AWS credentials
  setup: (credentials) => api.post('/aws/setup', credentials),
  
  // Test AWS credentials without saving
  test: (credentials) => api.post('/aws/test', credentials),
  
  // Remove AWS credentials
  remove: () => api.delete('/aws/remove')
};
