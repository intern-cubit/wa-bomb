import React from 'react';
import TemplateSuggestions from './TemplateSuggestions';
import VariableButtons from './VariableButtons';

const MessageTemplate = ({ message, onChange, selectedVariables, columns, onInsertVariable, templates, onUseTemplate }) => (
  <div className="space-y-4">
    {templates.length > 0 && (
      <div>
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Quick Templates</h4>
        <TemplateSuggestions templates={templates} onUseTemplate={onUseTemplate} />
      </div>
    )}
    
    {columns.length > 0 && (
      <div>
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Insert Variables</h4>
        <VariableButtons columns={columns} onInsertVariable={onInsertVariable} />
      </div>
    )}
    
    <div>
      <textarea
        placeholder="Type your message here. Use the buttons above to add personalized fields like {Name} or {Phone}."
        onChange={(e) => onChange(e.target.value)}
        value={message}
        rows={8}
        className="w-full p-4 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50/70 dark:bg-[rgba(30,30,30,0.5)] dark:backdrop-blur-sm text-gray-900 dark:text-white resize-y shadow-inner text-base"
      />
      {selectedVariables.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400 mr-1">Variables in use:</span>
          {selectedVariables.map((variable, idx) => (
            <span key={idx} className="inline-block px-2.5 py-1 bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-200 rounded-full text-xs font-medium">
              {variable}
            </span>
          ))}
        </div>
      )}
    </div>
  </div>
);

export default MessageTemplate;