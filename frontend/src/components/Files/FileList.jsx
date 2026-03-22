import React, { useState } from 'react';
import { filesAPI } from '../../services/files';
import Button from '../UI/Button';
import toast from 'react-hot-toast';

const FileList = ({ files, onFileAction, currentFolder = '' }) => {
  const [deletingId, setDeletingId] = useState(null);

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

  const handleDelete = async (file) => {
    const confirmMessage = file.is_folder 
      ? `Are you sure you want to delete the folder "${file.filename}" and all its contents? This action cannot be undone.`
      : `Are you sure you want to delete "${file.filename}"? This action cannot be undone.`;
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setDeletingId(file.id);
    try {
      await filesAPI.delete(file.id);
      toast.success(`${file.is_folder ? 'Folder' : 'File'} deleted successfully`);
      onFileAction && onFileAction();
    } catch (error) {
      const message = error.response?.data?.error || 'Delete failed';
      toast.error(message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleShare = async (file) => {
    if (file.is_folder) {
      toast.error('Cannot share folders');
      return;
    }

    try {
      const response = await filesAPI.share(file.id);
      const shareUrl = response.data.share_url;
      
      // Copy to clipboard
      await navigator.clipboard.writeText(shareUrl);
      toast.success('Share link copied to clipboard');
    } catch (error) {
      const message = error.response?.data?.error || 'Share failed';
      toast.error(message);
    }
  };

  const handleFolderClick = (folder, e) => {
    console.log('Folder clicked:', folder);
    console.log('Folder s3_key:', folder.s3_key);
    console.log('Folder folder_path:', folder.folder_path);
    e.preventDefault();
    e.stopPropagation();
    console.log('Calling onFileAction with navigate and folder:', folder);
    onFileAction && onFileAction('navigate', folder);
  };

  const getFileIcon = (file) => {
    if (file.is_folder) {
      return (
        <svg className="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
        </svg>
      );
    }

    const extension = file.extension?.toLowerCase();
    
    if (['.pdf'].includes(extension)) {
      return (
        <svg className="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'].includes(extension)) {
      return (
        <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (['.doc', '.docx'].includes(extension)) {
      return (
        <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (['.xls', '.xlsx'].includes(extension)) {
      return (
        <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
    
    // Default file icon
    return (
      <svg className="w-6 h-6 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
      </svg>
    );
  };

  if (files.length === 0) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No files or folders</h3>
        <p className="mt-1 text-sm text-gray-500">
          {currentFolder ? 'This folder is empty.' : 'Get started by uploading your first file or creating a folder.'}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
      <ul className="divide-y divide-gray-200">
        {files.map((file) => (
          <li key={file.id}>
            <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50">
              <div className="flex items-center flex-1 min-w-0">
                <div className="flex-shrink-0 mr-4">
                  {getFileIcon(file)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center">
                    {file.is_folder ? (
                      <div
                        onClick={(e) => {
                          console.log('Folder div clicked for file:', file);
                          e.preventDefault();
                          e.stopPropagation();
                          handleFolderClick(file, e);
                        }}
                        className="text-sm font-medium truncate flex items-center text-blue-600 hover:text-blue-800 cursor-pointer hover:underline"
                        style={{ cursor: 'pointer' }}
                      >
                        {file.filename}
                        <svg className="w-4 h-4 ml-1 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    ) : (
                      <span className="text-sm font-medium truncate text-gray-900">
                        {file.filename}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 flex items-center text-sm text-gray-500">
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
              
              <div className="flex items-center space-x-2">
                {!file.is_folder && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownload(file)}
                      className="text-xs"
                    >
                      Download
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleShare(file)}
                      className="text-xs"
                    >
                      Share
                    </Button>
                  </>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleDelete(file)}
                  disabled={deletingId === file.id}
                  className="text-xs text-red-600 border-red-300 hover:bg-red-50"
                >
                  {deletingId === file.id ? 'Deleting...' : 'Delete'}
                </Button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FileList;
