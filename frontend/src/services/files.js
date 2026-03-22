import api from './api';

export const filesAPI = {
  // Upload a file
  upload: (formData) => api.post('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  
  // Create a folder
  createFolder: (data) => api.post('/files/create-folder', data),
  
  // List user's files and folders
  list: (params = {}) => api.get('/files/', { params }),
  
  // Download a file
  download: (fileId) => api.get(`/files/${fileId}/download`, { 
    responseType: 'blob' 
  }),
  
  // Generate share URL
  share: (fileId) => api.post(`/files/${fileId}/share`),
  
  // Delete a file or folder
  delete: (fileId) => api.delete(`/files/${fileId}`),
  
  // Get file statistics
  getStats: () => api.get('/files/stats'),
};
