import React from 'react';
import { Eye, X } from 'lucide-react';

const CSVPreview = ({ data, columns, onClose }) => {
  if (!data || !columns) return null;
  
  return (
    <div className="bg-white/70 backdrop-blur-sm border border-gray-200 dark:bg-[rgba(30,30,30,0.5)] dark:backdrop-blur-md dark:border dark:border-gray-800 rounded-xl overflow-hidden shadow-md">
      <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50/70 dark:bg-[rgba(30,30,30,0.5)]">
        <h3 className="text-md font-semibold text-gray-900 dark:text-white flex items-center">
          <Eye className="mr-2 text-blue-600 dark:text-blue-400" size={16} />
          Contact Preview (First 3 Rows)
        </h3>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          aria-label="Close preview"
        >
          <X size={16} />
        </button>
      </div>
      
      <div className="overflow-x-auto max-h-48">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50/70 dark:bg-[rgba(30,30,30,0.5)] sticky top-0">
            <tr>
              {columns.slice(0, 4).map((column, idx) => (
                <th key={idx} className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white/70 dark:bg-transparent divide-y divide-gray-200 dark:divide-gray-700">
            {data.slice(0, 3).map((row, idx) => (
              <tr key={idx}>
                {columns.slice(0, 4).map((column, colIdx) => (
                  <td key={colIdx} className="px-4 py-2 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                    {row[column] || '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CSVPreview;