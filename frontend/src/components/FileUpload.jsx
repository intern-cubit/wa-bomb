import React from 'react';
import { Upload, FileText, Image, CheckCircle, X } from 'lucide-react';

const FileUpload = ({ onFileUpload, file, acceptedTypes, title, description, icon: Icon }) => {
  const inputId = title.replace(/\s+/g, '-').toLowerCase();

  return (
    <div className="bg-white/70 backdrop-blur-sm border border-gray-200 dark:bg-[rgba(30,30,30,0.5)] dark:backdrop-blur-md dark:border dark:border-gray-800 rounded-xl p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
        <Icon className="mr-2 text-blue-600 dark:text-blue-400" size={20} />
        {title}
      </h3>
      
      <label 
        htmlFor={inputId}
        className={`relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer 
                   hover:border-blue-400 dark:hover:border-blue-500 transition-all duration-200 
                   flex flex-col justify-center items-center min-h-[120px]
                   ${file ? 'border-green-400 dark:border-green-600 bg-green-50/70 dark:bg-green-900/20' : 'border-gray-300 dark:border-gray-600'}`
        }
      >
        {file ? (
          <div className="flex flex-col items-center">
            <CheckCircle className="text-green-600 dark:text-green-400 mb-2" size={32} />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 break-all px-2">
              {file.name}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">File uploaded successfully.</span>
          </div>
        ) : (
          <>
            <Upload className="mx-auto text-gray-400 dark:text-gray-500 mb-2" size={32} />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Click to upload or drag & drop
            </span>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {description}
            </p>
          </>
        )}
        <input
          id={inputId}
          type="file"
          accept={acceptedTypes}
          onChange={onFileUpload}
          className="hidden"
        />
      </label>
      {file && (
        <button
          onClick={() => onFileUpload({ target: { files: [] } })} // Simulate clearing file input
          className="absolute top-2 right-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1 rounded-full bg-gray-100 dark:bg-gray-700"
          aria-label="Remove file"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};

export default FileUpload;