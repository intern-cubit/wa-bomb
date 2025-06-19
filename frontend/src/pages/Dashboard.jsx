import React, { useState, useCallback, useEffect } from 'react';
import { MessageSquare, Send, FileText, Image, Users, Zap, CheckCircle, X, Info, Loader2 } from 'lucide-react'; // Import Loader2 for spinner

import Header from '../components/Header';
import StatsCard from '../components/StatsCard';
import FileUpload from '../components/FileUpload';
import CSVPreview from '../components/CSVPreview';
import MessageTemplate from '../components/MessageTemplate';
import UpdateStatus from '../components/UpdateStatus';

function Dashboard() {
    const [message, setMessage] = useState("");
    const [csvFile, setCsvFile] = useState(null);
    const [csvData, setCsvData] = useState(null); // This holds the preview data (first 3 rows)
    const [csvColumns, setCsvColumns] = useState([]);
    const [mediaFile, setMediaFile] = useState(null);
    const [status, setStatus] = useState(""); // For informative messages (processing, success)
    const [error, setError] = useState(""); // For error messages
    const [isLoading, setIsLoading] = useState(false); // New state for loading indicator
    const [showPreview, setShowPreview] = useState(false);
    const [selectedVariables, setSelectedVariables] = useState([]);

    // Generate dynamic templates based on CSV columns (logic unchanged)
    const generateTemplates = (columns) => {
        const hasName = columns.some(col => col.toLowerCase().includes('name') || col.toLowerCase().includes('fullname'));
        const hasEmail = columns.some(col => col.toLowerCase().includes('email'));
        const hasPhone = columns.some(col => col.toLowerCase().includes('phone') || col.toLowerCase().includes('mobile'));
        const hasCompany = columns.some(col => col.toLowerCase().includes('company'));
        const hasCity = columns.some(col => col.toLowerCase().includes('city'));

        // Attempt to find common variable names, prioritizing 'fullName' or 'name'
        const nameVar = columns.find(col => col.toLowerCase().includes('fullname')) || columns.find(col => col.toLowerCase().includes('name')) || columns[0];
        const emailVar = columns.find(col => col.toLowerCase().includes('email'));
        const phoneVar = columns.find(col => col.toLowerCase().includes('phone')) || columns.find(col => col.toLowerCase().includes('mobile'));
        const companyVar = columns.find(col => col.toLowerCase().includes('company'));
        const cityVar = columns.find(col => col.toLowerCase().includes('city'));

        const templates = [];

        if (hasName) {
            templates.push({
                name: "Personal Greeting",
                template: `Hi {${nameVar}}! Hope you're doing well. I wanted to reach out to you about something exciting!`,
            });
        }
        if (hasName && hasCompany) {
            templates.push({
                name: "Business Introduction",
                template: `Hello {${nameVar}}, I'm reaching out to introduce our new service that could benefit {${companyVar}}.`,
            });
        } else if (hasName) {
            templates.push({
                name: "Business Introduction",
                template: `Hello {${nameVar}}, I'm reaching out to introduce our new service that could benefit you.`,
            });
        }
        if (hasName && hasCity) {
            templates.push({
                name: "Location-based Outreach",
                template: `Hi {${nameVar}}! I noticed you're in {${cityVar}}. We have some exciting opportunities in your area!`,
            });
        }
        if (hasName) {
            templates.push({
                name: "Follow Up",
                template: `Hey {${nameVar}}, just following up on our previous conversation. Let me know your thoughts!`,
            });
        }
        if (hasName && hasCity) {
            templates.push({
                name: "Event Invitation",
                template: `Hi {${nameVar}}! You're invited to our special event in {${cityVar}}. Would love to see you there!`,
            });
        } else if (hasName) {
            templates.push({
                name: "Event Invitation",
                template: `Hi {${nameVar}}! You're invited to our special event. Would love to see you there!`,
            });
        }
        if (hasName && hasEmail) {
            templates.push({
                name: "Contact Verification",
                template: `Hi {${nameVar}}, just wanted to confirm that {${emailVar}} is still the best way to reach you.`,
            });
        }
        if (templates.length === 0) {
            templates.push({
                name: "General Message",
                template: `Hello! I wanted to reach out to you about something important.`,
            });
        }
        return templates;
    };

    // Update selected variables when message changes
    useEffect(() => {
        const variables = message.match(/\{([^}]+)\}/g)?.map(v => v.slice(1, -1)) || [];
        setSelectedVariables(variables);
    }, [message]);

    const handleCsvUpload = useCallback(async (e) => {
        console.log("handleCsvUpload triggered."); // DEBUG: Log when handler starts
        const file = e.target.files[0];

        // CRITICAL: Clear the input's value to allow re-uploading the same file
        // This makes sure the onChange event fires even if the exact same file is chosen again.
        e.target.value = null;

        setError(""); // Always clear previous errors when starting a new upload
        setStatus(""); // Clear previous status
        setIsLoading(true); // Set loading true while processing CSV

        if (!file) {
            setCsvFile(null); // Clear file state if no file selected
            setCsvData(null);
            setCsvColumns([]);
            setShowPreview(false);
            setIsLoading(false); // Stop loading
            console.log("No CSV file selected. Clearing state."); // DEBUG
            return;
        }

        if (!file.name.toLowerCase().endsWith('.csv')) {
            setError("Please upload a CSV file (e.g., contacts.csv).");
            setCsvFile(null);
            setCsvData(null);
            setCsvColumns([]);
            setShowPreview(false);
            setIsLoading(false); // Stop loading
            console.log("Invalid file type selected:", file.name); // DEBUG
            return;
        }

        console.log("CSV File selected:", file.name); // DEBUG: Log selected file name
        setCsvFile(file);
        setStatus("Processing CSV file...");
        setShowPreview(false); // Hide old preview while processing new file

        try {
            const formData = new FormData();
            formData.append('csv_file', file);

            console.log("Sending request to /preview-csv..."); // DEBUG: Log before fetch
            const response = await fetch('http://localhost:8000/preview-csv', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error("Backend /preview-csv error:", errorData); // DEBUG: Log backend error response
                throw new Error(errorData.detail || 'Failed to process CSV. Please check file format.');
            }

            const result = await response.json();
            console.log("CSV Preview Data from Backend:", result); // DEBUG: Log successful response
            setCsvData(result.preview);
            setCsvColumns(result.columns);
            setShowPreview(true);
            setStatus(`CSV processed. ${result.total_rows} contacts found.`); // Use total_rows from backend
            // Auto-select 'phone' variable if available in columns
            if (result.columns.some(col => col.toLowerCase() === 'phone' || col.toLowerCase() === 'mobile')) {
                const phoneCol = result.columns.find(col => col.toLowerCase() === 'phone' || col.toLowerCase() === 'mobile');
                setSelectedVariables(prev => (prev.includes(phoneCol) ? prev : [...prev, phoneCol]));
            }
        } catch (err) {
            console.error("Error during CSV preview fetch:", err); // DEBUG: Log network or other JS errors
            setError("Error processing CSV: " + err.message);
            setCsvFile(null);
            setCsvData(null);
            setCsvColumns([]);
            setShowPreview(false);
            setStatus(""); // Clear status on error
        } finally {
            setIsLoading(false); // Always stop loading, whether success or error
        }
    }, []); // Empty dependency array means this function is created once

    const handleMediaUpload = useCallback((e) => {
        console.log("handleMediaUpload triggered."); // DEBUG
        const file = e.target.files[0];
        setMediaFile(file || null); // Set null if no file selected
        // CRITICAL: Clear the input's value to allow re-uploading the same file
        e.target.value = null;
        if (file) {
            console.log("Media File selected:", file.name); // DEBUG
        } else {
            console.log("No media file selected. Clearing state."); // DEBUG
        }
    }, []);

    const insertVariable = (variable) => {
        const newVar = `{${variable}}`;
        const textarea = document.querySelector('textarea'); // Consider using a ref for more reliable access
        if (textarea) {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const newText = message.substring(0, start) + newVar + message.substring(end);
            setMessage(newText);
            // Optional: Set cursor after inserted variable
            setTimeout(() => {
                textarea.selectionStart = textarea.selectionEnd = start + newVar.length;
                textarea.focus();
            }, 0);
        } else {
            setMessage(prev => prev + newVar);
        }
    };

    const useTemplate = (template) => {
        setMessage(template);
    };

    const handleSubmit = async () => {
        setError(""); // Clear previous errors
        setStatus(""); // Clear previous status
        setIsLoading(true); // Set loading true when sending campaign

        if (!csvFile) {
            setError("Please upload your Contact List (CSV) first.");
            setIsLoading(false); // Stop loading on validation error
            return;
        }
        if (!message.trim()) {
            setError("Your message template cannot be empty.");
            setIsLoading(false); // Stop loading on validation error
            return;
        }
        // Ensure 'phone' or similar is present in columns based on current CSV
        if (!csvColumns.some(col => col.toLowerCase().includes('phone') || col.toLowerCase().includes('mobile'))) {
            setError("Your CSV file must contain a 'phone' or 'mobile' column for sending messages.");
            setIsLoading(false); // Stop loading on validation error
            return;
        }
        // Check if message contains variables but none are selected, if it's a personalized message
        if (message.includes('{') && selectedVariables.length === 0) {
            setError("Your message contains variables but none are recognized. Ensure your CSV has matching columns.");
            setIsLoading(false); // Stop loading on validation error
            return;
        }

        const formData = new FormData();
        formData.append("message", message);
        formData.append("csv_file", csvFile);
        formData.append("variables", JSON.stringify(selectedVariables));

        if (mediaFile) {
            formData.append("media_file", mediaFile);
        }

        try {
            setStatus("Sending campaign... This may take a while. Please do not close this window.");
            console.log("Sending request to /send-messages..."); // DEBUG
            const response = await fetch("http://localhost:8000/send-messages", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const data = await response.json();
                console.error("Backend /send-messages error:", data); // DEBUG
                throw new Error(data.detail || "Server responded with an error.");
            }

            const result = await response.json();
            console.log("Campaign Send Success:", result); // DEBUG
            setStatus("✅ Success! " + (result.detail || `Campaign sent to ${csvData?.length || 'all'} contacts!`));

            // Reset form after successful send to allow new campaign to be setup cleanly
            setMessage("");
            setCsvFile(null);
            setCsvData(null);
            setCsvColumns([]);
            setMediaFile(null);
            setShowPreview(false);
            setSelectedVariables([]);
        } catch (err) {
            console.error("Submission error:", err); // DEBUG
            setError("❌ Failed to send campaign: " + err.message);
            setStatus(""); // Clear status on error
        } finally {
            setIsLoading(false); // Always stop loading, whether success or error
        }
    };

    const templateSuggestions = csvColumns.length > 0 ? generateTemplates(csvColumns) : [];

    return (
        <div className="min-h-screen">
            <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
                <UpdateStatus />

                {/* Main Dashboard Content Area */}
                <div className="bg-white/70 backdrop-blur-sm border border-gray-200 dark:bg-[rgba(30,30,30,0.5)] dark:backdrop-blur-md dark:border dark:border-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-8 lg:space-y-0 lg:grid lg:grid-cols-12 lg:gap-8">

                    {/* Left Section: File Uploads & Preview (col-span-4 or 5) */}
                    <div className="lg:col-span-5 flex flex-col space-y-6">
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                            <span className="text-blue-600 dark:text-blue-400">1.</span> Audience & Media
                        </h2>
                        <FileUpload
                            title="Contact List (CSV)"
                            description="Upload your contacts. Must contain a 'phone' or 'mobile' column."
                            icon={FileText}
                            file={csvFile}
                            acceptedTypes=".csv"
                            onFileUpload={handleCsvUpload}
                        />

                        <FileUpload
                            title="Media Attachment (Optional)"
                            description="Attach an image, video, or document."
                            icon={Image}
                            file={mediaFile}
                            acceptedTypes="image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx"
                            onFileUpload={handleMediaUpload}
                        />

                        {/* Always show CSVPreview component, but it will render nothing if showPreview is false */}
                        {showPreview && csvData && (
                            <CSVPreview
                                data={csvData}
                                columns={csvColumns}
                                onClose={() => {
                                    setShowPreview(false);
                                    setCsvData(null); // Also clear the data when closing the preview
                                    setCsvColumns([]); // Clear columns too
                                    setCsvFile(null); // Optionally clear the file from the upload component
                                    setStatus(""); // Clear status related to CSV processing
                                    setError(""); // Clear any errors related to CSV processing
                                }}
                            />
                        )}
                        {/* Quick Guide in this section */}
                        <div className="bg-blue-50/70 backdrop-blur-sm border border-blue-200 dark:bg-blue-900/20 dark:border-blue-800 rounded-xl p-4">
                            <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2 flex items-center">
                                <Info className="mr-2" size={18} /> Quick Guide
                            </h4>
                            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1 list-disc pl-5">
                                <li>Upload your CSV contact list (phone numbers are essential!).</li>
                                <li>Optionally, attach media like images or PDFs.</li>
                                <li>Preview contacts to ensure data accuracy.</li>
                            </ul>
                        </div>
                    </div>

                    {/* Right Section: Message Template, Stats, Send (col-span-7 or 8) */}
                    <div className="lg:col-span-7 flex flex-col space-y-6">
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                            <span className="text-blue-600 dark:text-blue-400">2.</span> Craft & Send Campaign
                        </h2>
                        <div className="bg-white/70 backdrop-blur-sm border border-gray-200 dark:bg-[rgba(30,30,30,0.5)] dark:backdrop-blur-md dark:border dark:border-gray-800 rounded-xl p-6 shadow-sm">
                            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                                <MessageSquare className="mr-3 text-blue-600 dark:text-blue-400" size={24} />
                                Personalized Message Template
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

                        {/* Stats Summary - now positioned below message */}
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <StatsCard icon={Users} label="Contacts Loaded" value={csvData?.length || 0} color="bg-blue-600" />
                            <StatsCard icon={MessageSquare} label="Variables Used" value={selectedVariables.length} color="bg-indigo-600" />
                            <StatsCard
                                icon={Zap}
                                label="Campaign Status"
                                value={isLoading ? "In Progress..." : (error ? "Error" : (status.startsWith("✅") ? "Sent!" : "Ready"))}
                                color={isLoading ? "bg-yellow-600" : (error ? "bg-red-600" : (status.startsWith("✅") ? "bg-green-600" : "bg-gray-500"))}
                            />
                        </div>

                        {/* Status & Error Messages */}
                        {(status || error) && (
                            <div className={`rounded-xl p-4 transition-all duration-300 ease-in-out transform scale-100 
                  ${error ? 'bg-red-50/70 dark:bg-red-900/20 border border-red-200 dark:border-red-800' :
                                    (status.startsWith("✅") ? 'bg-green-50/70 dark:bg-green-900/20 border border-green-200 dark:border-green-800' :
                                        'bg-blue-50/70 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800') // Default for informational status
                                }`}>
                                <div className="flex items-center">
                                    {error ? <X className="text-red-600 dark:text-red-400 mr-2" size={20} /> :
                                        (status.startsWith("✅") ? <CheckCircle className="text-green-600 dark:text-green-400 mr-2" size={20} /> :
                                            <Info className="text-blue-600 dark:text-blue-400 mr-2" size={20} />)} {/* Info icon for general status */}
                                    <p className={`font-medium 
                          ${error ? 'text-red-800 dark:text-red-200' :
                                            (status.startsWith("✅") ? 'text-green-800 dark:text-green-200' :
                                                'text-blue-800 dark:text-blue-200') // Default for informational status
                                        }`}>
                                        {error || status}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Send Button */}
                        <button
                            onClick={handleSubmit}
                            disabled={isLoading || !csvFile || !message.trim() || (message.includes('{') && selectedVariables.length === 0)}
                            className="w-full px-6 py-4 bg-gradient-to-r from-teal-500 to-green-600 text-white text-xl font-bold rounded-xl hover:from-teal-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl flex items-center justify-center transform hover:-translate-y-0.5"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-3 animate-spin" size={24} />
                                    Sending Campaign...
                                </>
                            ) : (
                                <>
                                    <Send className="mr-3" size={24} />
                                    Send Campaign
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;