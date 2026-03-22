import React, { useState } from 'react';
import { useAWS } from '../../context/AWSContext';
import Button from '../UI/Button';
import Modal from '../UI/Modal';
import toast from 'react-hot-toast';

const AWSSetupModal = ({ isOpen, onClose, onSuccess }) => {
  const { setupCredentials, testCredentials } = useAWS();
  const [formData, setFormData] = useState({
    access_key_id: '',
    secret_access_key: '',
    region: 'us-east-1',
    bucket_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.access_key_id.trim()) {
      newErrors.access_key_id = 'Access Key ID is required';
    }
    
    if (!formData.secret_access_key.trim()) {
      newErrors.secret_access_key = 'Secret Access Key is required';
    }
    
    if (!formData.region.trim()) {
      newErrors.region = 'Region is required';
    }
    
    if (!formData.bucket_name.trim()) {
      newErrors.bucket_name = 'Bucket name is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleTest = async () => {
    if (!validateForm()) return;
    
    setTesting(true);
    try {
      await testCredentials(formData);
      toast.success('AWS credentials are valid!');
    } catch (error) {
      // Error is already handled by the context
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      await setupCredentials(formData);
      toast.success('AWS credentials configured successfully!');
      onSuccess();
      onClose();
    } catch (error) {
      // Error is already handled by the context
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      access_key_id: '',
      secret_access_key: '',
      region: 'us-east-1',
      bucket_name: ''
    });
    setErrors({});
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Setup AWS Account">
      <div className="space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                AWS Credentials Required
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  To upload files to AWS S3, you need to provide your AWS credentials. 
                  Contact your IT administrator to get these credentials.
                </p>
              </div>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="form-group">
            <label htmlFor="access_key_id" className="form-label">
              AWS Access Key ID
            </label>
            <input
              type="text"
              id="access_key_id"
              name="access_key_id"
              value={formData.access_key_id}
              onChange={handleInputChange}
              className={`input-field ${errors.access_key_id ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
              placeholder="AKIA..."
            />
            {errors.access_key_id && (
              <p className="error-message">{errors.access_key_id}</p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="secret_access_key" className="form-label">
              AWS Secret Access Key
            </label>
            <input
              type="password"
              id="secret_access_key"
              name="secret_access_key"
              value={formData.secret_access_key}
              onChange={handleInputChange}
              className={`input-field ${errors.secret_access_key ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
              placeholder="Enter your secret access key"
            />
            {errors.secret_access_key && (
              <p className="error-message">{errors.secret_access_key}</p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="region" className="form-label">
              AWS Region
            </label>
            <select
              id="region"
              name="region"
              value={formData.region}
              onChange={handleInputChange}
              className={`input-field ${errors.region ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
            >
              <option value="us-east-1">US East (N. Virginia) - us-east-1</option>
              <option value="us-east-2">US East (Ohio) - us-east-2</option>
              <option value="us-west-1">US West (N. California) - us-west-1</option>
              <option value="us-west-2">US West (Oregon) - us-west-2</option>
              <option value="eu-west-1">Europe (Ireland) - eu-west-1</option>
              <option value="eu-west-2">Europe (London) - eu-west-2</option>
              <option value="eu-central-1">Europe (Frankfurt) - eu-central-1</option>
              <option value="ap-southeast-1">Asia Pacific (Singapore) - ap-southeast-1</option>
              <option value="ap-southeast-2">Asia Pacific (Sydney) - ap-southeast-2</option>
              <option value="ap-northeast-1">Asia Pacific (Tokyo) - ap-northeast-1</option>
            </select>
            {errors.region && (
              <p className="error-message">{errors.region}</p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="bucket_name" className="form-label">
              S3 Bucket Name
            </label>
            <input
              type="text"
              id="bucket_name"
              name="bucket_name"
              value={formData.bucket_name}
              onChange={handleInputChange}
              className={`input-field ${errors.bucket_name ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
              placeholder="my-company-files"
            />
            {errors.bucket_name && (
              <p className="error-message">{errors.bucket_name}</p>
            )}
          </div>

          <div className="flex justify-between pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleTest}
              disabled={testing || loading}
            >
              {testing ? 'Testing...' : 'Test Credentials'}
            </Button>
            
            <div className="flex space-x-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={loading || testing}
              >
                {loading ? 'Setting up...' : 'Setup AWS Account'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default AWSSetupModal;
