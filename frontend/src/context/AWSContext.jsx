import React, { createContext, useContext, useState, useEffect } from 'react';
import { awsAPI } from '../services/aws';

const AWSContext = createContext();

export const useAWS = () => {
  const context = useContext(AWSContext);
  if (!context) {
    throw new Error('useAWS must be used within an AWSProvider');
  }
  return context;
};

export const AWSProvider = ({ children }) => {
  const [credentials, setCredentials] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkCredentialsStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await awsAPI.getStatus();
      setCredentials(response.data.has_credentials ? response.data.credentials : null);
    } catch (err) {
      console.error('Error checking AWS credentials status:', err);
      setError(err.message);
      setCredentials(null);
    } finally {
      setLoading(false);
    }
  };

  const setupCredentials = async (credentialsData) => {
    try {
      setLoading(true);
      setError(null);
      const response = await awsAPI.setup(credentialsData);
      setCredentials(response.data.credentials);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const removeCredentials = async () => {
    try {
      setLoading(true);
      setError(null);
      await awsAPI.remove();
      setCredentials(null);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const testCredentials = async (credentialsData) => {
    try {
      setError(null);
      const response = await awsAPI.test(credentialsData);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message;
      setError(errorMessage);
      throw err;
    }
  };

  useEffect(() => {
    checkCredentialsStatus();
  }, []);

  const value = {
    credentials,
    loading,
    error,
    hasCredentials: !!credentials,
    checkCredentialsStatus,
    setupCredentials,
    removeCredentials,
    testCredentials,
    clearError: () => setError(null)
  };

  return (
    <AWSContext.Provider value={value}>
      {children}
    </AWSContext.Provider>
  );
};
