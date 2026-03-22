import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useAWS } from '../context/AWSContext';
import { filesAPI } from '../services/files';
import FileUpload from '../components/Files/FileUpload';
import FileList from '../components/Files/FileList';
import CreateFolderModal from '../components/Files/CreateFolderModal';
import Button from '../components/UI/Button';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import toast from 'react-hot-toast';

const FilesPage = () => {
  const { user } = useAuth();
  const { hasCredentials } = useAWS();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentFolder, setCurrentFolder] = useState('');
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState([]);

  useEffect(() => {
    loadFiles();
  }, [currentFolder]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      console.log('Loading files for folder:', currentFolder);
      console.log('API call will be made with folder_path:', currentFolder);
      const response = await filesAPI.list({ folder_path: currentFolder });
      console.log('Files response:', response.data);
      setFiles(response.data.files);
      updateBreadcrumbs();
    } catch (error) {
      console.error('Error loading files:', error);
      toast.error('Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  const updateBreadcrumbs = () => {
    if (!currentFolder) {
      setBreadcrumbs([{ name: 'Home', path: '' }]);
      return;
    }

    const parts = currentFolder.split('/').filter(part => part);
    const breadcrumbItems = [{ name: 'Home', path: '' }];
    
    let currentPath = '';
    parts.forEach(part => {
      currentPath += part + '/';
      breadcrumbItems.push({ name: part, path: currentPath });
    });
    
    setBreadcrumbs(breadcrumbItems);
  };

  const handleFileAction = (action, data) => {
    if (action === 'navigate') {
      console.log('Navigating to folder:', data.s3_key);
      console.log('Setting currentFolder to:', data.s3_key);
      // Keep the trailing slash for folder navigation
      setCurrentFolder(data.s3_key);
    } else {
      loadFiles(); // Refresh the file list
    }
  };

  const handleBreadcrumbClick = (path) => {
    setCurrentFolder(path);
  };

  const getCurrentFolderName = () => {
    if (!currentFolder) return 'Home';
    const parts = currentFolder.split('/').filter(part => part);
    return parts[parts.length - 1] || 'Home';
  };

  if (!hasCredentials) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">
                    AWS Account Required
                  </h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    <p>
                      You need to connect your AWS account before you can upload and manage files. 
                      Please go to the dashboard to set up your AWS credentials.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">File Manager</h1>
              <p className="mt-2 text-gray-600">
                Upload, organize, and manage your files in the cloud
              </p>
            </div>
            <Button
              onClick={() => setShowCreateFolder(true)}
              className="bg-primary-600 hover:bg-primary-700"
            >
              Create Folder
            </Button>
          </div>

          {/* Breadcrumbs */}
          {breadcrumbs.length > 1 && (
            <nav className="flex mb-6" aria-label="Breadcrumb">
              <ol className="flex items-center space-x-2">
                {breadcrumbs.map((crumb, index) => (
                  <li key={index} className="flex items-center">
                    {index > 0 && (
                      <svg className="w-4 h-4 text-gray-400 mx-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                    <button
                      onClick={() => handleBreadcrumbClick(crumb.path)}
                      className={`text-sm font-medium ${
                        index === breadcrumbs.length - 1
                          ? 'text-gray-500'
                          : 'text-primary-600 hover:text-primary-800'
                      }`}
                    >
                      {crumb.name}
                    </button>
                  </li>
                ))}
              </ol>
            </nav>
          )}

          {/* Current Location Info */}
          {currentFolder && (
            <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-blue-800">
                    Currently in: {currentFolder}
                  </p>
                  <p className="text-xs text-blue-600">
                    Files uploaded here will be saved in this folder
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* File Upload */}
          <FileUpload 
            onUploadSuccess={loadFiles}
            currentFolder={currentFolder}
          />

          {/* File List */}
          {loading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <div>
              {files.length > 0 && (
                <div className="mb-4 text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
                  <p className="flex items-center">
                    <svg className="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    💡 <strong>Tip:</strong> Click on folder names to navigate inside them. You can upload files directly into any folder.
                  </p>
                </div>
              )}
              <FileList 
                files={files}
                onFileAction={handleFileAction}
                currentFolder={currentFolder}
              />
            </div>
          )}

          {/* Create Folder Modal */}
          <CreateFolderModal
            isOpen={showCreateFolder}
            onClose={() => setShowCreateFolder(false)}
            onSuccess={loadFiles}
            currentFolder={currentFolder}
          />
        </div>
      </div>
    </div>
  );
};

export default FilesPage;
