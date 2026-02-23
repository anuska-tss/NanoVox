import { useState, useEffect } from 'react'
import './App.css'

// Icons
const UploadIcon = () => (
    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" strokeLinejoin="round" />
        <polyline points="17 8 12 3 7 8" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="12" y1="3" x2="12" y2="15" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
)

const FileIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
    </svg>
)

const CheckIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
        <polyline points="20 6 9 17 4 12" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
)

function App() {
    const [file, setFile] = useState(null)
    const [view, setView] = useState('landing') // landing, processing, dashboard
    const [processingStep, setProcessingStep] = useState(0) // 0-4
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0])
            setError(null)
        }
    }

    const formatSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    const processCall = async () => {
        if (!file) return;

        setView('processing')
        setProcessingStep(1) // Uploading

        const formData = new FormData()
        formData.append('file', file)

        try {
            // Simulate steps for visual effect
            setTimeout(() => setProcessingStep(2), 1000) // Transcribing
            setTimeout(() => setProcessingStep(3), 2500) // Analyzing Sentiment

            const response = await fetch('http://127.0.0.1:8000/analyze', {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) throw new Error('Analysis failed')

            const data = await response.json()

            setProcessingStep(4) // Generating Insights
            setTimeout(() => {
                setResult(data)
                setView('dashboard')
            }, 1000)

        } catch (err) {
            setError(err.message)
            setView('landing')
        }
    }

    // Calculate percentage for donut chart (using frustration as inverse of positive or sentiment score)
    // Backend returns: customer_frustration (0-10). 
    // Let's assume: 0 frustration = 100% Positive. 10 frustration = 0% Positive.
    // Actually, let's use the sentiment label from backend if available, or map frustration.
    // The mock shows "78% Positive".
    const getPositivePercent = () => {
        if (!result) return 0;
        // Map frustration (0-10) to Positive %
        // 0 -> 100%, 5 -> 50%, 10 -> 0%
        const score = Math.max(0, 10 - (result.customer_frustration || 0));
        return Math.round((score / 10) * 100);
    }

    return (
        <div className="app-container">

            {/* 1. Landing Page View */}
            {view === 'landing' && (
                <div className="landing-view">
                    <header className="main-header">
                        <h1>Call Intelligence Dashboard</h1>
                        <p>Analyze call sentiment, resolution status, and agent performance</p>
                    </header>

                    <div className="upload-card">
                        <div className="upload-area">
                            <UploadIcon />
                            <h3>Upload Audio File</h3>
                            <p className="upload-hint">Drag and drop your audio file or click to browse</p>
                            <p className="supported-formats">Supported formats: .wav, .mp3</p>

                            <input
                                type="file"
                                id="file-upload"
                                className="hidden-input"
                                accept=".wav,.mp3,.m4a,.ogg"
                                onChange={handleFileChange}
                            />
                            <label htmlFor="file-upload" className="choose-btn">Choose File</label>
                        </div>

                        {file && (
                            <div className="file-preview">
                                <div className="file-info-row">
                                    <div className="file-icon-wrapper"><FileIcon /></div>
                                    <div className="file-details">
                                        <span className="filename">{file.name}</span>
                                        <span className="filesize">{formatSize(file.size)}</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {file && (
                            <button className="process-btn" onClick={processCall}>
                                Process Call
                            </button>
                        )}
                    </div>
                    {error && <div className="error-toast">{error}</div>}
                </div>
            )}

            {/* 2. Processing Overlay */}
            {view === 'processing' && (
                <div className="processing-view">
                    <div className="processing-card">
                        <div className="spinner-container">
                            <div className="spinner"></div>
                        </div>
                        <h2>Processing Call Analysis</h2>
                        <p className="processing-status">
                            {processingStep === 1 && "Uploading..."}
                            {processingStep === 2 && "Transcribing..."}
                            {processingStep === 3 && "Analyzing Sentiment..."}
                            {processingStep === 4 && "Generating Insights..."}
                        </p>

                        <div className="progress-bar-container">
                            <div className="progress-bar" style={{ width: `${processingStep * 25}%` }}></div>
                        </div>

                        <div className="steps-container">
                            <div className={`step-item ${processingStep > 1 ? 'completed' : 'active'}`}>
                                <div className="step-circle">{processingStep > 1 ? <CheckIcon /> : 1}</div>
                                <span>Uploading</span>
                            </div>
                            <div className={`step-item ${processingStep > 2 ? 'completed' : (processingStep === 2 ? 'active' : '')}`}>
                                <div className="step-circle">{processingStep > 2 ? <CheckIcon /> : 2}</div>
                                <span>Transcribing</span>
                            </div>
                            <div className={`step-item ${processingStep > 3 ? 'completed' : (processingStep === 3 ? 'active' : '')}`}>
                                <div className="step-circle">{processingStep > 3 ? <CheckIcon /> : 3}</div>
                                <span>Analyzing Sentiment</span>
                            </div>
                            <div className={`step-item ${processingStep === 4 ? 'active' : ''}`}>
                                <div className="step-circle">4</div>
                                <span>Generating Insights</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 3. Dashboard View */}
            {view === 'dashboard' && result && (
                <div className="dashboard-view">
                    <header className="dashboard-header">
                        <h1>Call Intelligence Dashboard</h1>
                        <p>Analyze call sentiment, resolution status, and agent performance</p>
                    </header>

                    {/* Transcript Section */}
                    <div className="transcript-section">
                        <div className="transcript-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h3>Transcript</h3>
                            <button
                                onClick={() => {
                                    if (!result?.transcription?.transcript) return;
                                    const text = result.transcription.transcript
                                        .map(seg => `[${Math.floor(seg.start / 60)}:${Math.floor(seg.start % 60).toString().padStart(2, '0')}] ${seg.speaker}: ${seg.text}`)
                                        .join('\n\n');
                                    const blob = new Blob([text], { type: 'text/plain' });
                                    const url = URL.createObjectURL(blob);
                                    const a = document.createElement('a');
                                    a.href = url;
                                    a.download = `transcript-${new Date().toISOString().slice(0, 10)}.txt`;
                                    document.body.appendChild(a);
                                    a.click();
                                    document.body.removeChild(a);
                                    URL.revokeObjectURL(url);
                                }}
                                className="process-btn"
                                style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', width: 'auto' }}
                            >
                                Save Transcript
                            </button>
                        </div>
                        <div className="transcript-container">
                            {result.transcription && result.transcription.transcript && result.transcription.transcript.map((seg, idx) => (
                                <div key={idx} className={`chat-bubble-row ${seg.speaker.toLowerCase()}`}>
                                    <div className="speaker-avatar">
                                        {seg.speaker === 'Customer' ? 'C' : 'A'}
                                    </div>
                                    <div className="chat-bubble">
                                        <p>{seg.text}</p>
                                        <div className="bubble-meta">
                                            <span className="timestamp">
                                                {Math.floor(seg.start / 60)}:{Math.floor(seg.start % 60).toString().padStart(2, '0')}
                                            </span>
                                            {/* Placeholder confidence/sentiment since segment-level sentiment isn't stored yet */}
                                            <span className="meta-tag">{(seg.speaker === 'Customer' && result.insights.customer_frustration > 5) ? 'Negative' : 'Neutral'}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Metrics Grid */}
                    <div className="metrics-grid">

                        {/* Left Card: Overall Sentiment */}
                        <div className="metric-card sentiment-card">
                            <h3>Overall Sentiment</h3>
                            <div className="donut-chart-wrapper">
                                <div className="donut-chart" style={{
                                    background: `conic-gradient(#22c55e 0% ${getPositivePercent()}%, #374151 ${getPositivePercent()}% 100%)`
                                }}>
                                    <div className="donut-hole">
                                        <span className="donut-percent">{getPositivePercent()}%</span>
                                        <span className="donut-label">Positive</span>
                                    </div>
                                </div>
                            </div>
                            <div className="chart-legend">
                                <div className="legend-item"><span className="dot negative"></span>Negative</div>
                                <div className="legend-item"><span className="dot neutral"></span>Neutral</div>
                                <div className="legend-item"><span className="dot positive"></span>Positive</div>
                            </div>
                        </div>

                        {/* Right Card: Call Summary */}
                        <div className="metric-card summary-card">
                            <h3>Call Summary</h3>
                            <div className="summary-grid">
                                <div className="summary-item">
                                    <label>Resolution Status</label>
                                    <span className="summary-value white">
                                        {result.insights.call_resolution ? 'Resolved' : 'Unresolved'}
                                    </span>
                                </div>
                                <div className="summary-item">
                                    <label>Transcript Length</label>
                                    <span className="summary-value white">
                                        {result.transcription.transcript ? result.transcription.transcript.length : 0} exchanges
                                    </span>
                                </div>
                                <div className="summary-item">
                                    <label>Avg Sentiment</label>
                                    <span className="summary-value blue">{getPositivePercent()}%</span>
                                </div>
                                <div className="summary-item">
                                    <label>Coaching Tips</label>
                                    <span className="summary-value white">3 items</span>
                                </div>
                            </div>
                        </div>

                    </div>

                    {/* Re-upload Area (Mock show it at the bottom too) */}
                    <div className="upload-card small-upload">
                        <div className="upload-area sm">
                            <UploadIcon />
                            <h3>Upload Audio File</h3>
                            <p className="upload-hint">Drag and drop your audio file or click to browse</p>
                            <label htmlFor="file-upload-2" className="choose-btn">Choose File</label>
                            <input type="file" id="file-upload-2" className="hidden-input" onChange={handleFileChange} />
                        </div>
                    </div>

                </div>
            )}

        </div>
    )
}

export default App
