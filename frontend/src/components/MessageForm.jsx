import React, { useState, useCallback, useEffect } from 'react'
import { Upload, Eye, MessageSquare, Send, FileText, Image, X, Plus } from 'lucide-react'

export default function MessageForm() {
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
    const cursorPosition = 0 // You might want to track cursor position for better UX
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
    <div className="max-w-6xl mx-auto p-6 bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
      <div className="bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">WhatsApp Message Dashboard</h1>
          <p className="text-gray-600">Send personalized messages to your contacts with ease</p>
        </div>

        <div className="space-y-8">
          {/* CSV Upload Section */}
          <div className="bg-gray-50 rounded-xl p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <FileText className="mr-2 text-blue-600" size={24} />
              Upload Contact List
            </h2>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
              <Upload className="mx-auto text-gray-400 mb-4" size={48} />
              <label className="cursor-pointer">
                <span className="text-lg font-medium text-gray-700">
                  Choose CSV File
                </span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleCsvUpload}
                  className="hidden"
                />
              </label>
              <p className="text-sm text-gray-500 mt-2">
                CSV should contain contact information with headers
              </p>
            </div>

            {csvFile && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <p className="text-green-800 font-medium">✅ File uploaded: {csvFile.name}</p>
                <p className="text-green-600 text-sm">{csvData?.length || 0} contacts found</p>
              </div>
            )}
          </div>

          {/* CSV Preview */}
          {showPreview && csvData && (
            <div className="bg-gray-50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-800 flex items-center">
                  <Eye className="mr-2 text-blue-600" size={20} />
                  CSV Preview
                </h3>
                <button
                  type="button"
                  onClick={() => setShowPreview(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X size={20} />
                </button>
              </div>
              
              <div className="overflow-x-auto bg-white rounded-lg shadow">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {csvColumns.map((column, idx) => (
                        <th key={idx} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {csvData.slice(0, 5).map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        {csvColumns.map((column, colIdx) => (
                          <td key={colIdx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {row[column] || '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {csvData.length > 5 && (
                  <div className="px-6 py-3 bg-gray-50 text-sm text-gray-500">
                    Showing 5 of {csvData.length} rows
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Template Section */}
          {csvColumns.length > 0 && (
            <div className="bg-gray-50 rounded-xl p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
                <MessageSquare className="mr-2 text-blue-600" size={24} />
                Create Message Template
              </h2>

              {/* Template Suggestions */}
              {templateSuggestions.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-700 mb-3">Smart Templates (Based on Your Data)</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {templateSuggestions.map((template, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => useTemplate(template.template)}
                        className="p-3 text-left bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all"
                      >
                        <div className="font-medium text-gray-800">{template.name}</div>
                        <div className="text-sm text-gray-600 truncate">{template.template}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Variable Buttons */}
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-700 mb-3">Available Variables</h3>
                <div className="flex flex-wrap gap-2">
                  {csvColumns.map((column, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => insertVariable(column)}
                      className="px-3 py-2 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors flex items-center"
                    >
                      <Plus className="mr-1" size={16} />
                      {column}
                    </button>
                  ))}
                </div>
              </div>

              {/* Message Template Textarea */}
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-2">
                  Message Template
                </label>
                <textarea
                  placeholder="Type your message here. Click variable buttons above to insert personalized fields."
                  onChange={(e) => setMessage(e.target.value)}
                  value={message}
                  rows={6}
                  className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                />
                {selectedVariables.length > 0 && (
                  <div className="mt-2">
                    <span className="text-sm text-gray-600">Using variables: </span>
                    {selectedVariables.map((variable, idx) => (
                      <span key={idx} className="inline-block px-2 py-1 bg-green-100 text-green-800 rounded text-sm mr-2">
                        {variable}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Media Upload */}
          <div className="bg-gray-50 rounded-xl p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
              <Image className="mr-2 text-blue-600" size={24} />
              Optional Media Attachment
            </h2>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
              <label className="cursor-pointer">
                <Upload className="mx-auto text-gray-400 mb-4" size={32} />
                <span className="text-lg font-medium text-gray-700">
                  Choose Media File (Optional)
                </span>
                <input
                  type="file"
                  onChange={(e) => setMediaFile(e.target.files[0])}
                  className="hidden"
                />
              </label>
              <p className="text-sm text-gray-500 mt-2">
                Images, videos, or documents to send with each message
              </p>
            </div>

            {mediaFile && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <p className="text-green-800 font-medium">✅ Media file: {mediaFile.name}</p>
              </div>
            )}
          </div>

          {/* Send Button */}
          <div className="text-center">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!csvFile || !message}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xl font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center mx-auto"
            >
              <Send className="mr-2" size={24} />
              Send Messages
            </button>
          </div>

          {/* Status Messages */}
          {status && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 font-medium">{status}</p>
            </div>
          )}
          
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 font-medium">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}