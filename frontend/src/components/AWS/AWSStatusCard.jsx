import React, { useState } from 'react';
import { useAWS } from '../../context/AWSContext';
import AWSSetupModal from './AWSSetupModal';
import Button from '../UI/Button';

const AWSStatusCard = () => {
  const { credentials, loading, removeCredentials } = useAWS();
  const [showSetupModal, setShowSetupModal] = useState(false);

  const handleRemoveCredentials = async () => {
    if (window.confirm('Are you sure you want to remove your AWS credentials? You won\'t be able to upload files until you set them up again.')) {
      try {
        await removeCredentials();
      } catch (error) {
        console.error('Error removing AWS credentials:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-gray-400 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">AWS Status</p>
            <p className="text-lg font-semibold text-gray-900">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!credentials) {
    return (
      <div className="card border-yellow-200 bg-yellow-50">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
          <div className="ml-4 flex-1">
            <p className="text-sm font-medium text-yellow-800">AWS Account</p>
            <p className="text-lg font-semibold text-yellow-900">Not Connected</p>
            <p className="text-sm text-yellow-700 mt-1">
              Connect your AWS account to start uploading files
            </p>
          </div>
          <div className="ml-4">
            <Button
              onClick={() => setShowSetupModal(true)}
              size="sm"
              className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200 border-yellow-300"
            >
              Connect
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="card border-green-200 bg-green-50">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
          <div className="ml-4 flex-1">
            <p className="text-sm font-medium text-green-800">AWS Account</p>
            <p className="text-lg font-semibold text-green-900">Connected</p>
            <div className="text-sm text-green-700 mt-1">
              <p>Region: <span className="font-medium">{credentials.region}</span></p>
              <p>Bucket: <span className="font-medium">{credentials.bucket_name}</span></p>
              <p className="text-xs text-green-600 mt-1">
                Connected on {new Date(credentials.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="ml-4 flex flex-col space-y-2">
            <Button
              onClick={() => setShowSetupModal(true)}
              size="sm"
              variant="outline"
              className="border-green-300 text-green-700 hover:bg-green-100"
            >
              Update
            </Button>
            <Button
              onClick={handleRemoveCredentials}
              size="sm"
              variant="outline"
              className="border-red-300 text-red-700 hover:bg-red-100"
            >
              Disconnect
            </Button>
          </div>
        </div>
      </div>

      <AWSSetupModal
        isOpen={showSetupModal}
        onClose={() => setShowSetupModal(false)}
        onSuccess={() => setShowSetupModal(false)}
      />
    </>
  );
};

export default AWSStatusCard;
