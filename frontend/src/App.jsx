import { useState, useEffect, useCallback, useRef } from 'react'
import './App.css'

import { SunIcon, MoonIcon, CheckIcon } from './components/ui/icons'
import { getScoreColor } from './components/utils'
import { API_BASE_URL, STORAGE_KEYS, ANALYSIS_CONFIG, PROCESSING_STEPS as STEPS, PROCESSING_STEP_STATUS as STEP_STATUS, DEFAULT_WEIGHTS } from './config'
import { analyzeAudio, testAnalysis, rescore, getHistory, getStats } from './api/nanovoxApi'
import FileUpload        from './components/FileUpload'
import ProfileSelector   from './components/ProfileSelector'
import AnalysisDashboard from './components/AnalysisDashboard'

// Processing view constants managed in src/config.js

// ── App ────────────────────────────────────────────────────────────────────

function App() {
    // ── Core UI state ──
    const [file, setFile]                       = useState(null)
    const [view, setView]                       = useState('landing')
    const [processingStep, setProcessingStep]   = useState(0)
    const [result, setResult]                   = useState(null)
    const [error, setError]                     = useState(null)

    // ── Theme ──
    const [theme, setTheme] = useState(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.THEME)
        if (saved) return saved
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    })

    // ── Scoring weights ──
    const [weights, setWeights]                 = useState(() => {
        const saved = localStorage.getItem(STORAGE_KEYS.WEIGHTS)
        return saved ? JSON.parse(saved) : { ...DEFAULT_WEIGHTS }
    })
    const [analyzerResults, setAnalyzerResults] = useState(null)
    const [rescoring, setRescoring]             = useState(false)
    const rescoreTimerRef                        = useRef(null)

    // ── History ──
    const [history, setHistory]                 = useState([])
    const [stats, setStats]                     = useState(null)
    const [historyLoading, setHistoryLoading]   = useState(false)

    // ── Dev Test Mode ──
    const [isTestMode, setIsTestMode]                     = useState(false)
    const [manualTranscriptJson, setManualTranscriptJson] = useState('')

    // ── Effects ───────────────────────────────────────────────────────────

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme)
        localStorage.setItem(STORAGE_KEYS.THEME, theme)
    }, [theme])

    // Debounced rescore whenever weights change after an analysis
    useEffect(() => {
        if (!analyzerResults || !result) return
        if (rescoreTimerRef.current) clearTimeout(rescoreTimerRef.current)

        rescoreTimerRef.current = setTimeout(async () => {
            setRescoring(true)
            try {
                const newAnalysis = await rescore(analyzerResults, weights)
                setResult(prev => ({
                    ...prev,
                    analysis: { ...newAnalysis, analyzer_results: analyzerResults },
                }))
            } catch (err) {
                console.error('Rescore failed:', err)
            } finally {
                setRescoring(false)
            }
        }, ANALYSIS_CONFIG.RESCORE_DEBOUNCE_MS)

        return () => { if (rescoreTimerRef.current) clearTimeout(rescoreTimerRef.current) }
    }, [weights, analyzerResults])

    // ── Handlers ──────────────────────────────────────────────────────────

    const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0]
            if (selectedFile.size > ANALYSIS_CONFIG.MAX_AUDIO_SIZE_BYTES) {
                setError(`File is too large (${(selectedFile.size / (1024 * 1024)).toFixed(1)}MB). Maximum allowed is 50MB.`)
                setFile(null)
                return
            }
            setFile(selectedFile)
            setError(null)
        }
    }

    const handleWeightChange = useCallback((key, value) => {
        setWeights(prev => {
            const next = { ...prev, [key]: value }
            localStorage.setItem(STORAGE_KEYS.WEIGHTS, JSON.stringify(next))
            return next
        })
    }, [])

    const handleResetWeights = () => {
        setWeights({ ...DEFAULT_WEIGHTS })
        localStorage.setItem(STORAGE_KEYS.WEIGHTS, JSON.stringify(DEFAULT_WEIGHTS))
    }

    const resetToLanding = () => {
        setView('landing')
        setFile(null)
        setResult(null)
        setAnalyzerResults(null)
    }

    const fetchHistory = async () => {
        setHistoryLoading(true)
        try {
            const [histData, statsData] = await Promise.all([getHistory(), getStats()])
            setHistory(histData)
            setStats(statsData)
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

    /**
     * processCall — orchestrates the full analysis pipeline.
     * Raw fetch logic lives in api/nanovoxApi.js; this function manages
     * UI state transitions, progress steps, and error handling.
     *
     * Test Mode  → calls testAnalysis() from api/
     * Normal Mode → calls analyzeAudio() from api/
     */
    const processCall = async () => {
        setError(null)

        // ── Test Mode: POST JSON transcript directly ──
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
            setProcessingStep(3)
            setTimeout(() => setProcessingStep(4), 400)
            setTimeout(() => setProcessingStep(5), 900)

            try {
                const data = await testAnalysis(parsedTranscript, weights, 'complaints')
                if (data.analyzer_results) setAnalyzerResults(data.analyzer_results)
                setProcessingStep(6)
                setTimeout(() => {
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

        // ── Normal Mode: upload audio file ──
        if (!file) return

        setView('processing')
        setProcessingStep(1)
        setTimeout(() => setProcessingStep(2), 600)
        setTimeout(() => setProcessingStep(3), 1400)
        setTimeout(() => setProcessingStep(4), 2200)
        setTimeout(() => setProcessingStep(5), 3000)

        try {
            const data = await analyzeAudio(file, weights)
            if (data.analysis?.analyzer_results) setAnalyzerResults(data.analysis.analyzer_results)
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

    // getScoreColor is now imported from components/utils.js

    // ── Render ────────────────────────────────────────────────────────────

    return (
        <div className="app-container">

            {/* ── Global Sticky Header ── */}
            <header className="global-header">
                <div className="global-header-inner">
                    <div className="global-header-left">
                        <h1 className="brand-logo" onClick={resetToLanding}>NanoVox</h1>
                        <span className="brand-tag">Call QA</span>
                    </div>
                    <div className="global-header-right">
                        <button className="header-btn header-btn-ghost" onClick={openHistory} aria-label="View call history">
                            📊 History
                        </button>
                        <button className="header-btn header-btn-primary" onClick={resetToLanding} aria-label="Start new analysis">
                            ➕ New Analysis
                        </button>
                        <button className="theme-toggle" onClick={toggleTheme} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
                            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
                        </button>
                    </div>
                </div>
            </header>

            <main className="app-main">

                {/* ── Landing View ── */}
                {view === 'landing' && (
                    <div className="landing-view">
                        <div className="landing-hero">
                            <h2>Analyze a Complaint Call</h2>
                            <p>Upload an audio file to get AI-powered quality insights</p>
                        </div>
                        <div className="landing-columns">
                            <FileUpload
                                file={file}
                                onFileChange={handleFileChange}
                                onProcess={processCall}
                                error={error}
                                isTestMode={isTestMode}
                                onTestModeToggle={() => { setIsTestMode(m => !m); setError(null) }}
                                manualTranscriptJson={manualTranscriptJson}
                                onManualTranscriptChange={setManualTranscriptJson}
                            />
                            <ProfileSelector
                                weights={weights}
                                onWeightChange={handleWeightChange}
                                onReset={handleResetWeights}
                                disabled={false}
                            />
                        </div>
                    </div>
                )}

                {/* ── Processing View ── */}
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
                                    const stepNum    = i + 1
                                    const isCompleted = processingStep > stepNum
                                    const isActive    = processingStep === stepNum
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

                {/* ── Dashboard View ── */}
                {view === 'dashboard' && result && (
                    <AnalysisDashboard
                        analysisResult={result}
                        rescoring={rescoring}
                    />
                )}

                {/* ── History View ── */}
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
                                                    <span className="td-time">
                                                        {new Date(call.analyzed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </td>
                                                <td>
                                                    <span className="table-score" style={{ color: getScoreColor(call.final_score) }}>
                                                        {call.final_score?.toFixed(0)}
                                                    </span>
                                                </td>
                                                <td>
                                                    <span className={`commitment-pill ${
                                                        call.commitment_status === 'Resolved' ? 'status-good' :
                                                        (call.commitment_status === 'Escalated / Unresolved' || call.commitment_status === 'Ghosted/Uncommitted') ? 'status-bad' :
                                                        'status-neutral'
                                                    }`}>
                                                        {call.commitment_status || 'Unknown'}
                                                    </span>
                                                </td>
                                                <td className="td-actions">
                                                    <a href={`${API_BASE_URL}/api/history/${call.id}`} target="_blank" rel="noopener noreferrer" className="action-link" title="View detail">
                                                        👁 View
                                                    </a>
                                                    <a href={`${API_BASE_URL}/api/report/${call.id}`} target="_blank" rel="noopener noreferrer" className="action-link action-pdf" title="Download PDF">
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
