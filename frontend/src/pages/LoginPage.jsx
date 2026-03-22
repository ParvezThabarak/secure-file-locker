import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/UI/Button';
import toast from 'react-hot-toast';

const LoginPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    otp_code: '',
    recovery_code: '',
    remember: false,
  });
  const [loading, setLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [useRecoveryCode, setUseRecoveryCode] = useState(false);
  
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await login(formData);
      
      if (result.success) {
        const from = location.state?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
      } else if (result.error === '2FA code required') {
        setRequires2FA(true);
        toast.info('Please enter your 2FA code');
      } else {
        toast.error(result.error);
      }
    } catch (error) {
      toast.error('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{' '}
            <Link
              to="/register"
              className="font-medium text-primary-600 hover:text-primary-500"
            >
              create a new account
            </Link>
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="form-label">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="input-field mt-1"
                placeholder="Enter your email"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={formData.password}
                onChange={handleChange}
                className="input-field mt-1"
                placeholder="Enter your password"
              />
            </div>

            {requires2FA && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label htmlFor={useRecoveryCode ? "recovery_code" : "otp_code"} className="form-label">
                    {useRecoveryCode ? 'Recovery Code' : 'Two-Factor Authentication Code'}
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setUseRecoveryCode(!useRecoveryCode);
                      setFormData(prev => ({ ...prev, otp_code: '', recovery_code: '' }));
                    }}
                    className="text-sm text-blue-600 hover:text-blue-500"
                  >
                    {useRecoveryCode ? 'Use authenticator app' : 'Use recovery code'}
                  </button>
                </div>
                
                {useRecoveryCode ? (
                  <input
                    id="recovery_code"
                    name="recovery_code"
                    type="text"
                    required
                    value={formData.recovery_code}
                    onChange={handleChange}
                    className="input-field mt-1 text-center text-lg tracking-widest"
                    placeholder="ABCD1234"
                    maxLength="8"
                  />
                ) : (
                  <input
                    id="otp_code"
                    name="otp_code"
                    type="text"
                    required
                    value={formData.otp_code}
                    onChange={handleChange}
                    className="input-field mt-1 text-center text-lg tracking-widest"
                    placeholder="000000"
                    maxLength="6"
                  />
                )}
                
                <p className="mt-1 text-xs text-gray-500">
                  {useRecoveryCode 
                    ? 'Enter one of your recovery codes (8 characters)'
                    : 'Enter the 6-digit code from your authenticator app'
                  }
                </p>
              </div>
            )}
            
            <div className="flex items-center">
              <input
                id="remember"
                name="remember"
                type="checkbox"
                checked={formData.remember}
                onChange={handleChange}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="remember" className="ml-2 block text-sm text-gray-900">
                Remember me
              </label>
            </div>
          </div>

          <div>
            <Button
              type="submit"
              className="w-full"
              loading={loading}
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
