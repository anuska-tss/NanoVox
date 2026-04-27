/**
 * nanovoxApi.js — NanoVox Backend API Client
 *
 * Single source of truth for all HTTP calls to the FastAPI backend.
 * App.jsx and component hooks import from here instead of using fetch() directly.
 *


// ── Analysis ───────────────────────────────────────────────────────────────

/**
 * POST /analyze
 * Transcribe an audio file with Whisper and run the full scoring pipeline.
 *
 * @param {File}   file    - Audio file object (.wav, .mp3, .m4a, .ogg)
 * @param {object} weights - { talk_ratio, sentiment, empathy, resolution }
 * @returns {Promise<object>} Full analysis result
 */

import { API_BASE_URL, ANALYSIS_CONFIG } from '../config'
const BASE_URL = API_BASE_URL

export const analyzeAudio = async (file, weights) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('weights', JSON.stringify(weights))

    const response = await fetch(`${BASE_URL}/analyze`, {
        method: 'POST',
        body: formData,
    })
    if (!response.ok) throw new Error('Analysis failed. Please try again.')
    return response.json()
}

/**
 * POST /api/test-analysis
 * Run the scoring pipeline on a manually supplied JSON transcript (bypasses Whisper).
 *
 * @param {Array}  transcript - Array of { speaker, start, end, text } segments
 * @param {object} weights    - Custom weight map
 * @param {string} profile    - 'complaints' | 'sales' (default: 'complaints')
 * @returns {Promise<object>} Scoring result
 */
export const testAnalysis = async (transcript, weights, profile = 'complaints') => {
    const response = await fetch(`${BASE_URL}/api/test-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript, weights, profile }),
    })
    if (!response.ok) throw new Error('Test analysis request failed.')
    const data = await response.json()
    if (data.error) throw new Error(data.message || data.error)
    return data
}

/**
 * POST /api/rescore
 * Recalculate the final score using cached analyzer results and new weights.
 * Avoids re-running Whisper or the analyzers.
 *
 * @param {Array}  analyzerResults - Cached analyzer results from a previous analysis
 * @param {object} weights         - New weight map
 * @returns {Promise<object>} Updated CallScore
 */
export const rescore = async (analyzerResults, weights) => {
    const response = await fetch(`${BASE_URL}/api/rescore`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analyzer_results: analyzerResults, weights }),
    })
    if (!response.ok) throw new Error('Rescore request failed.')
    const data = await response.json()
    if (data.error) throw new Error(data.error)
    return data
}

// ── History ────────────────────────────────────────────────────────────────

/**
 * GET /api/history
 * Fetch the most recent analyzed calls, newest first.
 *
 * @param {number} limit - Max number of rows to return (default: 20)
 * @returns {Promise<Array>} Array of call summary objects
    */
export const getHistory = async (limit = ANALYSIS_CONFIG.HISTORY_LIMIT) => {
    const response = await fetch(`${BASE_URL}/api/history?limit=${limit}`)
    if (!response.ok) throw new Error('Failed to fetch history.')
    return response.json()
}

/**
 * GET /api/stats
 * Fetch aggregate stats across all analyzed calls (avg score, totals, etc.)
 *
 * @returns {Promise<object>} Stats object
 */
export const getStats = async () => {
    const response = await fetch(`${BASE_URL}/api/stats`)
    if (!response.ok) throw new Error('Failed to fetch stats.')
    return response.json()
}
