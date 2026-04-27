import { UploadIcon, FileIcon } from './ui/icons'
import { formatSize } from './utils'

/**
 * FileUpload — Upload card (left column of the landing view).
 *
 * Handles:
 *   • Dev Test Mode toggle + JSON textarea
 *   • Audio file dropzone + file preview
 *   • Complaints profile badge
 *   • "Analyze" / "Run Test Analysis" button
 *
 * Props:
 *   file                    — currently selected File object (or null)
 *   onFileChange            — handler for the hidden <input type="file"> onChange
 *   onProcess               — fires processCall() in App.jsx
 *   error                   — error string to display (or null)
 *   isTestMode              — boolean, whether Dev Test Mode is active
 *   onTestModeToggle        — toggles isTestMode and clears error in App.jsx
 *   manualTranscriptJson    — current value of the JSON textarea
 *   onManualTranscriptChange — setter for the textarea value
 */
export default function FileUpload({
    file,
    onFileChange,
    onProcess,
    error,
    isTestMode,
    onTestModeToggle,
    manualTranscriptJson,
    onManualTranscriptChange,
}) {
    const readyToProcess = isTestMode
        ? manualTranscriptJson.trim().length > 0
        : file !== null

    return (
        <div className="upload-card glass-card">

            {/* ── Dev Test Mode toggle ── */}
            <div className="test-mode-toggle">
                <span className="test-mode-label">🧪 Dev Test Mode</span>
                <button
                    id="test-mode-btn"
                    className={`toggle-switch ${isTestMode ? 'active' : ''}`}
                    onClick={onTestModeToggle}
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
                        onChange={e => onManualTranscriptChange(e.target.value)}
                        placeholder={`Paste your JSON transcript array here...\n\nExample:\n[\n  { "speaker": "Agent", "start": 0.0, "end": 4.0, "text": "How can I help?" },\n  { "speaker": "Customer", "start": 4.2, "end": 9.0, "text": "My order is broken!" }\n]`}
                        aria-label="JSON transcript input"
                        rows={10}
                        spellCheck={false}
                    />
                    <p className="json-hint">Array of <code>{'{speaker, start, end, text}'}</code> objects</p>
                </div>
            ) : (
                /* ── Normal Mode: dropzone + file preview ── */
                <>
                    <div
                        className="upload-area"
                        role="button"
                        tabIndex={0}
                        onClick={() => document.getElementById('file-upload').click()}
                        onKeyDown={e => e.key === 'Enter' && document.getElementById('file-upload').click()}
                    >
                        <UploadIcon aria-hidden="true" />
                        <h3>Upload Audio</h3>
                        <p className="upload-hint">Drop your file or click to browse</p>
                        <p className="supported-formats">WAV, MP3, M4A, OGG</p>
                        <input
                            type="file"
                            id="file-upload"
                            className="hidden-input"
                            accept=".wav,.mp3,.m4a,.ogg"
                            onChange={onFileChange}
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

            {/* ── Complaints Profile badge ── */}
            <div className="landing-profile-badge">
                <span className="profile-badge-icon">🎧</span>
                <span>Complaints Profile</span>
            </div>

            {/* ── Submit button — shown only when ready ── */}
            {readyToProcess && (
                <button
                    id="process-call-btn"
                    className="process-btn"
                    onClick={onProcess}
                    aria-label="Start call analysis"
                >
                    {isTestMode ? '🧪 Run Test Analysis' : 'Analyze'}
                </button>
            )}

            {/* ── Error toast ── */}
            {error && <div className="error-toast" role="alert">{error}</div>}
        </div>
    )
}
