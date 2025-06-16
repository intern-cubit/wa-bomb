import React from 'react';

const TemplateSuggestions = ({ templates, onUseTemplate }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
    {templates.slice(0, 4).map((template, idx) => (
      <button
        key={idx}
        onClick={() => onUseTemplate(template.template)}
        className="p-3 text-left bg-white/70 backdrop-blur-sm border border-gray-200 dark:bg-[rgba(30,30,30,0.5)] dark:backdrop-blur-md dark:border dark:border-gray-800 rounded-lg hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md transition-all duration-200"
      >
        <div className="font-medium text-gray-800 dark:text-gray-200 text-sm">{template.name}</div>
        <div className="text-xs text-gray-600 dark:text-gray-400 truncate mt-1">{template.template}</div>
      </button>
    ))}
  </div>
);

export default TemplateSuggestions;