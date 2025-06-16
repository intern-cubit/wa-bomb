import React, { useState, useCallback, useEffect, createContext, useContext } from 'react'
import { Upload, Eye, MessageSquare, Send, FileText, Image, X, Plus, Moon, Sun, Users, Zap, CheckCircle } from 'lucide-react'

// Theme Context
const ThemeContext = createContext()

const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

// Theme Provider Component
const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(false)
  
  const toggleTheme = () => setIsDark(!isDark)
  
  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme }}>
      <div className={isDark ? 'dark' : ''}>
        {children}
      </div>
    </ThemeContext.Provider>
  )
}

// Header Component
const Header = () => {
  const { isDark, toggleTheme } = useTheme()
  
  return (
    <header className="flex justify-between items-center mb-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
          WhatsApp Campaign Manager
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Create, personalize, and send messages in minutes
        </p>
      </div>
      <button
        onClick={toggleTheme}
        className="p-3 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
      >
        {isDark ? <Sun className="text-yellow-500" size={20} /> : <Moon className="text-gray-600" size={20} />}
      </button>
    </header>
  )
}

// Stats Component
const StatsCard = ({ icon: Icon, label, value, color }) => (
  <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
    <div className="flex items-center">
      <div className={`p-2 rounded-lg ${color} mr-3`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
        <p className="text-xl font-semibold text-gray-900 dark:text-white">{value}</p>
      </div>
    </div>
  </div>
)

// File Upload Component
const FileUpload = ({ onFileUpload, file, acceptedTypes, title, description, icon: Icon }) => {
  return (
    <div className="h-full">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
        <Icon className="mr-2 text-blue-600 dark:text-blue-400" size={20} />
        {title}
      </h3>
      
      <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-6 text-center hover:border-blue-400 dark:hover:border-blue-500 transition-colors h-32 flex flex-col justify-center">
        <label className="cursor-pointer">
          <Upload className="mx-auto text-gray-400 dark:text-gray-500 mb-2" size={32} />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {file ? file.name : 'Choose File'}
          </span>
          <input
            type="file"
            accept={acceptedTypes}
            onChange={onFileUpload}
            className="hidden"
          />
        </label>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {description}
        </p>
      </div>
    </div>
  )
}

// CSV Preview Component
const CSVPreview = ({ data, columns, onClose }) => {
  if (!data || !columns) return null
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <Eye className="mr-2 text-blue-600 dark:text-blue-400" size={18} />
          Contact Preview
        </h3>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <X size={18} />
        </button>
      </div>
      
      <div className="overflow-x-auto max-h-48">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              {columns.slice(0, 4).map((column, idx) => (
                <th key={idx} className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
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
  )
}

// Template Suggestions Component
const TemplateSuggestions = ({ templates, onUseTemplate }) => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
    {templates.slice(0, 4).map((template, idx) => (
      <button
        key={idx}
        onClick={() => onUseTemplate(template.template)}
        className="p-3 text-left bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-500 hover:shadow-md transition-all"
      >
        <div className="font-medium text-gray-800 dark:text-gray-200 text-sm">{template.name}</div>
        <div className="text-xs text-gray-600 dark:text-gray-400 truncate mt-1">{template.template}</div>
      </button>
    ))}
  </div>
)

// Variable Buttons Component
const VariableButtons = ({ columns, onInsertVariable }) => (
  <div className="flex flex-wrap gap-2">
    {columns.map((column, idx) => (
      <button
        key={idx}
        onClick={() => onInsertVariable(column)}
        className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors flex items-center text-sm"
      >
        <Plus className="mr-1" size={14} />
        {column}
      </button>
    ))}
  </div>
)

// Message Template Component
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
        placeholder="Type your message here. Use the buttons above to add personalized fields."
        onChange={(e) => onChange(e.target.value)}
        value={message}
        rows={6}
        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
      />
      {selectedVariables.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {selectedVariables.map((variable, idx) => (
            <span key={idx} className="inline-block px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded text-xs">
              {variable}
            </span>
          ))}
        </div>
      )}
    </div>
  </div>
)

// Main Dashboard Component
function Dashboard() {
  const [message, setMessage] = useState("")
  const [csvFile, setCsvFile] = useState(null)
  const [csvData, setCsvData] = useState(null)
  const [csvColumns, setCsvColumns] = useState([])
  const [mediaFile, setMediaFile] = useState(null)
  const [status, setStatus] = useState("")
  const [error, setError] = useState("")
  const [showPreview, setShowPreview] = useState(false)
  const [selectedVariables, setSelectedVariables] = useState([])

  // Generate dynamic templates based on CSV columns
  const generateTemplates = (columns) => {
    const hasName = columns.some(col => col.toLowerCase().includes('name'))
    const hasEmail = columns.some(col => col.toLowerCase().includes('email'))
    const hasPhone = columns.some(col => col.toLowerCase().includes('phone'))
    const hasCompany = columns.some(col => col.toLowerCase().includes('company'))
    const hasCity = columns.some(col => col.toLowerCase().includes('city'))
    
    const nameVar = columns.find(col => col.toLowerCase().includes('name')) || columns[0]
    const emailVar = columns.find(col => col.toLowerCase().includes('email'))
    const phoneVar = columns.find(col => col.toLowerCase().includes('phone'))
    const companyVar = columns.find(col => col.toLowerCase().includes('company'))
    const cityVar = columns.find(col => col.toLowerCase().includes('city'))

    const templates = []

    // Personal Greeting
    if (hasName) {
      templates.push({
        name: "Personal Greeting",
        template: `Hi {${nameVar}}! Hope you're doing well. I wanted to reach out to you about something exciting!`
      })
    }

    // Business Introduction
    if (hasName && hasCompany) {
      templates.push({
        name: "Business Introduction",
        template: `Hello {${nameVar}}, I'm reaching out to introduce our new service that could benefit {${companyVar}}.`
      })
    } else if (hasName) {
      templates.push({
        name: "Business Introduction",
        template: `Hello {${nameVar}}, I'm reaching out to introduce our new service that could benefit you.`
      })
    }

    // Location-based outreach
    if (hasName && hasCity) {
      templates.push({
        name: "Location-based Outreach",
        template: `Hi {${nameVar}}! I noticed you're in {${cityVar}}. We have some exciting opportunities in your area!`
      })
    }

    // Follow Up
    if (hasName) {
      templates.push({
        name: "Follow Up",
        template: `Hey {${nameVar}}, just following up on our previous conversation. Let me know your thoughts!`
      })
    }

    // Event Invitation
    if (hasName && hasCity) {
      templates.push({
        name: "Event Invitation",
        template: `Hi {${nameVar}}! You're invited to our special event in {${cityVar}}. Would love to see you there!`
      })
    } else if (hasName) {
      templates.push({
        name: "Event Invitation",
        template: `Hi {${nameVar}}! You're invited to our special event. Would love to see you there!`
      })
    }

    // Contact verification
    if (hasName && hasEmail) {
      templates.push({
        name: "Contact Verification",
        template: `Hi {${nameVar}}, just wanted to confirm that {${emailVar}} is still the best way to reach you.`
      })
    }

    // Default fallback
    if (templates.length === 0) {
      templates.push({
        name: "General Message",
        template: `Hello! I wanted to reach out to you about something important.`
      })
    }

    return templates
  }

  // Update selected variables when message changes
  useEffect(() => {
    const variables = message.match(/\{([^}]+)\}/g)?.map(v => v.slice(1, -1)) || []
    setSelectedVariables(variables)
  }, [message])

  const handleCsvUpload = useCallback(async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError("Please upload a CSV file")
      return
    }

    setCsvFile(file)
    setError("")

    try {
      const formData = new FormData()
      formData.append('csv_file', file)
      
      const response = await fetch('http://localhost:8000/preview-csv', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to process CSV')
      }

      const result = await response.json()
      setCsvData(result.preview)
      setCsvColumns(result.columns)
      setShowPreview(true)
    } catch (err) {
      setError("Failed to process CSV file: " + err.message)
    }
  }, [])

  const insertVariable = (variable) => {
    const newVar = `{${variable}}`
    setMessage(prev => prev + newVar)
  }

  const useTemplate = (template) => {
    setMessage(template)
  }

  const handleSubmit = async () => {
    setStatus("")
    setError("")

    if (!message || !csvFile) {
      setError("Please provide both a message template and a CSV file.")
      return
    }

    if (selectedVariables.length === 0) {
      setError("Please select at least one variable to personalize your message.")
      return
    }

    const formData = new FormData()
    formData.append("message", message)
    formData.append("csv_file", csvFile)
    formData.append("variables", JSON.stringify(selectedVariables))
    
    if (mediaFile) {
      formData.append("media_file", mediaFile)
    }

    try {
      setStatus("Processing and sending messages...")
      const response = await fetch("http://localhost:8000/send-messages", {
        method: "POST",
        body: formData
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || "Server responded with an error.")
      }

      const result = await response.json()
      setStatus("✅ " + (result.detail || "All messages sent successfully!"))
    } catch (err) {
      console.error(err)
      setError("❌ " + err.message)
    }
  }

  const templateSuggestions = csvColumns.length > 0 ? generateTemplates(csvColumns) : []

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <div className="max-w-7xl mx-auto p-6">
        <Header />
        
        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatsCard icon={Users} label="Contacts" value={csvData?.length || 0} color="bg-blue-500" />
          <StatsCard icon={MessageSquare} label="Variables" value={selectedVariables.length} color="bg-green-500" />
          <StatsCard icon={Zap} label="Status" value={status ? "Ready" : "Setup"} color="bg-purple-500" />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-280px)]">
          {/* Left Column - File Uploads */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <FileUpload
                title="Contact List"
                description="CSV with contact information"
                icon={FileText}
                file={csvFile}
                acceptedTypes=".csv"
                onFileUpload={handleCsvUpload}
              />
            </div>
            
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <FileUpload
                title="Media (Optional)"
                description="Images, videos, or documents"
                icon={Image}
                file={mediaFile}
                acceptedTypes="*"
                onFileUpload={(e) => setMediaFile(e.target.files[0])}
              />
            </div>

            {/* CSV Preview */}
            {showPreview && csvData && (
              <CSVPreview 
                data={csvData} 
                columns={csvColumns} 
                onClose={() => setShowPreview(false)} 
              />
            )}
          </div>

          {/* Center Column - Message Template */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <MessageSquare className="mr-2 text-blue-600 dark:text-blue-400" size={20} />
              Message Template
            </h3>
            
            <MessageTemplate
              message={message}
              onChange={setMessage}
              selectedVariables={selectedVariables}
              columns={csvColumns}
              onInsertVariable={insertVariable}
              templates={templateSuggestions}
              onUseTemplate={useTemplate}
            />
          </div>

          {/* Right Column - Actions & Status */}
          <div className="space-y-6">
            {/* Send Button */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <button
                onClick={handleSubmit}
                disabled={!csvFile || !message}
                className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-lg font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center justify-center"
              >
                <Send className="mr-2" size={20} />
                Send Messages
              </button>
            </div>

            {/* Status Messages */}
            {status && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4">
                <div className="flex items-center">
                  <CheckCircle className="text-green-600 dark:text-green-400 mr-2" size={20} />
                  <p className="text-green-800 dark:text-green-200 font-medium">{status}</p>
                </div>
              </div>
            )}
            
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
                <div className="flex items-center">
                  <X className="text-red-600 dark:text-red-400 mr-2" size={20} />
                  <p className="text-red-800 dark:text-red-200 font-medium">{error}</p>
                </div>
              </div>
            )}

            {/* Help Text */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
              <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Quick Guide</h4>
              <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                <li>1. Upload your CSV contact list</li>
                <li>2. Choose a template or write your own</li>
                <li>3. Add variables to personalize</li>
                <li>4. Send your campaign!</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <Dashboard />
    </ThemeProvider>
  )
}