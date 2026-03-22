import api from './api';

export const profileAPI = {
  // Get user profile
  getProfile: () => api.get('/profile/'),
  
  // Update user profile
  updateProfile: (data) => api.put('/profile/', data),
  
  // Change password
  changePassword: (data) => api.post('/profile/change-password', data),
  
  // 2FA endpoints
  get2FAStatus: () => api.get('/profile/2fa-status'),
  enable2FA: () => api.post('/profile/enable-2fa'),
  verify2FA: (otpCode) => api.post('/profile/verify-2fa', { otp_code: otpCode }),
  disable2FA: (password) => api.post('/profile/disable-2fa', { password }),
  regenerateRecoveryCodes: (password) => api.post('/profile/regenerate-recovery-codes', { password }),
};