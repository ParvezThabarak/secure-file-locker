import React, { useState, useEffect } from 'react';
import { profileAPI } from '../../services/profile';
import Button from '../UI/Button';
import Modal from '../UI/Modal';
import toast from 'react-hot-toast';

const TwoFAManagement = ({ onEnable2FA }) => {
  const [twoFAStatus, setTwoFAStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDisableModal, setShowDisableModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [password, setPassword] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState([]);

  useEffect(() => {
    load2FAStatus();
  }, []);

  const load2FAStatus = async () => {
    try {
      setLoading(true);
      const response = await profileAPI.get2FAStatus();
      setTwoFAStatus(response.data);
    } catch (error) {
      console.error('Error loading 2FA status:', error);
      toast.error('Failed to load 2FA status');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable2FA = async () => {
    if (!password.trim()) {
      toast.error('Please enter your password');
      return;
    }

    setActionLoading(true);
    try {
      await profileAPI.disable2FA(password);
      toast.success('2FA disabled successfully');
      setShowDisableModal(false);
      setPassword('');
      load2FAStatus();
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to disable 2FA';
      toast.error(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRegenerateRecoveryCodes = async () => {
    if (!password.trim()) {
      toast.error('Please enter your password');
      return;
    }

    setActionLoading(true);
    try {
      const response = await profileAPI.regenerateRecoveryCodes(password);
      setRecoveryCodes(response.data.recovery_codes);
      toast.success('Recovery codes regenerated successfully');
      setShowRegenerateModal(false);
      setPassword('');
      load2FAStatus();
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to regenerate recovery codes';
      toast.error(message);
    } finally {
      setActionLoading(false);
    }
  };

  const copyRecoveryCodes = () => {
    const codesText = recoveryCodes.join('\n');
    navigator.clipboard.writeText(codesText);
    toast.success('Recovery codes copied to clipboard!');
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900 mr-3"></div>
          <p className="text-gray-700">Loading 2FA status...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Two-Factor Authentication</h3>
          <div className="flex items-center">
            {twoFAStatus?.is_2fa_enabled ? (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Enabled
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                Disabled
              </span>
            )}
          </div>
        </div>

        <div className="text-sm text-gray-600 mb-6">
          {twoFAStatus?.is_2fa_enabled ? (
            <p>
              Two-factor authentication is enabled for your account. You'll need to enter a code from your 
              authenticator app when logging in.
            </p>
          ) : (
            <p>
              Two-factor authentication adds an extra layer of security to your account. 
              Enable it to protect your files and data.
            </p>
          )}
        </div>

        {twoFAStatus?.is_2fa_enabled && (
          <div className="mb-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="h-5 w-5 text-blue-400 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-blue-800">Recovery Codes</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    You have {twoFAStatus.recovery_codes_count} unused recovery codes. 
                    Use these if you lose access to your authenticator app.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="flex space-x-3">
          {!twoFAStatus?.is_2fa_enabled ? (
            <Button
              onClick={onEnable2FA}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Enable 2FA
            </Button>
          ) : (
            <>
              <Button
                onClick={() => setShowRegenerateModal(true)}
                className="bg-gray-200 text-gray-700 hover:bg-gray-300"
              >
                Regenerate Recovery Codes
              </Button>
              <Button
                onClick={() => setShowDisableModal(true)}
                className="bg-red-600 hover:bg-red-700"
              >
                Disable 2FA
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Disable 2FA Modal */}
      <Modal isOpen={showDisableModal} onClose={() => setShowDisableModal(false)} title="Disable Two-Factor Authentication">
        <div className="space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="h-5 w-5 text-red-400 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-red-800">Warning</h4>
                <p className="text-sm text-red-700 mt-1">
                  Disabling 2FA will make your account less secure. You'll only need your password to log in.
                </p>
              </div>
            </div>
          </div>

          <div>
            <label htmlFor="disable-password" className="block text-sm font-medium text-gray-700">
              Enter your password to confirm
            </label>
            <input
              type="password"
              id="disable-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="Your password"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              onClick={() => setShowDisableModal(false)}
              disabled={actionLoading}
              className="bg-gray-200 text-gray-700 hover:bg-gray-300"
            >
              Cancel
            </Button>
            <Button
              onClick={handleDisable2FA}
              disabled={actionLoading}
              className="bg-red-600 hover:bg-red-700"
            >
              {actionLoading ? 'Disabling...' : 'Disable 2FA'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Regenerate Recovery Codes Modal */}
      <Modal isOpen={showRegenerateModal} onClose={() => setShowRegenerateModal(false)} title="Regenerate Recovery Codes">
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="h-5 w-5 text-yellow-400 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-yellow-800">Important</h4>
                <p className="text-sm text-yellow-700 mt-1">
                  This will invalidate all your existing recovery codes and generate new ones. 
                  Make sure to save the new codes in a secure place.
                </p>
              </div>
            </div>
          </div>

          <div>
            <label htmlFor="regenerate-password" className="block text-sm font-medium text-gray-700">
              Enter your password to confirm
            </label>
            <input
              type="password"
              id="regenerate-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="Your password"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              onClick={() => setShowRegenerateModal(false)}
              disabled={actionLoading}
              className="bg-gray-200 text-gray-700 hover:bg-gray-300"
            >
              Cancel
            </Button>
            <Button
              onClick={handleRegenerateRecoveryCodes}
              disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {actionLoading ? 'Generating...' : 'Regenerate Codes'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Recovery Codes Display Modal */}
      {recoveryCodes.length > 0 && (
        <Modal isOpen={true} onClose={() => setRecoveryCodes([])} title="New Recovery Codes">
          <div className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="h-5 w-5 text-yellow-400 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-yellow-800">Save These Codes</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    Store these recovery codes in a safe place. Each code can only be used once.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="grid grid-cols-2 gap-2 text-sm font-mono">
                {recoveryCodes.map((code, index) => (
                  <div key={index} className="p-2 bg-white border border-gray-200 rounded text-center">
                    {code}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <Button
                onClick={copyRecoveryCodes}
                className="bg-gray-200 text-gray-700 hover:bg-gray-300"
              >
                Copy Codes
              </Button>
              <Button
                onClick={() => setRecoveryCodes([])}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Done
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
};

export default TwoFAManagement;
