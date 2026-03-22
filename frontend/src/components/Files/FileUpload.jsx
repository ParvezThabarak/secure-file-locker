import React, { useState, useRef } from 'react';
import { filesAPI } from '../../services/files';
import Button from '../UI/Button';
import toast from 'react-hot-toast';

const FileUpload = ({ onUploadSuccess, currentFolder = '' }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFiles(files);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleFiles(files);
    }
  };

  const handleFiles = async (files) => {
    setUploading(true);
    const uploadPromises = files.map(file => uploadFile(file));
    
    try {
      const results = await Promise.all(uploadPromises);
      const successfulUploads = results.filter(result => result.success);
      
      if (successfulUploads.length > 0) {
        toast.success(`${successfulUploads.length} file(s) uploaded successfully`);
        onUploadSuccess && onUploadSuccess();
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
      setUploadProgress({});
    }
  };

  const uploadFile = async (file) => {
    try {
      // Check file size (100MB limit)
      if (file.size > 100 * 1024 * 1024) {
        toast.error(`File ${file.name} is too large. Maximum size is 100MB.`);
        return { success: false, error: 'File too large' };
      }

      // Create FormData
      const formData = new FormData();
      formData.append('file', file);
      if (currentFolder) {
        formData.append('folder_path', currentFolder);
      }

      // Upload file
      const response = await filesAPI.upload(formData);
      
      return { success: true, file: response.data.file };
    } catch (error) {
      const message = error.response?.data?.error || 'Upload failed';
      toast.error(`Failed to upload ${file.name}: ${message}`);
      return { success: false, error: message };
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="mb-6">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="space-y-4">
          <div className="mx-auto w-12 h-12 text-gray-400">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              {isDragging ? 'Drop files here' : 'Upload files'}
            </h3>
            <p className="text-sm text-gray-500">
              Drag and drop files here, or click to select files
            </p>
            {currentFolder && (
              <p className="text-sm text-blue-600 mt-1 font-medium">
                📁 Uploading to: {currentFolder}
              </p>
            )}
            <p className="text-xs text-gray-400 mt-1">
              Maximum file size: 100MB
            </p>
          </div>
          
          <div className="flex justify-center space-x-3">
            <Button
              onClick={openFileDialog}
              disabled={uploading}
              className="bg-primary-600 hover:bg-primary-700"
            >
              {uploading ? 'Uploading...' : 'Select Files'}
            </Button>
          </div>
        </div>
      </div>
      
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        accept="*/*"
      />
      
      {uploading && (
        <div className="mt-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-800">
                  Uploading files...
                </p>
                <p className="text-sm text-blue-600">
                  Please wait while your files are being uploaded to the cloud.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
