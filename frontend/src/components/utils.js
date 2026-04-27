import { DEFAULT_WEIGHTS as CONFIG_WEIGHTS, UI_COLORS, SCORE_THRESHOLDS } from '../config'

export const DEFAULT_WEIGHTS = CONFIG_WEIGHTS

export const PARAM_INFO = {
    talk_ratio: { label: 'Talk Ratio', icon: '🗣️' },
    sentiment:  { label: 'Sentiment',  icon: '🎭' },
    empathy:    { label: 'Empathy',    icon: '🤝' },
    resolution: { label: 'Resolution Status', icon: '✅' },
}

/**
 * Format a byte count into a human-readable string (e.g. "1.4 MB").
 */
export const formatSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

/**
 * Return a hex colour based on a 0–100 score.
 */
export const getScoreColor = (score) => {
    if (score >= SCORE_THRESHOLDS.STRONG) return UI_COLORS.SUCCESS
    if (score >= SCORE_THRESHOLDS.POOR)   return UI_COLORS.WARNING
    return UI_COLORS.DANGER
}

/**
 * Return a short text label for a 0–100 score.
 */
export const getScoreLabel = (score) => {
    if (score >= SCORE_THRESHOLDS.STRONG) return 'Strong'
    if (score >= SCORE_THRESHOLDS.FAIR)   return 'Fair'
    return 'Needs Work'
}
