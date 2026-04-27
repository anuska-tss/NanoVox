import { useState } from 'react'
import { ChevronIcon } from './ui/icons'
import { getScoreColor } from './utils'
import ScoreCard from './ui/ScoreCard'

// ── ParameterCard — private to this module ─────────────────────────────────
// Renders an expandable card for a single scoring parameter.

const ParameterCard = ({ paramKey, param }) => {
    const [expanded, setExpanded] = useState(false)
    const color = getScoreColor(param.score)

    const contextText       = param.metadata?.context_text || `Score: ${param.score.toFixed(0)}/100`
    const phrases           = param.metadata?.detected_phrases || []
    const sentimentImproved = param.metadata?.sentiment_improved
    const status            = param.metadata?.status

    return (
        <div
            className="param-card"
            onClick={() => setExpanded(e => !e)}
            role="button"
            aria-expanded={expanded}
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && setExpanded(e => !e)}
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
                                {phrases.map((p, i) => <span key={i} className="phrase-tag">{p}</span>)}
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

// ── Helpers ────────────────────────────────────────────────────────────────

const getPositivePercent = (analysisResult) => {
    if (!analysisResult?.analysis?.breakdown?.sentiment) return 0
    return Math.round(analysisResult.analysis.breakdown.sentiment.score)
}

const handleExportTranscript = (analysisResult) => {
    if (!analysisResult?.transcription?.transcript) return
    const text = analysisResult.transcription.transcript
        .map(seg =>
            `[${Math.floor(seg.start / 60)}:${Math.floor(seg.start % 60).toString().padStart(2, '0')}] ${seg.speaker}: ${seg.text}`
        )
        .join('\n\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `transcript-${new Date().toISOString().slice(0, 10)}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
}

// ── Main export ────────────────────────────────────────────────────────────

/**
 * AnalysisDashboard — full results view rendered after a call is analyzed.
 *
 * Props:
 *   analysisResult — the full API response object (result state from App.jsx)
 *   rescoring      — boolean, shows "Recalculating..." indicator when true
 */
export default function AnalysisDashboard({ analysisResult, rescoring }) {
    if (!analysisResult) return null

    const positivePercent = getPositivePercent(analysisResult)

    return (
        <div className="dashboard-view">
            <div className="dashboard-subtitle">
                <h2>Analysis Results</h2>
                <p>Call quality breakdown for <strong>{analysisResult.filename}</strong></p>
            </div>

            {/* ── Score + Parameter Breakdown ── */}
            {analysisResult.analysis && (
                <div className="analysis-section">
                    <ScoreCard analysis={analysisResult.analysis} />

                    {rescoring && <div className="rescore-indicator">Recalculating...</div>}

                    {analysisResult.analysis.breakdown &&
                        Object.keys(analysisResult.analysis.breakdown).length > 0 && (
                            <div className="param-breakdown">
                                <h2 className="breakdown-title">Parameters</h2>
                                <div className="param-grid">
                                    {Object.entries(analysisResult.analysis.breakdown).map(([key, param]) => (
                                        <ParameterCard key={key} paramKey={key} param={param} />
                                    ))}
                                </div>
                            </div>
                        )}
                </div>
            )}

            {/* ── Transcript ── */}
            <div className="transcript-section">
                <div className="transcript-header">
                    <h3>Transcript</h3>
                    <button
                        id="save-transcript-btn"
                        onClick={() => handleExportTranscript(analysisResult)}
                        className="save-btn"
                        aria-label="Download transcript"
                    >
                        Export
                    </button>
                </div>
                <div className="transcript-container">
                    {analysisResult.transcription?.transcript?.map((seg, idx) => (
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

            {/* ── Metrics Grid ── */}
            <div className="metrics-grid">
                <div className="metric-card sentiment-card">
                    <h3>Sentiment</h3>
                    <div className="donut-chart-wrapper">
                        <div className="donut-chart" style={{
                            background: `conic-gradient(var(--gradient-start) 0% ${positivePercent}%, var(--bg-surface) ${positivePercent}% 100%)`
                        }}>
                            <div className="donut-hole">
                                <span className="donut-percent">{positivePercent}%</span>
                                <span className="donut-label">Positive</span>
                            </div>
                        </div>
                    </div>
                    <div className="chart-legend">
                        <div className="legend-item"><span className="dot positive" aria-hidden="true"></span>Positive</div>
                        <div className="legend-item"><span className="dot neutral"  aria-hidden="true"></span>Neutral</div>
                    </div>
                </div>

                <div className="metric-card summary-card">
                    <h3>Summary</h3>
                    <div className="summary-grid">
                        <div className="summary-item">
                            <label>Resolution Status</label>
                            <span className="summary-value">
                                {analysisResult.analysis?.breakdown?.resolution?.metadata?.status || 'Unknown'}
                            </span>
                        </div>
                        <div className="summary-item">
                            <label>Exchanges</label>
                            <span className="summary-value">
                                {analysisResult.transcription?.transcript?.length || 0}
                            </span>
                        </div>
                        <div className="summary-item">
                            <label>Sentiment</label>
                            <span className="summary-value blue">{positivePercent}%</span>
                        </div>
                        <div className="summary-item">
                            <label>Score</label>
                            <span
                                className="summary-value"
                                style={{ color: analysisResult.analysis?.final_score ? getScoreColor(analysisResult.analysis.final_score) : undefined }}
                            >
                                {analysisResult.analysis?.final_score ? analysisResult.analysis.final_score.toFixed(0) : '—'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
