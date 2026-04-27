/**
 * config.js — NanoVox Application Configuration
 *
 * Centralized source of truth for all environment variables,
 * business logic constants, and UI configuration.
 */

// ── API Configuration ──────────────────────────────────────────────────────

// The base URL for the backend API.
// In development, this usually points to http://127.0.0.1:8000
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// ── Persistence ─────────────────────────────────────────────────────────────

export const STORAGE_KEYS = {
    THEME: 'nanovox_theme',
    WEIGHTS: 'nanovox_weights',
};

// ── Analysis Logic ─────────────────────────────────────────────────────────

export const DEFAULT_WEIGHTS = {
    talk_ratio: 5,
    sentiment: 35,
    empathy: 20,
    resolution: 40,
};

export const ANALYSIS_CONFIG = {
    // Debounce time for rescoring when weights change (ms)
    RESCORE_DEBOUNCE_MS: 300,
    // Max number of history items to fetch by default
    HISTORY_LIMIT: 20,
    // Max audio file size (50MB)
    MAX_AUDIO_SIZE_BYTES: 50 * 1024 * 1024,
};

// ── UI States ───────────────────────────────────────────────────────────────

export const PROCESSING_STEPS = [
    { label: 'Upload' },
    { label: 'Transcribe' },
    { label: 'Sentiment' },
    { label: 'Analyze' },
    { label: 'Score' },
    { label: 'Done' },
];

export const PROCESSING_STEP_STATUS = [
    '',
    'Uploading audio...',
    'Transcribing audio...',
    'Analyzing sentiment...',
    'Processing parameters...',
    'Calculating score...',
    'Complete',
];

// ── Aesthetics ─────────────────────────────────────────────────────────────

export const UI_COLORS = {
    SUCCESS: '#22c55e',
    WARNING: '#f59e0b',
    DANGER: '#ef4444',
};

export const SCORE_THRESHOLDS = {
    STRONG: 80,
    FAIR: 60,
    POOR: 50, // Threshold below which is DANGER
};
