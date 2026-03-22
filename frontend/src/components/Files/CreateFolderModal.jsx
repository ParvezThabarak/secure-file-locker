import React, { useState } from 'react';
import { filesAPI } from '../../services/files';
import Button from '../UI/Button';
import Modal from '../UI/Modal';
import toast from 'react-hot-toast';

const CreateFolderModal = ({ isOpen, onClose, onSuccess, currentFolder = '' }) => {
  const [folderName, setFolderName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!folderName.trim()) {
      setError('Folder name is required');
      return;
    }

    if (folderName.trim().length < 1) {
      setError('Folder name must be at least 1 character long');
      return;
    }

    if (folderName.trim().length > 100) {
      setError('Folder name must be less than 100 characters');
      return;
    }

    // Check for invalid characters
    const invalidChars = /[<>:"/\\|?*]/;
    if (invalidChars.test(folderName.trim())) {
      setError('Folder name contains invalid characters');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await filesAPI.createFolder({
        folder_name: folderName.trim(),
        parent_folder_path: currentFolder
      });
      
      toast.success('Folder created successfully');
      onSuccess && onSuccess();
      onClose();
      setFolderName('');
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to create folder';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFolderName('');
    setError('');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Folder">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="form-group">
          <label htmlFor="folder_name" className="form-label">
            Folder Name
          </label>
          <input
            type="text"
            id="folder_name"
            value={folderName}
            onChange={(e) => {
              setFolderName(e.target.value);
              setError('');
            }}
            className={`input-field ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
            placeholder="Enter folder name"
            disabled={loading}
            autoFocus
          />
          {error && (
            <p className="error-message">{error}</p>
          )}
        </div>

        {currentFolder && (
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Location:</span> {currentFolder || 'Root folder'}
            </p>
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4">
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
            disabled={loading || !folderName.trim()}
          >
            {loading ? 'Creating...' : 'Create Folder'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default CreateFolderModal;
