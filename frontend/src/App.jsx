import { useState, useEffect, useCallback, useRef } from 'react'
import './App.css'

const SunIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
)

const MoonIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
)

const UploadIcon = () => (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" strokeLinejoin="round" />
        <polyline points="17 8 12 3 7 8" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="12" y1="3" x2="12" y2="15" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
)

const FileIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
    </svg>
)

const CheckIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <polyline points="20 6 9 17 4 12" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
)

const InfoIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
)

const ChevronIcon = ({ open }) => (
    <svg
        width="14" height="14" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1.5"
        style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
        aria-hidden="true"
    >
        <polyline points="6 9 12 15 18 9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
)

const DEFAULT_WEIGHTS = { talk_ratio: 5, sentiment: 30, empathy: 15, resolution: 50 }

const PARAM_INFO = {
    talk_ratio: { label: 'Talk Ratio', icon: '🗣️' },
    sentiment: { label: 'Sentiment', icon: '🎭' },
    empathy: { label: 'Empathy', icon: '🤝' },
    resolution: { label: 'Resolution Status', icon: '✅' },
}

const formatSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getScoreColor = (score) => {
    if (score >= 80) return 'var(--success)'
    if (score >= 60) return 'var(--warning)'
    return 'var(--danger)'
}

const getScoreLabel = (score) => {
    if (score >= 80) return 'Strong'
    if (score >= 60) return 'Fair'
    return 'Needs Work'
}

const CircularGauge = ({ score }) => {
    const radius = 44
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (score / 100) * circumference

    return (
        <div className="gauge-wrapper" role="img" aria-label={`Score: ${score.toFixed(1)} out of 100`}>
            <svg width="100%" height="100%" viewBox="0 0 100 100">
                <defs>
                    <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="var(--gradient-start)" />
                        <stop offset="100%" stopColor="var(--gradient-end)" />
                    </linearGradient>
                </defs>
                <circle cx="50" cy="50" r={radius} fill="none" stroke="var(--bg-surface)" strokeWidth="6" />
                <circle
                    cx="50" cy="50" r={radius}
                    fill="none"
                    stroke="url(#gaugeGradient)"
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    transform="rotate(-90 50 50)"
                    style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
                />
            </svg>
            <div className="gauge-center">
                <span className="gauge-score">{score.toFixed(0)}</span>
                <span className="gauge-label">{getScoreLabel(score)}</span>
            </div>
        </div>
    )
}

const ScoreCard = ({ analysis }) => {
    if (!analysis || analysis.error) {
        return (
            <div className="score-card">
                <div className="score-card-error">
                    <span>Scoring data unavailable</span>
                    {analysis?.message && <p>{analysis.message}</p>}
                </div>
            </div>
        )
    }

    const { final_score, profile_used, interpretation } = analysis

    return (
        <div className="score-card">
            <div className="score-card-header">
                <div>
                    <h3>Call Quality</h3>
                    <span className="profile-badge">{profile_used}</span>
                </div>
                <CircularGauge score={final_score} />
            </div>
            <hr className="score-divider" />
            {interpretation && (
                <p className="score-interpretation">{interpretation}</p>
            )}
        </div>
    )
}

const ParameterCard = ({ paramKey, param }) => {
    const [expanded, setExpanded] = useState(false)
    const color = getScoreColor(param.score)

    const contextText = param.metadata?.context_text || `Score: ${param.score.toFixed(0)}/100`
    const phrases = param.metadata?.detected_phrases || []
    const sentimentImproved = param.metadata?.sentiment_improved
    const status = param.metadata?.status

    return (
        <div
            className="param-card"
            onClick={() => setExpanded(e => !e)}
            role="button"
            aria-expanded={expanded}
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && setExpanded(e => !e)}
        >
            <div className="param-card-header">
                <div className="param-icon-title">
                    <span className="param-icon" aria-hidden="true">{param.icon}</span>
                    <span className="param-name">{param.display_name}</span>
                </div>
                <ChevronIcon open={expanded} />
            </div>

            <p className="param-context">{contextText}</p>

            <div className="param-score-row">
                <span className="param-score-num" style={{ color }}>{param.score.toFixed(0)}</span>
                <div className="param-score-bar-bg">
                    <div
                        className="param-score-bar-fill"
                        style={{ width: `${param.score}%`, background: color }}
                    />
                </div>
            </div>

            <div className="param-footer">
                <span>Weight {param.weight.toFixed(0)}%</span>
                <span style={{ color: param.contribution < -10 ? 'var(--danger)' : undefined }}>
                    {param.contribution > 0 ? '+' : ''}{param.contribution.toFixed(1)}
                </span>
            </div>

            {expanded && (
                <div className="param-detail" onClick={e => e.stopPropagation()}>
                    <hr className="param-detail-divider" />

                    {phrases.length > 0 && (
                        <div className="param-detail-section">
                            <span className="param-detail-label">Detected</span>
                            <div className="phrase-tags">
                                {phrases.map((p, i) => (
                                    <span key={i} className="phrase-tag">{p}</span>
                                ))}
                            </div>
                        </div>
                    )}

                    {sentimentImproved !== undefined && (
                        <div className="param-detail-section">
                            <span className="param-detail-label">Sentiment</span>
                            <span className={`journey-badge ${sentimentImproved ? 'improved' : 'flat'}`}>
                                {sentimentImproved ? 'Improved' : 'No change'}
                            </span>
                        </div>
                    )}

                    {status && (
                        <div className="param-detail-section">
                            <span className="param-detail-label">Outcome</span>
                            <span className="outcome-text">{status}</span>
                        </div>
                    )}

                    <div className="param-detail-section">
                        <span className="param-detail-label">Raw</span>
                        <span className="param-detail-value">{param.raw_value.toFixed(2)}</span>
                    </div>
                    <div className="param-detail-section">
                        <span className="param-detail-label">Penalty</span>
                        <span className="param-detail-value" style={{ color: param.penalty > 30 ? 'var(--warning)' : undefined }}>
                            {param.penalty.toFixed(1)}
                        </span>
                    </div>

                    {param.metadata?.phrase_count_high !== undefined && (
                        <div className="phrase-counts">
                            <span className="count-item high">High {param.metadata.phrase_count_high}</span>
                            <span className="count-item med">Med {param.metadata.phrase_count_medium}</span>
                            <span className="count-item low">Low {param.metadata.phrase_count_low}</span>
                            {param.metadata.negative_phrases_detected > 0 && (
                                <span className="count-item neg">Neg {param.metadata.negative_phrases_detected}</span>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

const WeightSliders = ({ weights, onChange, disabled }) => {
    const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0)

    return (
        <div className="weight-sliders">
            <div className="weight-sliders-header">
                <h3>Weight Configuration</h3>
                <span className="weight-total">Total: {totalWeight}</span>
            </div>
            <p className="weight-hint">Adjust how much each parameter affects the final score. Weights are auto-normalized.</p>
            <div className="slider-grid">
                {Object.entries(weights).map(([key, value]) => {
                    const info = PARAM_INFO[key] || { label: key, icon: '•' }
                    const normalized = totalWeight > 0 ? Math.round((value / totalWeight) * 100) : 0
                    return (
                        <div key={key} className="slider-item">
                            <div className="slider-label-row">
                                <span className="slider-icon">{info.icon}</span>
                                <span className="slider-label">{info.label}</span>
                                <span className="slider-value">{value} <span className="slider-pct">({normalized}%)</span></span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={value}
                                onChange={e => onChange(key, parseInt(e.target.value))}
                                className="weight-slider"
                                disabled={disabled}
                                aria-label={`${info.label} weight`}
                            />
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

function App() {
    const [file, setFile] = useState(null)
    const [view, setView] = useState('landing')
    const [processingStep, setProcessingStep] = useState(0)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [theme, setTheme] = useState(() => {
        const saved = localStorage.getItem('nanovox_theme')
        if (saved) return saved
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    })

    const [weights, setWeights] = useState(() => {
        // Always use Complaints defaults; ignore any stale Sales weights in storage
        return { ...DEFAULT_WEIGHTS }
    })
    const [analyzerResults, setAnalyzerResults] = useState(null)
    const [rescoring, setRescoring] = useState(false)
    const rescoreTimerRef = useRef(null)

    // History state
    const [history, setHistory] = useState([])
    const [stats, setStats] = useState(null)
    const [historyLoading, setHistoryLoading] = useState(false)

    // Developer Test Mode
    const [isTestMode, setIsTestMode] = useState(false)
    const [manualTranscriptJson, setManualTranscriptJson] = useState('')

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme)
        localStorage.setItem('nanovox_theme', theme)
    }, [theme])

    const toggleTheme = () => {
        setTheme(t => t === 'dark' ? 'light' : 'dark')
    }

    const fetchHistory = async () => {
        setHistoryLoading(true)
        try {
            const [histRes, statsRes] = await Promise.all([
                fetch('http://localhost:8000/api/history?limit=20'),
                fetch('http://localhost:8000/api/stats')
            ])
            if (histRes.ok) setHistory(await histRes.json())
            if (statsRes.ok) setStats(await statsRes.json())
        } catch (e) {
            console.error('Failed to fetch history:', e)
        } finally {
            setHistoryLoading(false)
        }
    }

    const openHistory = () => {
        setView('history')
        fetchHistory()
    }

    const handleWeightChange = useCallback((key, value) => {
        setWeights(prev => {
            const next = { ...prev, [key]: value }
            localStorage.setItem('nanovox_weights', JSON.stringify(next))
            return next
        })
    }, [])

    // Debounced rescore when weights change
    useEffect(() => {
        if (!analyzerResults || !result) return
        if (rescoreTimerRef.current) clearTimeout(rescoreTimerRef.current)

        rescoreTimerRef.current = setTimeout(async () => {
            setRescoring(true)
            try {
                const resp = await fetch('http://127.0.0.1:8000/api/rescore', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ analyzer_results: analyzerResults, weights })
                })
                if (resp.ok) {
                    const newAnalysis = await resp.json()
                    if (!newAnalysis.error) {
                        setResult(prev => ({
                            ...prev,
                            analysis: { ...newAnalysis, analyzer_results: analyzerResults }
                        }))
                    }
                }
            } catch (err) {
                console.error('Rescore failed:', err)
            } finally {
                setRescoring(false)
            }
        }, 300)

        return () => { if (rescoreTimerRef.current) clearTimeout(rescoreTimerRef.current) }
    }, [weights, analyzerResults])

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0])
            setError(null)
        }
    }

    const processCall = async () => {
        setError(null)

        // ── Test Mode: POST JSON transcript directly to /api/test-analysis ──
        if (isTestMode) {
            if (!manualTranscriptJson.trim()) {
                setError('Please paste a JSON transcript before analyzing.')
                return
            }
            let parsedTranscript
            try {
                parsedTranscript = JSON.parse(manualTranscriptJson)
            } catch {
                setError('Invalid JSON — please check the transcript format and try again.')
                return
            }
            if (!Array.isArray(parsedTranscript) || parsedTranscript.length === 0) {
                setError('Transcript must be a non-empty JSON array of segment objects.')
                return
            }

            setView('processing')
            setProcessingStep(3) // skip Upload + Transcribe steps visually
            setTimeout(() => setProcessingStep(4), 400)
            setTimeout(() => setProcessingStep(5), 900)

            try {
                const response = await fetch('http://127.0.0.1:8000/api/test-analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        transcript: parsedTranscript,
                        weights,
                        profile: 'complaints',
                    }),
                })
                if (!response.ok) throw new Error('Test analysis request failed.')
                const data = await response.json()
                if (data.error) throw new Error(data.message || data.error)

                if (data.analyzer_results) setAnalyzerResults(data.analyzer_results)

                setProcessingStep(6)
                setTimeout(() => {
                    // Shape the response to match the dashboard expectations
                    setResult({
                        filename: 'manual-transcript.json',
                        file_size_bytes: manualTranscriptJson.length,
                        transcription: { text: '', transcript: parsedTranscript },
                        insights: {},
                        analysis: data,
                    })
                    setView('dashboard')
                }, 400)
            } catch (err) {
                setError(err.message)
                setView('landing')
            }
            return
        }

        // ── Normal Mode: upload audio file → /analyze ──
        if (!file) return

        setView('processing')
        setProcessingStep(1)

        const formData = new FormData()
        formData.append('file', file)
        formData.append('weights', JSON.stringify(weights))

        try {
            setTimeout(() => setProcessingStep(2), 600)
            setTimeout(() => setProcessingStep(3), 1400)
            setTimeout(() => setProcessingStep(4), 2200)
            setTimeout(() => setProcessingStep(5), 3000)

            const response = await fetch('http://127.0.0.1:8000/analyze', {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) throw new Error('Analysis failed. Please try again.')

            const data = await response.json()

            // Store raw analyzer results for rescoring
            if (data.analysis?.analyzer_results) {
                setAnalyzerResults(data.analysis.analyzer_results)
            }

            setProcessingStep(6)
            setTimeout(() => {
                setResult(data)
                setView('dashboard')
            }, 500)

        } catch (err) {
            setError(err.message)
            setView('landing')
        }
    }

    const getPositivePercent = () => {
        if (!result?.analysis?.breakdown?.sentiment) return 0
        return Math.round(result.analysis.breakdown.sentiment.score)
    }

    const STEPS = [
        { label: 'Upload' },
        { label: 'Transcribe' },
        { label: 'Sentiment' },
        { label: 'Analyze' },
        { label: 'Score' },
        { label: 'Done' },
    ]

    const STEP_STATUS = [
        '',
        'Uploading audio...',
        'Transcribing audio...',
        'Analyzing sentiment...',
        'Processing parameters...',
        'Calculating score...',
        'Complete',
    ]

    return (
        <div className="app-container">
            {/* ── Global Sticky Header ── */}
            <header className="global-header">
                <div className="global-header-inner">
                    <div className="global-header-left">
                        <h1 className="brand-logo" onClick={() => { setView('landing'); setFile(null); setResult(null); setAnalyzerResults(null) }}>
                            NanoVox
                        </h1>
                        <span className="brand-tag">Call QA</span>
                    </div>
                    <div className="global-header-right">
                        <button className="header-btn header-btn-ghost" onClick={openHistory} aria-label="View call history">
                            📊 History
                        </button>
                        <button className="header-btn header-btn-primary" onClick={() => { setView('landing'); setFile(null); setResult(null); setAnalyzerResults(null) }} aria-label="Start new analysis">
                            ➕ New Analysis
                        </button>
                        <button className="theme-toggle" onClick={toggleTheme} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
                            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
                        </button>
                    </div>
                </div>
            </header>

            <main className="app-main">

                {view === 'landing' && (
                    <div className="landing-view">
                        <div className="landing-hero">
                            <h2>Analyze a Complaint Call</h2>
                            <p>Upload an audio file to get AI-powered quality insights</p>
                        </div>

                        <div className="landing-columns">
                            {/* ── Upload Card ── */}
                            <div className="upload-card glass-card">

                                {/* Mode toggle */}
                                <div className="test-mode-toggle">
                                    <span className="test-mode-label">🧪 Dev Test Mode</span>
                                    <button
                                        id="test-mode-btn"
                                        className={`toggle-switch ${isTestMode ? 'active' : ''}`}
                                        onClick={() => { setIsTestMode(m => !m); setError(null) }}
                                        aria-pressed={isTestMode}
                                        aria-label="Toggle developer test mode"
                                    >
                                        <span className="toggle-knob" />
                                    </button>
                                </div>

                                {isTestMode ? (
                                    /* ── Test Mode: JSON textarea ── */
                                    <div className="json-input-wrapper">
                                        <textarea
                                            id="json-transcript-input"
                                            className="json-textarea glass-card"
                                            value={manualTranscriptJson}
                                            onChange={e => setManualTranscriptJson(e.target.value)}
                                            placeholder={`Paste your JSON transcript array here...\n\nExample:\n[\n  { "speaker": "Agent", "start": 0.0, "end": 4.0, "text": "How can I help?" },\n  { "speaker": "Customer", "start": 4.2, "end": 9.0, "text": "My order is broken!" }\n]`}
                                            aria-label="JSON transcript input"
                                            rows={10}
                                            spellCheck={false}
                                        />
                                        <p className="json-hint">Array of <code>{'{speaker, start, end, text}'}</code> objects</p>
                                    </div>
                                ) : (
                                    /* ── Normal Mode: file uploader ── */
                                    <>
                                        <div className="upload-area" role="button" tabIndex={0}
                                            onClick={() => document.getElementById('file-upload').click()}
                                            onKeyDown={e => e.key === 'Enter' && document.getElementById('file-upload').click()}>
                                            <UploadIcon aria-hidden="true" />
                                            <h3>Upload Audio</h3>
                                            <p className="upload-hint">Drop your file or click to browse</p>
                                            <p className="supported-formats">WAV, MP3, M4A, OGG</p>
                                            <input
                                                type="file"
                                                id="file-upload"
                                                className="hidden-input"
                                                accept=".wav,.mp3,.m4a,.ogg"
                                                onChange={handleFileChange}
                                                aria-label="Upload audio file"
                                            />
                                        </div>

                                        {file && (
                                            <div className="file-preview">
                                                <div className="file-info-row">
                                                    <div className="file-icon-wrapper"><FileIcon aria-hidden="true" /></div>
                                                    <div className="file-details">
                                                        <span className="filename">{file.name}</span>
                                                        <span className="filesize">{formatSize(file.size)}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </>
                                )}

                                <div className="landing-profile-badge">
                                    <span className="profile-badge-icon">🎧</span>
                                    <span>Complaints Profile</span>
                                </div>

                                {(isTestMode ? manualTranscriptJson.trim() : file) && (
                                    <button
                                        id="process-call-btn"
                                        className="process-btn"
                                        onClick={processCall}
                                        aria-label="Start call analysis"
                                    >
                                        {isTestMode ? '🧪 Run Test Analysis' : 'Analyze'}
                                    </button>
                                )}
                            </div>

                            {/* ── Weight Configuration ── */}
                            <div className="weight-config-panel glass-card">
                                <WeightSliders
                                    weights={weights}
                                    onChange={handleWeightChange}
                                    disabled={false}
                                />
                            </div>
                        </div>

                        {error && <div className="error-toast" role="alert">{error}</div>}
                    </div>
                )}

                {view === 'processing' && (
                    <div className="processing-view" role="status" aria-live="polite">
                        <div className="processing-card">
                            <div className="spinner-container">
                                <div className="spinner" aria-hidden="true"></div>
                            </div>
                            <h2>Processing</h2>
                            <p className="processing-status">{STEP_STATUS[processingStep]}</p>

                            <div className="progress-bar-container">
                                <div className="progress-bar" style={{ width: `${(processingStep / 6) * 100}%` }}></div>
                            </div>

                            <div className="steps-container">
                                {STEPS.map((step, i) => {
                                    const stepNum = i + 1
                                    const isCompleted = processingStep > stepNum
                                    const isActive = processingStep === stepNum
                                    return (
                                        <div key={step.label} className={`step-item ${isCompleted ? 'completed' : isActive ? 'active' : ''}`}>
                                            <div className="step-circle">
                                                {isCompleted ? <CheckIcon /> : stepNum}
                                            </div>
                                            <span>{step.label}</span>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {view === 'dashboard' && result && (
                    <div className="dashboard-view">
                        <div className="dashboard-subtitle">
                            <h2>Analysis Results</h2>
                            <p>Call quality breakdown for <strong>{result.filename}</strong></p>
                        </div>

                        {result.analysis && (
                            <div className="analysis-section">
                                <ScoreCard analysis={result.analysis} />

                                {rescoring && <div className="rescore-indicator">Recalculating...</div>}

                                {result.analysis.breakdown && Object.keys(result.analysis.breakdown).length > 0 && (
                                    <div className="param-breakdown">
                                        <h2 className="breakdown-title">Parameters</h2>
                                        <div className="param-grid">
                                            {Object.entries(result.analysis.breakdown).map(([key, param]) => (
                                                <ParameterCard key={key} paramKey={key} param={param} />
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="transcript-section">
                            <div className="transcript-header">
                                <h3>Transcript</h3>
                                <button
                                    id="save-transcript-btn"
                                    onClick={() => {
                                        if (!result?.transcription?.transcript) return
                                        const text = result.transcription.transcript
                                            .map(seg => `[${Math.floor(seg.start / 60)}:${Math.floor(seg.start % 60).toString().padStart(2, '0')}] ${seg.speaker}: ${seg.text}`)
                                            .join('\n\n')
                                        const blob = new Blob([text], { type: 'text/plain' })
                                        const url = URL.createObjectURL(blob)
                                        const a = document.createElement('a')
                                        a.href = url
                                        a.download = `transcript-${new Date().toISOString().slice(0, 10)}.txt`
                                        document.body.appendChild(a)
                                        a.click()
                                        document.body.removeChild(a)
                                        URL.revokeObjectURL(url)
                                    }}
                                    className="save-btn"
                                    aria-label="Download transcript"
                                >
                                    Export
                                </button>
                            </div>
                            <div className="transcript-container">
                                {result.transcription?.transcript?.map((seg, idx) => (
                                    <div key={idx} className={`chat-bubble-row ${seg.speaker.toLowerCase()}`}>
                                        <div className="speaker-avatar" aria-label={seg.speaker}>
                                            {seg.speaker === 'Customer' ? 'C' : 'A'}
                                        </div>
                                        <div className="chat-bubble">
                                            <p>{seg.text}</p>
                                            <div className="bubble-meta">
                                                <span className="timestamp">
                                                    {Math.floor(seg.start / 60)}:{Math.floor(seg.start % 60).toString().padStart(2, '0')}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="metrics-grid">
                            <div className="metric-card sentiment-card">
                                <h3>Sentiment</h3>
                                <div className="donut-chart-wrapper">
                                    <div className="donut-chart" style={{
                                        background: `conic-gradient(var(--gradient-start) 0% ${getPositivePercent()}%, var(--bg-surface) ${getPositivePercent()}% 100%)`
                                    }}>
                                        <div className="donut-hole">
                                            <span className="donut-percent">{getPositivePercent()}%</span>
                                            <span className="donut-label">Positive</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="chart-legend">
                                    <div className="legend-item"><span className="dot positive" aria-hidden="true"></span>Positive</div>
                                    <div className="legend-item"><span className="dot neutral" aria-hidden="true"></span>Neutral</div>
                                </div>
                            </div>

                            <div className="metric-card summary-card">
                                <h3>Summary</h3>
                                <div className="summary-grid">
                                    <div className="summary-item">
                                        <label>Resolution Status</label>
                                        <span className="summary-value">
                                            {result.analysis?.breakdown?.resolution?.metadata?.status || 'Unknown'}
                                        </span>
                                    </div>
                                    <div className="summary-item">
                                        <label>Exchanges</label>
                                        <span className="summary-value">
                                            {result.transcription?.transcript?.length || 0}
                                        </span>
                                    </div>
                                    <div className="summary-item">
                                        <label>Sentiment</label>
                                        <span className="summary-value blue">{getPositivePercent()}%</span>
                                    </div>
                                    <div className="summary-item">
                                        <label>Score</label>
                                        <span
                                            className="summary-value"
                                            style={{ color: result.analysis?.final_score ? getScoreColor(result.analysis.final_score) : undefined }}
                                        >
                                            {result.analysis?.final_score ? result.analysis.final_score.toFixed(0) : '—'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                )}

                {view === 'history' && (
                    <div className="history-view">
                        <div className="history-topbar">
                            <h2>Call History</h2>
                            <button className="refresh-btn" onClick={fetchHistory} disabled={historyLoading}>
                                {historyLoading ? '⏳' : '🔄 Refresh'}
                            </button>
                        </div>

                        {stats && stats.total_calls > 0 && (
                            <div className="stats-strip">
                                <div className="strip-stat">
                                    <span className="strip-val">{stats.total_calls}</span>
                                    <span className="strip-lbl">Calls</span>
                                </div>
                                <div className="strip-divider" />
                                <div className="strip-stat">
                                    <span className="strip-val" style={{ color: getScoreColor(stats.avg_score || 0) }}>
                                        {stats.avg_score ?? '—'}
                                    </span>
                                    <span className="strip-lbl">Avg Score</span>
                                </div>
                                <div className="strip-divider" />
                                <div className="strip-stat">
                                    <span className="strip-val" style={{ color: 'var(--success)' }}>
                                        {stats.committed_count || 0}
                                    </span>
                                    <span className="strip-lbl">Resolved</span>
                                </div>
                                <div className="strip-divider" />
                                <div className="strip-stat">
                                    <span className="strip-val" style={{ color: 'var(--danger)' }}>
                                        {stats.ghosted_count || 0}
                                    </span>
                                    <span className="strip-lbl">Escalated</span>
                                </div>
                            </div>
                        )}

                        <div className="data-table-wrapper">
                            {historyLoading && <p className="history-loading">Loading history...</p>}
                            {!historyLoading && history.length === 0 && (
                                <p className="history-empty">No calls analyzed yet. Upload a call to get started.</p>
                            )}
                            {!historyLoading && history.length > 0 && (
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Filename</th>
                                            <th>Date</th>
                                            <th>Score</th>
                                            <th>Resolution</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {history.map(call => (
                                            <tr key={call.id}>
                                                <td className="td-filename">
                                                    <span className="file-icon-sm">🎵</span>
                                                    {call.filename}
                                                </td>
                                                <td className="td-date">
                                                    {new Date(call.analyzed_at).toLocaleDateString()}
                                                    <span className="td-time">{new Date(call.analyzed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                </td>
                                                <td>
                                                    <span className="table-score" style={{ color: getScoreColor(call.final_score) }}>
                                                        {call.final_score?.toFixed(0)}
                                                    </span>
                                                </td>
                                                <td>
                                                    <span className={`commitment-pill ${call.commitment_status === 'Resolved' ? 'status-good' :
                                                        (call.commitment_status === 'Escalated / Unresolved' || call.commitment_status === 'Ghosted/Uncommitted') ? 'status-bad' :
                                                            'status-neutral'
                                                        }`}>
                                                        {call.commitment_status || 'Unknown'}
                                                    </span>
                                                </td>
                                                <td className="td-actions">
                                                    <a href={`http://localhost:8000/api/history/${call.id}`} target="_blank" rel="noopener noreferrer" className="action-link" title="View detail">
                                                        👁 View
                                                    </a>
                                                    <a href={`http://localhost:8000/api/report/${call.id}`} target="_blank" rel="noopener noreferrer" className="action-link action-pdf" title="Download PDF">
                                                        📄 PDF
                                                    </a>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                )}

            </main>
        </div>
    )
}

export default App
