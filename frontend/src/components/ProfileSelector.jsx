import { PARAM_INFO } from './utils'

/**
 * WeightSliders — internal slider grid for adjusting parameter weights.
 * Embedded inside ProfileSelector; not exported separately.
 */
function WeightSliders({ weights, onWeightChange, onReset, disabled }) {
    const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0)

    return (
        <div className="weight-sliders">
            <div className="weight-sliders-header">
                <div className="weight-title-row">
                    <h3>Weight Configuration</h3>
                    <button className="reset-btn-link" onClick={onReset} disabled={disabled} title="Restore default weights">
                        🔄 Reset
                    </button>
                </div>
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
                                onChange={e => onWeightChange(key, parseInt(e.target.value))}
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

/**
 * ProfileSelector — Weight configuration panel (right column of the landing view).
 *
 * Wraps WeightSliders in the glass card panel used on the landing page.
 *
 * Props:
 *   weights        — current { talk_ratio, sentiment, empathy, resolution } weight map
 *   onWeightChange — fn(key, value) — handleWeightChange from App.jsx
 *   disabled       — disable sliders (e.g. while processing)
 */
export default function ProfileSelector({ weights, onWeightChange, onReset, disabled }) {
    return (
        <div className="weight-config-panel glass-card">
            <WeightSliders
                weights={weights}
                onWeightChange={onWeightChange}
                onReset={onReset}
                disabled={disabled}
            />
        </div>
    )
}
