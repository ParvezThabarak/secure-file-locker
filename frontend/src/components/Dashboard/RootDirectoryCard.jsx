import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { filesAPI } from '../../services/files';
import LoadingSpinner from '../UI/LoadingSpinner';
import Button from '../UI/Button';
import toast from 'react-hot-toast';

const RootDirectoryCard = () => {
  const [rootFiles, setRootFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRootFiles();
  }, []);

  const loadRootFiles = async () => {
    try {
      setLoading(true);
      const response = await filesAPI.list({ folder_path: '', per_page: 8 });
      setRootFiles(response.data.files);
    } catch (error) {
      console.error('Error loading root files:', error);
      toast.error('Failed to load root directory');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (file) => {
    try {
      const response = await filesAPI.download(file.id);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('File downloaded successfully');
    } catch (error) {
      const message = error.response?.data?.error || 'Download failed';
      toast.error(message);
    }
  };

  const getFileIcon = (file) => {
    if (file.is_folder) {
      return (
        <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
        </svg>
      );
    }

    const extension = file.extension?.toLowerCase();
    
    if (['.pdf'].includes(extension)) {
      return (
        <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'].includes(extension)) {
      return (
        <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (['.doc', '.docx'].includes(extension)) {
      return (
        <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (['.xls', '.xlsx'].includes(extension)) {
      return (
        <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
    
    // Default file icon
    return (
      <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
      </svg>
    );
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Root Directory</h2>
        <Link to="/files">
          <Button variant="outline" size="sm">View All</Button>
        </Link>
      </div>
      
      {loading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      ) : rootFiles.length > 0 ? (
        <div className="space-y-3">
          {rootFiles.map((file) => (
            <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="flex items-center flex-1 min-w-0">
                <div className="flex-shrink-0 mr-3">
                  {getFileIcon(file)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center">
                    {file.is_folder ? (
                      <Link
                        to="/files"
                        className="text-sm font-medium text-blue-600 hover:text-blue-800 cursor-pointer hover:underline truncate flex items-center"
                      >
                        {file.filename}
                        <svg className="w-4 h-4 ml-1 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    ) : (
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {file.filename}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 flex items-center text-xs text-gray-500">
                    <span>
                      {file.is_folder ? 'Folder' : file.file_size_formatted}
                    </span>
                    <span className="mx-2">•</span>
                    <span>
                      {new Date(file.uploaded_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
              
              {!file.is_folder && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleDownload(file)}
                  className="text-xs ml-2"
                >
                  Download
                </Button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No files or folders</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by uploading your first file or creating a folder.
          </p>
          <div className="mt-4">
            <Link to="/files">
              <Button size="sm">Go to File Manager</Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default RootDirectoryCard;
