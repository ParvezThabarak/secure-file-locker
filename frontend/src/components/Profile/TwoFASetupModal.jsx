import React, { useState } from 'react';
import { profileAPI } from '../../services/profile';
import Modal from '../UI/Modal';
import Button from '../UI/Button';
import toast from 'react-hot-toast';

const TwoFASetupModal = ({ isOpen, onClose, onSuccess }) => {
  const [step, setStep] = useState(1); // 1: QR Code, 2: Verification, 3: Recovery Codes
  const [qrCode, setQrCode] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleStartSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await profileAPI.enable2FA();
      setQrCode(response.data.qr_code);
      setStep(2);
      toast.success('QR code generated! Scan it with your authenticator app.');
    } catch (err) {
      const message = err.response?.data?.error || 'Failed to start 2FA setup';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!otpCode.trim()) {
      setError('Please enter the 6-digit code from your authenticator app');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await profileAPI.verify2FA(otpCode);
      setRecoveryCodes(response.data.recovery_codes);
      setStep(3);
      toast.success('2FA enabled successfully!');
    } catch (err) {
      const message = err.response?.data?.error || 'Invalid verification code';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = () => {
    onSuccess();
    onClose();
    resetModal();
  };

  const resetModal = () => {
    setStep(1);
    setQrCode('');
    setOtpCode('');
    setRecoveryCodes([]);
    setError('');
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  const copyRecoveryCodes = () => {
    const codesText = recoveryCodes.join('\n');
    navigator.clipboard.writeText(codesText);
    toast.success('Recovery codes copied to clipboard!');
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Setup Two-Factor Authentication">
      <div className="space-y-6">
        {step === 1 && (
          <div className="text-center">
            <div className="mb-4">
              <svg className="mx-auto h-16 w-16 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Enable Two-Factor Authentication</h3>
            <p className="text-gray-600 mb-6">
              Two-factor authentication adds an extra layer of security to your account. 
              You'll need an authenticator app like Google Authenticator or Authy.
            </p>
            <Button
              onClick={handleStartSetup}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? 'Generating QR Code...' : 'Start Setup'}
            </Button>
          </div>
        )}

        {step === 2 && (
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Scan QR Code</h3>
            <div className="mb-6">
              {qrCode && (
                <div className="flex justify-center">
                  <img 
                    src={qrCode} 
                    alt="QR Code for 2FA setup" 
                    className="border border-gray-300 rounded-lg p-4 bg-white"
                  />
                </div>
              )}
            </div>
            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-4">
                1. Open your authenticator app (Google Authenticator, Authy, etc.)<br/>
                2. Scan the QR code above<br/>
                3. Enter the 6-digit code from your app below
              </p>
              <div className="max-w-xs mx-auto">
                <input
                  type="text"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  className="w-full text-center text-2xl font-mono border border-gray-300 rounded-md px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  maxLength={6}
                />
              </div>
            </div>
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
            <div className="flex justify-center space-x-3">
              <Button
                onClick={() => setStep(1)}
                className="bg-gray-200 text-gray-700 hover:bg-gray-300"
              >
                Back
              </Button>
              <Button
                onClick={handleVerifyCode}
                disabled={loading || otpCode.length !== 6}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? 'Verifying...' : 'Verify & Enable'}
              </Button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="text-center">
            <div className="mb-4">
              <svg className="mx-auto h-16 w-16 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">2FA Enabled Successfully!</h3>
            <p className="text-gray-600 mb-6">
              Save these recovery codes in a safe place. You can use them to access your account 
              if you lose your authenticator device.
            </p>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex items-start">
                <svg className="h-5 w-5 text-yellow-400 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div className="text-left">
                  <h4 className="text-sm font-medium text-yellow-800">Important!</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    Each recovery code can only be used once. Store them securely and don't share them with anyone.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
              <div className="grid grid-cols-2 gap-2 text-sm font-mono">
                {recoveryCodes.map((code, index) => (
                  <div key={index} className="p-2 bg-white border border-gray-200 rounded text-center">
                    {code}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-center space-x-3">
              <Button
                onClick={copyRecoveryCodes}
                className="bg-gray-200 text-gray-700 hover:bg-gray-300"
              >
                Copy Codes
              </Button>
              <Button
                onClick={handleComplete}
                className="bg-green-600 hover:bg-green-700"
              >
                Complete Setup
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default TwoFASetupModal;
